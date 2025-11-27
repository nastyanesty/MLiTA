from dataclasses import dataclass
from typing import List, Tuple, Union

@dataclass
class Pred:
    name: str
    args: Tuple[str, ...]


@dataclass
class Not:
    sub: "Formula"


@dataclass
class And:
    left: "Formula"
    right: "Formula"


@dataclass
class Or:
    left: "Formula"
    right: "Formula"


@dataclass
class Implies:
    left: "Formula"
    right: "Formula"


Formula = Union[Pred, Not, And, Or, Implies]

def tokenize(s: str):
    """
    Превращает строку в токены.
    Поддерживает: (), имена русские/английские, ¬, ∧, ∨, ->, →.
    """
    tokens = []
    i = 0

    import re
    name_re = re.compile(r"[A-Za-zА-Яа-яЁё_][A-Za-zА-Яа-яЁё_0-9]*")

    while i < len(s):
        ch = s[i]

        if ch.isspace():
            i += 1
            continue

        # ---- импликации ----
        if s.startswith("->", i):
            tokens.append(("IMPLIES", "->"))
            i += 2
            continue

        if s.startswith("→", i):   # Иногда ChatGPT пишет импликацию так
            tokens.append(("IMPLIES", "→"))
            i += 1
            continue

        # ---- односимвольные ----
        if ch == "(":
            tokens.append(("LPAREN", ch))
            i += 1
            continue
        if ch == ")":
            tokens.append(("RPAREN", ch))
            i += 1
            continue
        if ch == ",":
            tokens.append(("COMMA", ch))
            i += 1
            continue
        if ch in ["¬", "!"]:
            tokens.append(("NOT", ch))
            i += 1
            continue
        if ch in ["∧", "&"]:
            tokens.append(("AND", ch))
            i += 1
            continue
        if ch in ["∨", "|"]:
            tokens.append(("OR", ch))
            i += 1
            continue

        # ---- имена ----
        m = name_re.match(s, i)
        if m:
            tokens.append(("NAME", m.group(0)))
            i = m.end()
            continue

        raise ValueError(f"Неожиданный символ {ch!r} в позиции {i}")

    tokens.append(("END", ""))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def consume(self, ttype=None):
        tok = self.tokens[self.pos]
        if ttype and tok[0] != ttype:
            raise ValueError(f"Ожидался {ttype}, а получено {tok}")
        self.pos += 1
        return tok

    def parse(self) -> Formula:
        node = self.parse_implication()
        if self.peek()[0] != "END":
            raise ValueError("Лишние токены после формулы")
        return node

    # Импликация (низший приоритет)
    def parse_implication(self) -> Formula:
        left = self.parse_or()
        if self.peek()[0] == "IMPLIES":
            self.consume("IMPLIES")
            right = self.parse_implication()
            return Implies(left, right)
        return left

    # ∨
    def parse_or(self) -> Formula:
        node = self.parse_and()
        while self.peek()[0] == "OR":
            self.consume("OR")
            right = self.parse_and()
            node = Or(node, right)
        return node

    # ∧
    def parse_and(self) -> Formula:
        node = self.parse_unary()
        while self.peek()[0] == "AND":
            self.consume("AND")
            right = self.parse_unary()
            node = And(node, right)
        return node

    # ¬
    def parse_unary(self) -> Formula:
        if self.peek()[0] == "NOT":
            self.consume("NOT")
            sub = self.parse_unary()
            return Not(sub)
        return self.parse_atom()

    # скобки или предикат
    def parse_atom(self) -> Formula:
        tok = self.peek()

        # (expr)
        if tok[0] == "LPAREN":
            self.consume("LPAREN")
            node = self.parse_implication()
            self.consume("RPAREN")
            return node

        # Предикат (включая 0-арные)
        if tok[0] == "NAME":
            name = self.consume("NAME")[1]
            # аргументы?
            if self.peek()[0] == "LPAREN":
                self.consume("LPAREN")
                args = []
                if self.peek()[0] == "NAME":
                    args.append(self.consume("NAME")[1])
                    while self.peek()[0] == "COMMA":
                        self.consume("COMMA")
                        args.append(self.consume("NAME")[1])
                self.consume("RPAREN")
                return Pred(name, tuple(args))
            else:
                return Pred(name, tuple())

        raise ValueError(f"Неожиданный токен {tok} в атоме")


