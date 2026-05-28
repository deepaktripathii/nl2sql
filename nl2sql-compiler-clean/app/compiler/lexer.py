"""
lexer.py
────────
Lexical analyser for SQL queries.

Transforms a raw SQL string into a flat list of Token objects.
Handles:
  - SQL keywords (SELECT, FROM, WHERE …)
  - Identifiers and quoted identifiers (backtick, double-quote)
  - Single-quoted and double-quoted string literals
  - Integer and decimal number literals
  - All standard SQL operators and punctuation
  - Single-line (--) and block (/* */) comments (skipped)
  - Whitespace (skipped)
  - Unknown characters flagged as TokenType.UNKNOWN
"""

from typing import List
from app.compiler.tokens import Token
from app.constants import TokenType, KEYWORD_MAP, SQL_FUNCTIONS


class LexerError(Exception):
    """Raised when the lexer encounters an unrecoverable situation."""


class Lexer:
    """
    Hand-written, character-level SQL lexer.

    Usage
    -----
    tokens = Lexer("SELECT id FROM users WHERE age > 18").tokenize()
    """

    def __init__(self, source: str) -> None:
        self._src: str = source
        self._pos: int = 0
        self._line: int = 1
        self._col: int = 1
        self._tokens: List[Token] = []

    # ── public API ─────────────────────────────────────────────────────────

    def tokenize(self) -> List[Token]:
        """Return the complete token stream (including EOF)."""
        self._tokens = []
        while not self._at_end():
            self._scan_next()
        self._emit(TokenType.EOF, "")
        return self._tokens

    # ── core loop ──────────────────────────────────────────────────────────

    def _scan_next(self) -> None:
        ch = self._peek()

        # whitespace
        if ch in " \t\r\n":
            self._advance()
            return

        # single-line comment (--)
        if ch == "-" and self._peek(1) == "-":
            while not self._at_end() and self._peek() != "\n":
                self._advance()
            return

        # block comment /* ... */
        if ch == "/" and self._peek(1) == "*":
            self._advance()
            self._advance()
            while not self._at_end():
                if self._peek() == "*" and self._peek(1) == "/":
                    self._advance()
                    self._advance()
                    break
                if self._peek() == "\n":
                    self._line += 1
                    self._col = 1
                self._advance()
            return

        # string literals (single-quoted)
        if ch == "'":
            self._read_string("'")
            return

        # double-quoted identifier / string
        if ch == '"':
            self._read_string('"', as_identifier=True)
            return

        # backtick-quoted identifier (MySQL)
        if ch == "`":
            self._read_string("`", as_identifier=True)
            return

        # numbers
        if ch.isdigit() or (ch == "." and self._peek(1).isdigit()):
            self._read_number()
            return

        # identifiers / keywords
        if ch.isalpha() or ch == "_":
            self._read_word()
            return

        # two-char operators
        two = self._peek() + (self._peek(1) or "")
        if two == "!=":
            self._emit_and_advance(TokenType.NEQ, "!=", n=2)
            return
        if two == "<>":
            self._emit_and_advance(TokenType.NEQ, "<>", n=2)
            return
        if two == "<=":
            self._emit_and_advance(TokenType.LTE, "<=", n=2)
            return
        if two == ">=":
            self._emit_and_advance(TokenType.GTE, ">=", n=2)
            return

        # single-char operators / punctuation
        single_map = {
            "=": TokenType.EQ,
            "<": TokenType.LT,
            ">": TokenType.GT,
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.DIVIDE,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            ";": TokenType.SEMICOLON,
        }
        if ch in single_map:
            self._emit_and_advance(single_map[ch], ch)
            return

        # unknown
        self._emit_and_advance(TokenType.UNKNOWN, ch)

    # ── readers ────────────────────────────────────────────────────────────

    def _read_string(self, quote: str, as_identifier: bool = False) -> None:
        start_col = self._col
        self._advance()  # opening quote
        buf = []
        while not self._at_end():
            ch = self._peek()
            if ch == quote:
                self._advance()
                break
            if ch == "\\" and not as_identifier:
                self._advance()
                esc = self._advance()
                buf.append({"n": "\n", "t": "\t", "r": "\r"}.get(esc, esc))
            else:
                if ch == "\n":
                    self._line += 1
                    self._col = 1
                buf.append(self._advance())
        value = "".join(buf)
        tok_type = TokenType.IDENTIFIER if as_identifier else TokenType.STRING
        self._tokens.append(Token(tok_type, value, self._line, start_col))

    def _read_number(self) -> None:
        start_col = self._col
        buf = []
        has_dot = False
        while not self._at_end() and (self._peek().isdigit() or (self._peek() == "." and not has_dot)):
            if self._peek() == ".":
                has_dot = True
            buf.append(self._advance())
        # optional exponent e.g. 1e5
        if not self._at_end() and self._peek() in "eE":
            buf.append(self._advance())
            if not self._at_end() and self._peek() in "+-":
                buf.append(self._advance())
            while not self._at_end() and self._peek().isdigit():
                buf.append(self._advance())
        self._tokens.append(Token(TokenType.NUMBER, "".join(buf), self._line, start_col))

    def _read_word(self) -> None:
        start_col = self._col
        buf = []
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            buf.append(self._advance())
        word = "".join(buf)
        lower = word.lower()

        # Handle "ORDER BY" / "GROUP BY" as single logical tokens
        if lower in ("order", "group"):
            saved_pos = self._pos
            saved_col = self._col
            # skip whitespace
            while not self._at_end() and self._peek() in " \t\r\n":
                self._advance()
            by_buf = []
            while not self._at_end() and self._peek().isalpha():
                by_buf.append(self._advance())
            if "".join(by_buf).lower() == "by":
                tok_type = TokenType.ORDER_BY if lower == "order" else TokenType.GROUP_BY
                self._tokens.append(Token(tok_type, word + " BY", self._line, start_col))
                return
            else:
                # rollback
                self._pos = saved_pos
                self._col = saved_col

        # Function names
        if lower in SQL_FUNCTIONS:
            self._tokens.append(Token(TokenType.FUNCTION, word, self._line, start_col))
            return

        tok_type = KEYWORD_MAP.get(lower, TokenType.IDENTIFIER)
        self._tokens.append(Token(tok_type, word, self._line, start_col))

    # ── helpers ────────────────────────────────────────────────────────────

    def _peek(self, offset: int = 0) -> str:
        idx = self._pos + offset
        return self._src[idx] if idx < len(self._src) else ""

    def _advance(self) -> str:
        ch = self._src[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 1
        else:
            self._col += 1
        return ch

    def _at_end(self) -> bool:
        return self._pos >= len(self._src)

    def _emit(self, tok_type: TokenType, value: str) -> None:
        self._tokens.append(Token(tok_type, value, self._line, self._col))

    def _emit_and_advance(self, tok_type: TokenType, value: str, n: int = 1) -> None:
        col = self._col
        for _ in range(n):
            self._advance()
        self._tokens.append(Token(tok_type, value, self._line, col))
