def is_variable(term):
    # является ли терм переменной (одна маленькая буква)
    return isinstance(term, str) and len(term) == 1 and term.islower()


def is_constant(term):
    # является ли терм константой (начинается с большой буквы или несколько символов)
    if isinstance(term, str):
        return term and (term[0].isupper() or len(term) > 1)
    return False


def is_function(term):
    # является ли терм функцией вида f(a,b)
    return (isinstance(term, tuple) and
            len(term) >= 1 and
            isinstance(term[0], str) and
            term[0].islower() and  # имя функции начинается с маленькой буквы
            len(term) > 1)  # есть хотя бы один аргумент


def is_predicate(lit):
    # является ли литерал предикатом
    return (isinstance(lit, tuple) and
            len(lit) >= 1 and
            isinstance(lit[0], str) and
            lit[0].isupper())  # имя предиката начинается с большой буквы


def get_predicate_name_and_args(lit):
    # возвращает имя предиката и его аргументы
    if is_predicate(lit):
        return lit[0], lit[1:]
    return None, []


def get_function_name_and_args(term):
    # возвращает имя функции и ее аргументы
    if is_function(term):
        return term[0], term[1:]
    return None, []


def unify(x, y, substitution=None):
    # унификация двух термов
    if substitution is None:
        substitution = {}

    # если уже одинаковы с учетом подстановки
    if x == y:
        return substitution

    # переменная x
    if is_variable(x):
        # проверка на вхождение переменной в терм
        if term_check(x, y, substitution):
            return None
        # применяем существующую подстановку к x
        if x in substitution:
            return unify(substitution[x], y, substitution)
        # применяем существующую подстановку к y, если y переменная
        elif is_variable(y) and y in substitution:
            return unify(x, substitution[y], substitution)
        else:
            substitution[x] = y
            return substitution

    # переменная y
    elif is_variable(y):
        return unify(y, x, substitution)

    # функции
    elif is_function(x) and is_function(y):
        x_name, x_args = get_function_name_and_args(x)
        y_name, y_args = get_function_name_and_args(y)

        if x_name != y_name or len(x_args) != len(y_args):
            return None

        for x_arg, y_arg in zip(x_args, y_args):
            substitution = unify(x_arg, y_arg, substitution)
            if substitution is None:
                return None
        return substitution

    # предикаты
    elif is_predicate(x) and is_predicate(y):
        x_name, x_args = get_predicate_name_and_args(x)
        y_name, y_args = get_predicate_name_and_args(y)

        if x_name != y_name or len(x_args) != len(y_args):
            return None

        for x_arg, y_arg in zip(x_args, y_args):
            substitution = unify(x_arg, y_arg, substitution)
            if substitution is None:
                return None
        return substitution

    # константы
    elif is_constant(x) and is_constant(y):
        return substitution if x == y else None

    # разные типы термов
    else:
        return None


def term_check(var, term, substitution):
    # проверка вхождения переменной в терм
    # сначала применяем текущие подстановки
    term = apply_substitution(term, substitution)

    if var == term:
        return True

    if is_variable(term):
        return False

    if is_function(term):
        _, args = get_function_name_and_args(term)
        for arg in args:
            if term_check(var, arg, substitution):
                return True

    if is_predicate(term):
        _, args = get_predicate_name_and_args(term)
        for arg in args:
            if term_check(var, arg, substitution):
                return True

    if isinstance(term, tuple):
        for item in term:
            if term_check(var, item, substitution):
                return True

    return False


def apply_substitution(expr, substitution):
    # применение подстановки к выражению
    if not substitution or expr is None:
        return expr

    # переменная
    if is_variable(expr):
        # рекурсивно применяем подстановку по цепочке
        result = expr
        while result in substitution and substitution[result] != result:
            result = substitution[result]
        return result

    # константа
    if is_constant(expr):
        return expr

    # функция
    if is_function(expr):
        func_name, args = get_function_name_and_args(expr)
        new_args = tuple(apply_substitution(arg, substitution) for arg in args)
        return (func_name,) + new_args

    # предикат
    if is_predicate(expr):
        pred_name, args = get_predicate_name_and_args(expr)
        new_args = tuple(apply_substitution(arg, substitution) for arg in args)
        return (pred_name,) + new_args

    # отрицание
    if isinstance(expr, tuple) and len(expr) == 2 and expr[0] == 'not':
        return ('not', apply_substitution(expr[1], substitution))

    # кортеж (рекурсия)
    if isinstance(expr, tuple):
        return tuple(apply_substitution(item, substitution) for item in expr)

    return expr