def parse_formula_str(s: str) -> Formula:
    tokens = tokenize(s)
    p = Parser(tokens)
    return p.parse()


# ========== ПРЕОБРАЗОВАНИЕ В КНФ ==========

def eliminate_implications(node: Formula) -> Formula:
    if isinstance(node, Implies):
        left = eliminate_implications(node.left)
        right = eliminate_implications(node.right)
        # A → B ≡ ¬A ∨ B
        return Or(Not(left), right)
    if isinstance(node, And):
        return And(eliminate_implications(node.left), eliminate_implications(node.right))
    if isinstance(node, Or):
        return Or(eliminate_implications(node.left), eliminate_implications(node.right))
    if isinstance(node, Not):
        return Not(eliminate_implications(node.sub))
    return node


def to_nnf(node: Formula) -> Formula:
    """
    Преобразование в NNF (Normal Negation Form)
    """
    if isinstance(node, Not):
        sub = node.sub
        if isinstance(sub, Not):
            return to_nnf(sub.sub)
        if isinstance(sub, And):
            return Or(to_nnf(Not(sub.left)), to_nnf(Not(sub.right)))
        if isinstance(sub, Or):
            return And(to_nnf(Not(sub.left)), to_nnf(Not(sub.right)))
        return Not(to_nnf(sub))

    if isinstance(node, And):
        return And(to_nnf(node.left), to_nnf(node.right))
    if isinstance(node, Or):
        return Or(to_nnf(node.left), to_nnf(node.right))
    return node


def distribute_or_over_and(node: Formula) -> Formula:
    if isinstance(node, Or):
        A = distribute_or_over_and(node.left)
        B = distribute_or_over_and(node.right)

        if isinstance(A, And):
            return And(
                distribute_or_over_and(Or(A.left, B)),
                distribute_or_over_and(Or(A.right, B)),
            )
        if isinstance(B, And):
            return And(
                distribute_or_over_and(Or(A, B.left)),
                distribute_or_over_and(Or(A, B.right)),
            )
        return Or(A, B)

    if isinstance(node, And):
        return And(
            distribute_or_over_and(node.left),
            distribute_or_over_and(node.right)
        )

    return node


def to_cnf(node: Formula) -> Formula:
    node = eliminate_implications(node)
    node = to_nnf(node)
    node = distribute_or_over_and(node)
    return node


# ========== СБОР КЛАУЗ ==========

def collect_literals(node: Formula):
    if isinstance(node, Or):
        return collect_literals(node.left) + collect_literals(node.right)

    if isinstance(node, Not) and isinstance(node.sub, Pred):
        return [("not", (node.sub.name, tuple(node.sub.args)))]

    if isinstance(node, Pred):
        return [(node.name, tuple(node.args))]

    raise ValueError(f"Ожидался литерал, а получено: {node}")


def collect_clauses(node: Formula):
    if isinstance(node, And):
        return collect_clauses(node.left) + collect_clauses(node.right)
    return [collect_literals(node)]


# ========== РАЗБИЕНИЕ ПО ЗАПЯТЫМ НА ВЕРХНЕМ УРОВНЕ ==========

def split_top_commas(text: str):
    parts = []
    depth = 0
    buff = []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1

        if ch == "," and depth == 0:
            part = "".join(buff).strip()
            if part:
                parts.append(part)
            buff = []
        else:
            buff.append(ch)

    tail = "".join(buff).strip()
    if tail:
        parts.append(tail)

    return parts


# ========== ОСНОВНАЯ ФУНКЦИЯ ==========

def parse_all_to_clauses(text: str):
    """
    Принимает строку:
      "A, B -> C, ¬(D → E)"
    Возвращает список клауз:
      [ [('A',())], [('not',('B',())), ('C',())], ... ]
    """
    clauses = []
    for f_str in split_top_commas(text):
        if not f_str:
            continue
        ast = parse_formula_str(f_str)
        cnf = to_cnf(ast)
        clauses.extend(collect_clauses(cnf))
    return clauses
