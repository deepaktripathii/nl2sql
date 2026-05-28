"""
parser.py
─────────
Recursive-descent SQL parser.

Consumes the token stream from the Lexer and builds an AST
(SelectStatement and child nodes from grammar.py).

Supported grammar:
  SELECT [DISTINCT] col_list
  FROM table_ref
  [JOIN ...]
  [WHERE condition]
  [GROUP BY col_list]
  [HAVING condition]
  [ORDER BY order_list]
  [LIMIT n [OFFSET m]]
"""

from typing import List, Optional
from app.compiler.tokens import Token
from app.constants import TokenType
from app.compiler.grammar import (
    ASTNode, SelectStatement, IdentifierNode, LiteralNode,
    WildcardNode, FunctionCallNode, BinaryOpNode, UnaryOpNode,
    BetweenNode, InListNode, IsNullNode, TableRefNode,
    JoinNode, OrderItemNode,
)


class ParseError(Exception):
    """Raised for syntax errors detected during parsing."""


class Parser:
    """
    Recursive-descent parser for SQL SELECT statements.

    Usage
    -----
    from app.compiler.lexer import Lexer
    tokens = Lexer(sql).tokenize()
    ast    = Parser(tokens).parse()
    """

    COMPARISON_OPS = {
        TokenType.EQ, TokenType.NEQ, TokenType.LT,
        TokenType.GT, TokenType.LTE, TokenType.GTE,
    }

    def __init__(self, tokens: List[Token]) -> None:
        # Strip EOF so we can check cleanly
        self._tokens = [t for t in tokens if t.type != TokenType.EOF]
        self._eof = tokens[-1] if tokens else Token(TokenType.EOF, "", 1, 0)
        self._pos = 0

    # ── public API ─────────────────────────────────────────────────────────

    def parse(self) -> SelectStatement:
        stmt = self._parse_select()
        # consume optional trailing semicolon
        if self._check(TokenType.SEMICOLON):
            self._advance()
        return stmt

    # ── SELECT statement ───────────────────────────────────────────────────

    def _parse_select(self) -> SelectStatement:
        self._expect(TokenType.SELECT)

        distinct = False
        if self._check(TokenType.DISTINCT):
            self._advance()
            distinct = True

        columns = self._parse_column_list()

        from_table = None
        if self._check(TokenType.FROM):
            self._advance()
            from_table = self._parse_table_ref()

        joins = self._parse_joins()

        where = None
        if self._check(TokenType.WHERE):
            self._advance()
            where = self._parse_condition()

        group_by: List[ASTNode] = []
        if self._check(TokenType.GROUP_BY):
            self._advance()
            group_by = self._parse_col_ref_list()

        having = None
        if self._check(TokenType.HAVING):
            self._advance()
            having = self._parse_condition()

        order_by: List[OrderItemNode] = []
        if self._check(TokenType.ORDER_BY):
            self._advance()
            order_by = self._parse_order_list()

        limit = offset = None
        if self._check(TokenType.LIMIT):
            self._advance()
            limit = int(self._expect(TokenType.NUMBER).value)
        if self._check(TokenType.OFFSET):
            self._advance()
            offset = int(self._expect(TokenType.NUMBER).value)

        return SelectStatement(
            distinct=distinct,
            columns=columns,
            from_table=from_table,
            joins=joins,
            where=where,
            group_by=group_by,
            having=having,
            order_by=order_by,
            limit=limit,
            offset=offset,
        )

    # ── column list ────────────────────────────────────────────────────────

    def _parse_column_list(self) -> List[ASTNode]:
        cols: List[ASTNode] = []
        cols.append(self._parse_col_expr())
        while self._check(TokenType.COMMA):
            self._advance()
            cols.append(self._parse_col_expr())
        return cols

    def _parse_col_expr(self) -> ASTNode:
        # wildcard *
        if self._check(TokenType.STAR):
            self._advance()
            return WildcardNode()

        # function call
        if self._check(TokenType.FUNCTION):
            return self._parse_function_call(with_alias=True)

        # identifier or table.col
        if self._check(TokenType.IDENTIFIER):
            name = self._advance().value
            # table.col or table.*
            if self._check(TokenType.DOT):
                self._advance()
                if self._check(TokenType.STAR):
                    self._advance()
                    return WildcardNode(table=name)
                col = self._expect(TokenType.IDENTIFIER).value
                alias = self._try_alias()
                return IdentifierNode(name=col, table=name, alias=alias)
            alias = self._try_alias()
            return IdentifierNode(name=name, alias=alias)

        raise ParseError(
            f"Expected column expression, got {self._peek().value!r} at L{self._peek().line}:C{self._peek().column}"
        )

    def _parse_col_ref_list(self) -> List[ASTNode]:
        items: List[ASTNode] = [self._parse_col_ref()]
        while self._check(TokenType.COMMA):
            self._advance()
            items.append(self._parse_col_ref())
        return items

    def _parse_col_ref(self) -> ASTNode:
        """Parse table.col or col (no alias, no function)."""
        if self._check(TokenType.FUNCTION):
            return self._parse_function_call(with_alias=False)
        name = self._expect(TokenType.IDENTIFIER).value
        if self._check(TokenType.DOT):
            self._advance()
            col = self._expect(TokenType.IDENTIFIER).value
            return IdentifierNode(name=col, table=name)
        return IdentifierNode(name=name)

    # ── FROM / table ref ───────────────────────────────────────────────────

    def _parse_table_ref(self) -> TableRefNode:
        name = self._expect(TokenType.IDENTIFIER).value
        alias = self._try_alias()
        return TableRefNode(name=name, alias=alias)

    # ── JOINs ──────────────────────────────────────────────────────────────

    def _parse_joins(self) -> List[JoinNode]:
        joins: List[JoinNode] = []
        while self._peek_is_join():
            joins.append(self._parse_join())
        return joins

    def _peek_is_join(self) -> bool:
        return self._check(TokenType.JOIN) or self._check(TokenType.LEFT) \
            or self._check(TokenType.RIGHT) or self._check(TokenType.INNER) \
            or self._check(TokenType.OUTER)

    def _parse_join(self) -> JoinNode:
        join_type = "INNER"
        if self._check(TokenType.LEFT):
            join_type = "LEFT"
            self._advance()
        elif self._check(TokenType.RIGHT):
            join_type = "RIGHT"
            self._advance()
        elif self._check(TokenType.INNER):
            join_type = "INNER"
            self._advance()
        elif self._check(TokenType.OUTER):
            join_type = "OUTER"
            self._advance()

        if self._check(TokenType.OUTER) and join_type in ("LEFT", "RIGHT"):
            self._advance()  # consume redundant OUTER

        self._expect(TokenType.JOIN)
        table = self._parse_table_ref()

        condition = None
        if self._check(TokenType.ON):
            self._advance()
            condition = self._parse_condition()

        return JoinNode(join_type=join_type, table=table, condition=condition)

    # ── condition parsing ──────────────────────────────────────────────────

    def _parse_condition(self) -> ASTNode:
        left = self._parse_and_expr()
        while self._check(TokenType.OR):
            self._advance()
            right = self._parse_and_expr()
            left = BinaryOpNode(left=left, operator="OR", right=right)
        return left

    def _parse_and_expr(self) -> ASTNode:
        left = self._parse_not_expr()
        while self._check(TokenType.AND):
            self._advance()
            right = self._parse_not_expr()
            left = BinaryOpNode(left=left, operator="AND", right=right)
        return left

    def _parse_not_expr(self) -> ASTNode:
        if self._check(TokenType.NOT):
            self._advance()
            operand = self._parse_comparison()
            return UnaryOpNode(operator="NOT", operand=operand)
        return self._parse_comparison()

    def _parse_comparison(self) -> ASTNode:
        # parenthesised sub-condition
        if self._check(TokenType.LPAREN):
            self._advance()
            node = self._parse_condition()
            self._expect(TokenType.RPAREN)
            return node

        left = self._parse_atom()

        # IS [NOT] NULL
        if self._check(TokenType.IS):
            self._advance()
            negated = False
            if self._check(TokenType.NOT):
                negated = True
                self._advance()
            self._expect(TokenType.NULL)
            return IsNullNode(expr=left, negated=negated)

        # [NOT] IN (...)
        negated = False
        if self._check(TokenType.NOT):
            self._advance()
            negated = True

        if self._check(TokenType.IN):
            self._advance()
            self._expect(TokenType.LPAREN)
            values: List[ASTNode] = [self._parse_atom()]
            while self._check(TokenType.COMMA):
                self._advance()
                values.append(self._parse_atom())
            self._expect(TokenType.RPAREN)
            return InListNode(expr=left, values=values, negated=negated)

        # [NOT] BETWEEN a AND b
        if self._check(TokenType.BETWEEN):
            self._advance()
            low = self._parse_atom()
            self._expect(TokenType.AND)
            high = self._parse_atom()
            return BetweenNode(expr=left, low=low, high=high, negated=negated)

        # [NOT] LIKE
        if self._check(TokenType.LIKE):
            self._advance()
            pattern = self._parse_atom()
            op = "NOT LIKE" if negated else "LIKE"
            return BinaryOpNode(left=left, operator=op, right=pattern)

        if negated:
            # rollback mentally — re-attach the NOT as unary
            # (this handles NOT EXISTS etc.)
            return UnaryOpNode(operator="NOT", operand=left)

        # comparison operators
        if self._peek().type in self.COMPARISON_OPS:
            op_token = self._advance()
            right = self._parse_atom()
            return BinaryOpNode(left=left, operator=op_token.value, right=right)

        return left

    # ── atom (lowest-level expression) ────────────────────────────────────

    def _parse_atom(self) -> ASTNode:
        tok = self._peek()

        if tok.type == TokenType.NUMBER:
            self._advance()
            v = float(tok.value) if "." in tok.value else int(tok.value)
            return LiteralNode(value=v, kind="number")

        if tok.type == TokenType.STRING:
            self._advance()
            return LiteralNode(value=tok.value, kind="string")

        if tok.type == TokenType.BOOLEAN:
            self._advance()
            return LiteralNode(value=tok.value.lower() == "true", kind="boolean")

        if tok.type == TokenType.NULL:
            self._advance()
            return LiteralNode(value=None, kind="null")

        if tok.type == TokenType.FUNCTION:
            return self._parse_function_call(with_alias=False)

        if tok.type == TokenType.IDENTIFIER:
            name = self._advance().value
            if self._check(TokenType.DOT):
                self._advance()
                col = self._expect(TokenType.IDENTIFIER).value
                return IdentifierNode(name=col, table=name)
            return IdentifierNode(name=name)

        if tok.type == TokenType.LPAREN:
            self._advance()
            node = self._parse_condition()
            self._expect(TokenType.RPAREN)
            return node

        if tok.type == TokenType.STAR:
            self._advance()
            return WildcardNode()

        raise ParseError(
            f"Unexpected token {tok.value!r} (type={tok.type.name}) at L{tok.line}:C{tok.column}"
        )

    # ── function call ──────────────────────────────────────────────────────

    def _parse_function_call(self, with_alias: bool) -> FunctionCallNode:
        name = self._expect(TokenType.FUNCTION).value
        self._expect(TokenType.LPAREN)

        distinct = False
        if self._check(TokenType.DISTINCT):
            self._advance()
            distinct = True

        args: List[ASTNode] = []
        if self._check(TokenType.STAR):
            self._advance()
            args.append(WildcardNode())
        elif not self._check(TokenType.RPAREN):
            args.append(self._parse_atom())
            while self._check(TokenType.COMMA):
                self._advance()
                args.append(self._parse_atom())

        self._expect(TokenType.RPAREN)
        alias = self._try_alias() if with_alias else None
        return FunctionCallNode(name=name, args=args, distinct=distinct, alias=alias)

    # ── ORDER BY ───────────────────────────────────────────────────────────

    def _parse_order_list(self) -> List[OrderItemNode]:
        items: List[OrderItemNode] = []
        items.append(self._parse_order_item())
        while self._check(TokenType.COMMA):
            self._advance()
            items.append(self._parse_order_item())
        return items

    def _parse_order_item(self) -> OrderItemNode:
        expr = self._parse_col_ref()
        direction = "ASC"
        if self._check(TokenType.IDENTIFIER) and self._peek().value.upper() in ("ASC", "DESC"):
            direction = self._advance().value.upper()
        return OrderItemNode(expr=expr, direction=direction)

    # ── alias helper ───────────────────────────────────────────────────────

    def _try_alias(self) -> Optional[str]:
        if self._check(TokenType.AS):
            self._advance()
            return self._expect(TokenType.IDENTIFIER).value
        # implicit alias (bare identifier after col, not a keyword)
        if self._check(TokenType.IDENTIFIER):
            return self._advance().value
        return None

    # ── token stream helpers ───────────────────────────────────────────────

    def _peek(self) -> Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return self._eof

    def _advance(self) -> Token:
        tok = self._peek()
        self._pos += 1
        return tok

    def _check(self, *types: TokenType) -> bool:
        return self._peek().type in types

    def _expect(self, *types: TokenType) -> Token:
        tok = self._peek()
        if tok.type not in types:
            expected = " or ".join(t.name for t in types)
            raise ParseError(
                f"Expected {expected}, got {tok.value!r} (type={tok.type.name}) "
                f"at L{tok.line}:C{tok.column}"
            )
        return self._advance()