def resolve_clauses(clause1, clause2):
    # резолюция двух клауз (резольвент)
    resolvents = []

    for i, lit1 in enumerate(clause1):
        for j, lit2 in enumerate(clause2):
            # определяем, какая пара: предикат и его отрицание
            pos_lit = None
            neg_lit = None

            if is_predicate(lit1) and isinstance(lit2, tuple) and lit2[0] == 'not' and is_predicate(lit2[1]):
                pos_lit = lit1
                neg_lit = lit2[1]
            elif isinstance(lit1, tuple) and lit1[0] == 'not' and is_predicate(lit1[1]) and is_predicate(lit2):
                pos_lit = lit2
                neg_lit = lit1[1]
            else:
                continue

            # унификация
            substitution = unify(pos_lit, neg_lit, {})
            if substitution is not None:
                # подстановка во всей клаузе
                new_clause = []
                # литералы из clause1 (кроме lit1) с подстановкой
                for k, lit in enumerate(clause1):
                    if k != i:
                        new_lit = apply_substitution(lit, substitution)
                        new_clause.append(new_lit)
                # литералы из clause2 (кроме lit2) с подстановкой
                for k, lit in enumerate(clause2):
                    if k != j:
                        new_lit = apply_substitution(lit, substitution)
                        new_clause.append(new_lit)

                # удаление дубликатов (склейка - 5.5)
                unique_clause = []
                for item in new_clause:
                    if item not in unique_clause:
                        unique_clause.append(item)
                resolvents.append((unique_clause, substitution))
    return resolvents


def is_subsumed_by(clause, other_clause):
    # является ли clause наддизъюнктом other_clause (other_clause ⊆ clause)
    if not other_clause and clause:
        return False

    # для каждого литерала в other_clause ищем соответствующий в clause
    for other_lit in other_clause:
        found_match = False
        for clause_lit in clause:
            substitution = unify(other_lit, clause_lit, {})
            if substitution is not None:
                found_match = True
                break
        if not found_match:
            return False
    return True


def remove_subsumed_clauses(clauses):
    # удаляет все наддизъюнкты из множества клауз
    if not clauses:
        return clauses

    sorted_clauses = sorted(clauses, key=len)
    result = []

    for i, clause in enumerate(sorted_clauses):
        is_subsumed = False
        for other in result:
            if is_subsumed_by(clause, other):
                is_subsumed = True
                break
        if not is_subsumed:
            result.append(clause)
    return result


def is_tautology(clause):
    # является ли клауза тавтологией (P и ¬P)
    for i, lit1 in enumerate(clause):
        for j, lit2 in enumerate(clause):
            if i >= j:
                continue

            # проверяем, являются ли они противоположными
            pos_lit = None
            neg_lit = None

            if is_predicate(lit1) and isinstance(lit2, tuple) and lit2[0] == 'not' and is_predicate(lit2[1]):
                pos_lit = lit1
                neg_lit = lit2[1]
            elif isinstance(lit1, tuple) and lit1[0] == 'not' and is_predicate(lit1[1]) and is_predicate(lit2):
                pos_lit = lit2
                neg_lit = lit1[1]
            else:
                continue

            # пробуем унифицировать
            substitution = unify(pos_lit, neg_lit, {})
            if substitution is not None:
                return True
    return False


def clause_to_str(clause):
    # клауза в строку
    if not clause:
        return "□"

    def term_to_str(term):
        if is_variable(term):
            return term
        elif is_constant(term):
            return term
        elif is_function(term):
            func_name, args = get_function_name_and_args(term)
            args_str = ", ".join(term_to_str(arg) for arg in args)
            return f"{func_name}({args_str})"
        elif is_predicate(term):
            pred_name, args = get_predicate_name_and_args(term)
            args_str = ", ".join(term_to_str(arg) for arg in args)
            return f"{pred_name}({args_str})"
        else:
            return str(term)

    literals = []
    for lit in clause:
        if is_predicate(lit):
            literals.append(term_to_str(lit))
        elif isinstance(lit, tuple) and lit[0] == 'not' and is_predicate(lit[1]):
            literals.append(f"¬{term_to_str(lit[1])}")
        else:
            literals.append(str(lit))

    return " ∨ ".join(literals)


