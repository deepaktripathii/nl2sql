"""
constants.py
────────────
All hard-coded constants: token names, SQL keywords, grammar
rules, blocked commands, and regex patterns.
"""

from enum import Enum, auto

# ─── Token Type Enumeration ───────────────────────────────────────────────────

class TokenType(Enum):
    # Query keywords
    SELECT      = auto()
    FROM        = auto()
    WHERE       = auto()
    AND         = auto()
    OR          = auto()
    NOT         = auto()
    ORDER_BY    = auto()
    GROUP_BY    = auto()
    HAVING      = auto()
    LIMIT       = auto()
    OFFSET      = auto()
    JOIN        = auto()
    LEFT        = auto()
    RIGHT       = auto()
    INNER       = auto()
    OUTER       = auto()
    ON          = auto()
    AS          = auto()
    DISTINCT    = auto()
    ALL         = auto()
    IN          = auto()
    BETWEEN     = auto()
    LIKE        = auto()
    IS          = auto()
    NULL        = auto()
    EXISTS      = auto()
    UNION       = auto()
    INTERSECT   = auto()
    EXCEPT      = auto()
    CASE        = auto()
    WHEN        = auto()
    THEN        = auto()
    ELSE        = auto()
    END         = auto()

    # Aggregate / scalar functions
    FUNCTION    = auto()

    # Data types / literals
    NUMBER      = auto()
    STRING      = auto()
    BOOLEAN     = auto()
    IDENTIFIER  = auto()

    # Operators
    COMMA       = auto()
    DOT         = auto()
    STAR        = auto()
    LPAREN      = auto()
    RPAREN      = auto()
    SEMICOLON   = auto()

    # Comparison operators
    EQ          = auto()   # =
    NEQ         = auto()   # != or <>
    LT          = auto()   # <
    GT          = auto()   # >
    LTE         = auto()   # <=
    GTE         = auto()   # >=

    # Arithmetic
    PLUS        = auto()
    MINUS       = auto()
    DIVIDE      = auto()

    # Dangerous / blocked DML/DDL keywords
    INSERT      = auto()
    UPDATE      = auto()
    DELETE      = auto()
    DROP        = auto()
    CREATE      = auto()
    ALTER       = auto()
    TRUNCATE    = auto()
    EXEC        = auto()
    EXECUTE     = auto()
    GRANT       = auto()
    REVOKE      = auto()

    # Control
    EOF         = auto()
    UNKNOWN     = auto()


# ─── Keyword → TokenType Map ─────────────────────────────────────────────────

KEYWORD_MAP: dict[str, TokenType] = {
    "select":    TokenType.SELECT,
    "from":      TokenType.FROM,
    "where":     TokenType.WHERE,
    "and":       TokenType.AND,
    "or":        TokenType.OR,
    "not":       TokenType.NOT,
    "order":     TokenType.ORDER_BY,
    "group":     TokenType.GROUP_BY,
    "having":    TokenType.HAVING,
    "limit":     TokenType.LIMIT,
    "offset":    TokenType.OFFSET,
    "join":      TokenType.JOIN,
    "left":      TokenType.LEFT,
    "right":     TokenType.RIGHT,
    "inner":     TokenType.INNER,
    "outer":     TokenType.OUTER,
    "on":        TokenType.ON,
    "as":        TokenType.AS,
    "distinct":  TokenType.DISTINCT,
    "all":       TokenType.ALL,
    "in":        TokenType.IN,
    "between":   TokenType.BETWEEN,
    "like":      TokenType.LIKE,
    "is":        TokenType.IS,
    "null":      TokenType.NULL,
    "exists":    TokenType.EXISTS,
    "union":     TokenType.UNION,
    "intersect": TokenType.INTERSECT,
    "except":    TokenType.EXCEPT,
    "case":      TokenType.CASE,
    "when":      TokenType.WHEN,
    "then":      TokenType.THEN,
    "else":      TokenType.ELSE,
    "end":       TokenType.END,
    "true":      TokenType.BOOLEAN,
    "false":     TokenType.BOOLEAN,
    # Blocked
    "insert":    TokenType.INSERT,
    "update":    TokenType.UPDATE,
    "delete":    TokenType.DELETE,
    "drop":      TokenType.DROP,
    "create":    TokenType.CREATE,
    "alter":     TokenType.ALTER,
    "truncate":  TokenType.TRUNCATE,
    "exec":      TokenType.EXEC,
    "execute":   TokenType.EXECUTE,
    "grant":     TokenType.GRANT,
    "revoke":    TokenType.REVOKE,
}

