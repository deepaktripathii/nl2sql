"""
grammar.py
──────────
AST node types for the SQL parser.
Each class corresponds to a grammar production rule.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class ASTNode:
    node_type: str

    def to_dict(self) -> dict:
        result = {"node_type": self.node_type}
        for k, v in self.__dict__.items():
            if k == "node_type":
                continue
            if isinstance(v, ASTNode):
                result[k] = v.to_dict()
            elif isinstance(v, list):
                result[k] = [
                    item.to_dict() if isinstance(item, ASTNode) else item
                    for item in v
                ]
            else:
                result[k] = v
        return result


@dataclass
class IdentifierNode(ASTNode):
    name: str
    table: Optional[str] = None
    alias: Optional[str] = None

    def __init__(self, name: str, table: Optional[str] = None, alias: Optional[str] = None):
        super().__init__("Identifier")
        self.name = name
        self.table = table
        self.alias = alias

    def __str__(self) -> str:
        base = f"{self.table}.{self.name}" if self.table else self.name
        return f"{base} AS {self.alias}" if self.alias else base


@dataclass
class LiteralNode(ASTNode):
    value: Any
    kind: str

    def __init__(self, value: Any, kind: str):
        super().__init__("Literal")
        self.value = value
        self.kind = kind

    def __str__(self) -> str:
        return f"'{self.value}'" if self.kind == "string" else str(self.value)


@dataclass
class WildcardNode(ASTNode):
    table: Optional[str] = None

    def __init__(self, table: Optional[str] = None):
        super().__init__("Wildcard")
        self.table = table

    def __str__(self) -> str:
        return f"{self.table}.*" if self.table else "*"


@dataclass
class FunctionCallNode(ASTNode):
    name: str
    args: List[ASTNode]
    distinct: bool = False
    alias: Optional[str] = None

    def __init__(self, name: str, args: List[ASTNode], distinct: bool = False, alias: Optional[str] = None):
        super().__init__("FunctionCall")
        self.name = name
        self.args = args
        self.distinct = distinct
        self.alias = alias

    def __str__(self) -> str:
        d = "DISTINCT " if self.distinct else ""
        args_str = ", ".join(str(a) for a in self.args)
        alias_str = f" AS {self.alias}" if self.alias else ""
        return f"{self.name.upper()}({d}{args_str}){alias_str}"


@dataclass
class BinaryOpNode(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode

    def __init__(self, left: ASTNode, operator: str, right: ASTNode):
        super().__init__("BinaryOp")
        self.left = left
        self.operator = operator
        self.right = right

    def __str__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"


@dataclass
class UnaryOpNode(ASTNode):
    operator: str
    operand: ASTNode

    def __init__(self, operator: str, operand: ASTNode):
        super().__init__("UnaryOp")
        self.operator = operator
        self.operand = operand

    def __str__(self) -> str:
        return f"({self.operator} {self.operand})"


@dataclass
class BetweenNode(ASTNode):
    expr: ASTNode
    low: ASTNode
    high: ASTNode
    negated: bool = False

    def __init__(self, expr: ASTNode, low: ASTNode, high: ASTNode, negated: bool = False):
        super().__init__("Between")
        self.expr = expr
        self.low = low
        self.high = high
        self.negated = negated

    def __str__(self) -> str:
        n = "NOT " if self.negated else ""
        return f"{self.expr} {n}BETWEEN {self.low} AND {self.high}"


@dataclass
class InListNode(ASTNode):
    expr: ASTNode
    values: List[ASTNode]
    negated: bool = False

    def __init__(self, expr: ASTNode, values: List[ASTNode], negated: bool = False):
        super().__init__("InList")
        self.expr = expr
        self.values = values
        self.negated = negated

    def __str__(self) -> str:
        n = "NOT " if self.negated else ""
        vals = ", ".join(str(v) for v in self.values)
        return f"{self.expr} {n}IN ({vals})"


@dataclass
class IsNullNode(ASTNode):
    expr: ASTNode
    negated: bool = False

    def __init__(self, expr: ASTNode, negated: bool = False):
        super().__init__("IsNull")
        self.expr = expr
        self.negated = negated

    def __str__(self) -> str:
        n = "NOT " if self.negated else ""
        return f"{self.expr} IS {n}NULL"


@dataclass
class TableRefNode(ASTNode):
    name: str
    alias: Optional[str] = None

    def __init__(self, name: str, alias: Optional[str] = None):
        super().__init__("TableRef")
        self.name = name
        self.alias = alias

    def __str__(self) -> str:
        return f"{self.name}" + (f" AS {self.alias}" if self.alias else "")


@dataclass
class JoinNode(ASTNode):
    join_type: str
    table: TableRefNode
    condition: Optional[ASTNode] = None

    def __init__(self, join_type: str, table: TableRefNode, condition: Optional[ASTNode] = None):
        super().__init__("Join")
        self.join_type = join_type
        self.table = table
        self.condition = condition


@dataclass
class OrderItemNode(ASTNode):
    expr: ASTNode
    direction: str = "ASC"

    def __init__(self, expr: ASTNode, direction: str = "ASC"):
        super().__init__("OrderItem")
        self.expr = expr
        self.direction = direction

    def __str__(self) -> str:
        return f"{self.expr} {self.direction}"


@dataclass
class SelectStatement(ASTNode):
    distinct: bool
    columns: List[ASTNode]
    from_table: Optional[TableRefNode]
    joins: List[JoinNode]
    where: Optional[ASTNode]
    group_by: List[ASTNode]
    having: Optional[ASTNode]
    order_by: List[OrderItemNode]
    limit: Optional[int]
    offset: Optional[int]

    def __init__(
        self,
        distinct: bool = False,
        columns: Optional[List[ASTNode]] = None,
        from_table: Optional[TableRefNode] = None,
        joins: Optional[List[JoinNode]] = None,
        where: Optional[ASTNode] = None,
        group_by: Optional[List[ASTNode]] = None,
        having: Optional[ASTNode] = None,
        order_by: Optional[List[OrderItemNode]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ):
        super().__init__("SelectStatement")
        self.distinct = distinct
        self.columns = columns or []
        self.from_table = from_table
        self.joins = joins or []
        self.where = where
        self.group_by = group_by or []
        self.having = having
        self.order_by = order_by or []
        self.limit = limit
        self.offset = offset