def substitution_to_str(substitution):
    # подстановка в строку
    if not substitution:
        return "{}"

    def term_to_str(term):
        if is_variable(term):
            return term
        elif is_constant(term):
            return term
        elif is_function(term):
            func_name, args = get_function_name_and_args(term)
            args_str = ", ".join(term_to_str(arg) for arg in args)
            return f"{func_name}({args_str})"
        else:
            return str(term)

    items = []
    for var, value in substitution.items():
        items.append(f"{var}/{term_to_str(value)}")
    return "{" + ", ".join(items) + "}"


def find_clause_name(clause, clause_dict):
    # возвращает имя резольвенты
    for name, cl in clause_dict.items():
        if cl == clause:
            return name
    return "Unknown"


def has_constants(clause):
    # содержит ли клауза константы
    def has_constants_in_term(term):
        if is_constant(term):
            return True
        elif is_function(term):
            _, args = get_function_name_and_args(term)
            return any(has_constants_in_term(arg) for arg in args)
        elif is_predicate(term):
            _, args = get_predicate_name_and_args(term)
            return any(has_constants_in_term(arg) for arg in args)
        return False

    for lit in clause:
        if is_predicate(lit):
            if any(has_constants_in_term(arg) for arg in get_predicate_name_and_args(lit)[1]):
                return True
        elif isinstance(lit, tuple) and lit[0] == 'not' and is_predicate(lit[1]):
            if any(has_constants_in_term(arg) for arg in get_predicate_name_and_args(lit[1])[1]):
                return True
    return False


def prove(clauses):
    # основная функция
    print("Начальные резольвенты:")
    clause_dict = {}
    for i, clause in enumerate(clauses, 1):
        clause_name = f"C{i}"
        clause_dict[clause_name] = clause
        print(f"{clause_name}: {clause_to_str(clause)}")

    steps = []
    parent_map = {}

    length = len(clauses)
    next_clause_num = length + 1
    active_clauses = [clauses[-1]]
    used_pairs = set()
    current = clauses[-1]

    # стратегия вычеркивания - 5.8
    initial_clauses = [c for c in clauses if not is_tautology(c)]
    initial_clauses = remove_subsumed_clauses(initial_clauses)

    if len(initial_clauses) != length:
        print(f"Удалено тавтологий/наддизъюнктов: {length - len(initial_clauses)}")
        clauses = initial_clauses
        clause_dict.clear()
        for i, clause in enumerate(clauses, 1):
            clause_name = f"C{i}"
            clause_dict[clause_name] = clause
            print(f"{clause_name}: {clause_to_str(clause)}")

        length = len(clauses)
        next_clause_num = length + 1
        active_clauses = [clauses[-1]]

    # основной цикл
    while active_clauses:
        current = active_clauses.pop(0)
        current_name = find_clause_name(current, clause_dict)

        # сортируем клаузы для эффективности
        other_clauses = sorted(clauses, key=lambda c: (len(c), not has_constants(c)))

        for other in other_clauses:
            if current == other:
                continue

            other_name = find_clause_name(other, clause_dict)
            pair = tuple(sorted([current_name, other_name]))

            if pair in used_pairs:
                continue
            used_pairs.add(pair)

            # резолюции
            resolvents = resolve_clauses(current, other)
            for resolvent, substitution in resolvents:
                # пропуск тавтологий
                if is_tautology(resolvent):
                    continue

                # найдена пустая резолюция
                if not resolvent:
                    useful_steps = reconstruct_proof_path(current_name, other_name, parent_map, clause_dict, length)
                    if substitution:
                        steps.append(
                            f"Шаг {len(steps) + 1}: Резолюция {current_name} и {other_name} (унификация: {substitution_to_str(substitution)}) -> □")
                    else:
                        steps.append(f"Шаг {len(steps) + 1}: Резолюция {current_name} и {other_name} -> □")

                    print("\nПолная последовательность шагов:")
                    for step in steps:
                        print(step)

                    def get_step_word(count):
                        if count % 10 == 1 and count % 100 != 11:
                            return "шаг"
                        elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
                            return "шага"
                        else:
                            return "шагов"

                    print(f"Формула доказана за {len(steps)} {get_step_word(len(steps))}")
                    print("\nПолезные резолюции (шаги):")
                    for step in useful_steps:
                        print(step)
                    return

                # проверяем, не является ли наддизъюнктом
                is_subsumed = False
                for existing_clause in clauses:
                    if is_subsumed_by(resolvent, existing_clause):
                        is_subsumed = True
                        break

                if not is_subsumed and resolvent not in clauses:
                    # удаляем наддизъюнкты
                    clauses = [c for c in clauses if not is_subsumed_by(c, resolvent)]

                    # добавляем новую клаузу
                    clauses.append(resolvent)
                    active_clauses.append(resolvent)

                    new_name = f"C{next_clause_num}"
                    clause_dict[new_name] = resolvent
                    parent_map[new_name] = (current_name, other_name, substitution)
                    next_clause_num += 1

                    if substitution:
                        step_desc = f"Шаг {len(steps) + 1} - {new_name}: Резолюция {current_name} и {other_name} (унификация: {substitution_to_str(substitution)}) -> {new_name}: {clause_to_str(resolvent)}"
                    else:
                        step_desc = f"Шаг {len(steps) + 1} - {new_name}: Резолюция {current_name} и {other_name} -> {new_name}: {clause_to_str(resolvent)}"
                    steps.append(step_desc)

                    if len(steps) > 1000:
                        print("Превышен лимит шагов")
                        return

    print("\nФормула не доказана")