# ─── Aggregate / Scalar SQL Functions ────────────────────────────────────────

SQL_FUNCTIONS = {
    "count", "sum", "avg", "min", "max",
    "upper", "lower", "length", "substr", "substring",
    "trim", "ltrim", "rtrim", "replace", "concat",
    "coalesce", "ifnull", "nullif", "isnull",
    "now", "curdate", "curtime", "date", "year",
    "month", "day", "datediff", "date_format",
    "round", "floor", "ceil", "abs", "mod", "power",
    "cast", "convert",
    "row_number", "rank", "dense_rank", "ntile",
    "lead", "lag", "first_value", "last_value",
}

# ─── Dangerous Token Types (BLOCK these immediately) ─────────────────────────

DANGEROUS_TOKEN_TYPES = {
    TokenType.INSERT,
    TokenType.UPDATE,
    TokenType.DELETE,
    TokenType.DROP,
    TokenType.CREATE,
    TokenType.ALTER,
    TokenType.TRUNCATE,
    TokenType.EXEC,
    TokenType.EXECUTE,
    TokenType.GRANT,
    TokenType.REVOKE,
}

DANGEROUS_KEYWORDS = {
    "insert", "update", "delete", "drop", "create",
    "alter", "truncate", "exec", "execute", "grant", "revoke",
}

# ─── Grammar Rules (BNF-style descriptions for display) ──────────────────────

GRAMMAR_RULES = {
    "SELECT_STMT":    "SELECT_STMT → SELECT [DISTINCT] col_list FROM table_ref [joins] [WHERE cond] [GROUP BY cols] [HAVING cond] [ORDER BY cols] [LIMIT n]",
    "COL_LIST":       "col_list    → * | col_expr (, col_expr)*",
    "COL_EXPR":       "col_expr    → (table.)? col [AS alias] | func_call [AS alias]",
    "TABLE_REF":      "table_ref   → table_name [AS alias]",
    "JOIN_CLAUSE":    "join_clause → [LEFT|RIGHT|INNER|OUTER]? JOIN table_ref ON cond",
    "WHERE_CLAUSE":   "WHERE_CLAUSE→ WHERE condition",
    "CONDITION":      "condition   → expr (AND|OR condition)* | NOT condition",
    "EXPR":           "expr        → col_ref op literal | col_ref IN (list) | col_ref BETWEEN a AND b | col_ref LIKE pattern",
    "GROUP_CLAUSE":   "GROUP_CLAUSE→ GROUP BY col_ref (, col_ref)*",
    "ORDER_CLAUSE":   "ORDER_CLAUSE→ ORDER BY col_ref [ASC|DESC] (, col_ref [ASC|DESC])*",
    "LIMIT_CLAUSE":   "LIMIT_CLAUSE→ LIMIT integer [OFFSET integer]",
    "FUNC_CALL":      "func_call   → FUNC_NAME ( [DISTINCT]? col_ref | * )",
}

# ─── Operator Precedence ──────────────────────────────────────────────────────

OPERATOR_PRECEDENCE = {
    "OR":      1,
    "AND":     2,
    "NOT":     3,
    "=":       4,
    "!=":      4,
    "<>":      4,
    "<":       4,
    ">":       4,
    "<=":      4,
    ">=":      4,
    "LIKE":    4,
    "IN":      4,
    "BETWEEN": 4,
    "IS":      4,
    "+":       5,
    "-":       5,
    "*":       6,
    "/":       6,
}

# ─── UI / Display ─────────────────────────────────────────────────────────────

TOKEN_COLORS = {
    "SELECT":     "#4FC3F7",
    "FROM":       "#4FC3F7",
    "WHERE":      "#4FC3F7",
    "JOIN":       "#4FC3F7",
    "FUNCTION":   "#FFD54F",
    "IDENTIFIER": "#A5D6A7",
    "NUMBER":     "#EF9A9A",
    "STRING":     "#CE93D8",
    "OPERATOR":   "#FFCC80",
    "KEYWORD":    "#80DEEA",
    "DANGEROUS":  "#FF5252",
    "UNKNOWN":    "#BDBDBD",
}