def reconstruct_proof_path(clause1_name, clause2_name, parent_map, clause_dict, length):
    # путь доказательства от пустой клаузы к начальным клаузам

    def get_all_ancestors(anc_clause_name):
        ancestors = {anc_clause_name}
        if anc_clause_name in parent_map:
            parent_1, parent_2, _ = parent_map[anc_clause_name]
            ancestors.update(get_all_ancestors(parent_1))
            ancestors.update(get_all_ancestors(parent_2))
        return ancestors

    def topological_sort(clause_names):
        visited = set()
        result = []

        def visit(visit_clause_name):
            if visit_clause_name in visited:
                return
            visited.add(visit_clause_name)

            if visit_clause_name in parent_map:
                parent_1, parent_2, _ = parent_map[visit_clause_name]
                if parent_1 in parent_map or not parent_1.startswith('C') or int(parent_1[1:]) > length:
                    visit(parent_1)
                if parent_2 in parent_map or not parent_2.startswith('C') or int(parent_2[1:]) > length:
                    visit(parent_2)
            result.append(visit_clause_name)

        for clause in clause_names:
            visit(clause)
        return result

    # все клаузы, участвующие в доказательстве
    all_ancestors = get_all_ancestors(clause1_name).union(get_all_ancestors(clause2_name))

    initial_clauses = []
    derived_clauses = []

    for clause_name in all_ancestors:
        if clause_name.startswith('C') and int(clause_name[1:]) <= length:
            initial_clauses.append(clause_name)
        else:
            derived_clauses.append(clause_name)

    initial_clauses.sort(key=lambda x: int(x[1:]))
    sorted_derived = topological_sort(derived_clauses)

    useful_steps = []

    for clause_name in initial_clauses:
        useful_steps.append(f"Начальная {clause_name}: {clause_to_str(clause_dict[clause_name])}")

    step_number = 1
    for clause_name in sorted_derived:
        if clause_name in parent_map:
            parent1, parent2, substitution = parent_map[clause_name]
            if substitution:
                step_desc = f"Шаг {step_number} - {clause_name}: Резолюция {parent1} и {parent2} (унификация: {substitution_to_str(substitution)}) -> {clause_name}: {clause_to_str(clause_dict[clause_name])}"
            else:
                step_desc = f"Шаг {step_number} - {clause_name}: Резолюция {parent1} и {parent2} -> {clause_name}: {clause_to_str(clause_dict[clause_name])}"
            useful_steps.append(step_desc)
            step_number += 1

    useful_steps.append(f"Шаг {step_number}: Резолюция {clause1_name} и {clause2_name} -> □ (пустая клауза)")
    return useful_steps