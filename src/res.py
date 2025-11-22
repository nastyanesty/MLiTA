def is_variable(term):
    # является ли терм переменной (начинается с маленькой буквы)
    if isinstance(term, str):
        return term and term[0].islower()
    return False


def is_predicate(lit):
    # является ли литерал предикатом
    return isinstance(lit, tuple) and len(lit) == 2 and isinstance(lit[1], tuple)


def unify(x, y, substitution=None):
    # унификация двух термов
    if substitution is None:
        substitution = {}

    # термы одинаковы
    if x == y:
        return substitution

    # унификация x
    if is_variable(x):
        # уже есть подстановка x
        if x in substitution:
            return unify(substitution[x], y, substitution)
        # есть подстановка y
        elif is_variable(y) and y in substitution:
            return unify(x, substitution[y], substitution)
        # нет подстановок
        else:
            if term_check(x, y, substitution):
                return None
            substitution[x] = y
            return substitution

    # аналогично для y
    elif is_variable(y):
        return unify(y, x, substitution)

    # унификация предикатов
    elif is_predicate(x) and is_predicate(y):
        if x[0] != y[0] or len(x[1]) != len(y[1]):
            return None
        for x_arg, y_arg in zip(x[1], y[1]):
            substitution = unify(x_arg, y_arg, substitution)
            if substitution is None:
                return None
        return substitution
    return None


def term_check(var, term, substitution):
    # проверка вхождения переменной в терм (предикат)
    if isinstance(term, tuple):
        return any(term_check(var, item, substitution) for item in term)
    return False


def apply_substitution(expr, substitution):
    # применение унификации к выражению
    if not substitution:
        return expr

    # переменная
    if isinstance(expr, str):
        return substitution.get(expr, expr)

    # кортеж (рекурсия)
    if isinstance(expr, tuple):
        # отрицание
        if len(expr) == 2 and expr[0] == 'not':
            return ('not', apply_substitution(expr[1], substitution))
        # по всем элементам кортежа
        else:
            return tuple(apply_substitution(item, substitution) for item in expr)
    return expr


def resolve_clauses(clause1, clause2):
    # резолюция двух клауз (резольвент)
    resolvents = []

    for i, lit1 in enumerate(clause1):
        for j, lit2 in enumerate(clause2):
            pos_lit = None
            neg_lit = None
            # пары предикат - предикат с отрицанием
            if is_predicate(lit1) and lit2[0] == 'not' and is_predicate(lit2[1]):
                pos_lit = lit1
                neg_lit = lit2[1]
            elif lit1[0] == 'not' and is_predicate(lit1[1]) and is_predicate(lit2):
                pos_lit = lit2
                neg_lit = lit1[1]
            else:
                continue

            # унификация (не сработает, если предикаты разные)
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
    # стратегия вычеркивания - 5.8

    # other_clause пустая, а clause - нет, не поддизъюнкт
    if not other_clause and clause:
        return False

    # унификация каждого литерала other_clause с каким-либо литералом clause
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
    # стратегия вычеркивания - 5.8
    if not clauses:
        return clauses

    # сортировка по длине
    # более короткие клаузы с большей вероятностью будут поддизъюнктами
    sorted_clauses = sorted(clauses, key=len)
    result = []

    # является ли clause наддизъюнктом какой-либо клаузы
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
    # стратегия вычеркивания - 5.8
    for i, lit1 in enumerate(clause):
        for j, lit2 in enumerate(clause):
            if i >= j:
                continue
            # пары предикат - предикат с отрицанием
            if is_predicate(lit1) and lit2[0] == 'not' and is_predicate(lit2[1]):
                substitution = unify(lit1, lit2[1], {})
                if substitution is not None:
                    return True
            elif lit1[0] == 'not' and is_predicate(lit1[1]) and is_predicate(lit2):
                substitution = unify(lit1[1], lit2, {})
                if substitution is not None:
                    return True
    return False


def clause_to_str(clause):
    # клауза в строку
    if not clause:
        return "□"
    literals = []
    for lit in clause:
        if isinstance(lit, str):
            literals.append(lit)
        elif lit[0] == 'not':
            if isinstance(lit[1], tuple) and len(lit[1]) == 2 and isinstance(lit[1][1], tuple):
                literals.append(f"¬{lit[1][0]}{{{', '.join(lit[1][1])}}}")
            else:
                literals.append(f"¬{lit[1]}")
        elif isinstance(lit, tuple) and len(lit) == 2 and isinstance(lit[1], tuple):
            literals.append(f"{lit[0]}{{{', '.join(lit[1])}}}")
        else:
            literals.append(str(lit))
    return " ∨ ".join(literals)


def substitution_to_str(substitution):
    # подстановка в строку
    if not substitution:
        return "{}"
    items = []
    for var, value in substitution.items():
        items.append(f"{var}/{value}")
    return "{" + ", ".join(items) + "}"


def find_clause_name(clause, clause_dict):
    # возвращает имя резольвенты
    for name, cl in clause_dict.items():
        if cl == clause:
            return name
    return "Unknown"

def has_constants(clause):
    # содержит ли клауза константы
    constants = ['Марк', 'Цезарь']
    for lit in clause:
        if isinstance(lit, tuple) and lit[0] != 'not':
            terms = lit[1] if isinstance(lit[1], tuple) else (lit[1],)
            if any(c in terms for c in constants):
                return True
    return False


def prove(clauses):
    # основная функция
    # полученные резольвенты
    print("Начальные резольвенты:")
    clause_dict = {}
    for i, clause in enumerate(clauses, 1):
        clause_name = f"C{i}"
        clause_dict[clause_name] = clause
        print(f"{clause_name}: {clause_to_str(clause)}")

    # настройка для восстановления (для поиска полезных шагов)
    steps = []
    parent_map = {}

    length = len(clauses)
    next_clause_num = length + 1  # число следующей резольвенты
    active_clauses = [clauses[-1]]  # последняя, которую нужно доказать
    used_pairs = set()  # повторная обработка пар
    current = clauses[-1]

    # стратегия вычеркивания - 5.8
    initial_clauses = [c for c in clauses if not is_tautology(c)]
    initial_clauses = remove_subsumed_clauses(initial_clauses)
    # если что-то удалилось, вывод обновленных резольвент
    if len(initial_clauses) != length:
        print(f"Удалено тавтологий/наддизъюнктов: {length - len(initial_clauses)}")
        clauses = initial_clauses
        for i, clause in enumerate(clauses, 1):
            clause_name = f"C{i}"
            clause_dict[clause_name] = clause
            print(f"{clause_name}: {clause_to_str(clause)}")
        # обновление параметров
        length = len(clauses)
        next_clause_num = length + 1
        active_clauses = [clauses[-1]]

    # основной цикл
    while active_clauses:
        current = active_clauses.pop(0)
        current_name = find_clause_name(current, clause_dict)
        other_clauses = sorted(clauses, key=lambda c: (len(c), has_constants(c)))

        # обработка всех пар (без повторного использования)
        for other in other_clauses:
            other_name = find_clause_name(other, clause_dict)
            pair = tuple(sorted([id(current), id(other)]))
            if pair in used_pairs:
                continue
            used_pairs.add(pair)

            # резолюции
            resolvents = resolve_clauses(current, other)
            for resolvent, substitution in resolvents:
                # пропуск тавтологий
                if is_tautology(resolvent):
                    continue

                # найдена пустая резолюция, доказано
                if not resolvent:
                    # полезные шаги и все шаги
                    useful_steps = reconstruct_proof_path(current_name, other_name, parent_map, clause_dict, length)
                    if substitution:
                        steps.append(f"Шаг {len(steps) + 1}: Резолюция {current_name} и {other_name} (унификация: {substitution_to_str(substitution)}) -> □")
                    else:
                        steps.append(f"Шаг {len(steps) + 1}: Резолюция {current_name} и {other_name} -> □")
                    # вывод
                    print("\nПолная последовательность шагов:")
                    for step in steps:
                        print(step)
                    print(f"Формула доказана за {len(steps)} шагов")
                    print("\nПолезные резолюции (шаги):")
                    for step in useful_steps:
                        print(step)
                    return

                # является ли наддизъюнктом существующих клауз
                is_subsumed = False
                for existing_clause in clauses:
                    if is_subsumed_by(resolvent, existing_clause):
                        is_subsumed = True
                        break

                # если не наддизъюнкт и не дубликат
                if not is_subsumed and resolvent not in clauses:
                    # все клаузы, которые являются наддизъюнктами новой, удаляются
                    clauses = [c for c in clauses if not is_subsumed_by(c, resolvent)]
                    # добавление в резольвенты и цикл
                    clauses.append(resolvent)
                    active_clauses.append(resolvent)
                    # добавление в словарь, родителей и обновление параметра
                    new_name = f"C{next_clause_num}"
                    clause_dict[new_name] = resolvent
                    parent_map[new_name] = (current_name, other_name, substitution)
                    next_clause_num += 1
                    # вывод
                    if substitution:
                        step_desc = f"Шаг {len(steps) + 1} - {new_name}: Резолюция {current_name} и {other_name} (унификация: {substitution_to_str(substitution)}) -> {new_name}: {clause_to_str(resolvent)}"
                    else:
                        step_desc = f"Шаг {len(steps) + 1} - {new_name}: Резолюция {current_name} и {other_name} -> {new_name}: {clause_to_str(resolvent)}"
                    steps.append(step_desc)

                    # лимит
                    if len(steps) > 1000:
                        print("Превышен лимит шагов")
                        return
    # если не будет резолюций вообще
    if current == clauses[-1]:
        print("\nФормула не доказана: резолюций с доказуемой резольвентой нет")

def reconstruct_proof_path(clause1_name, clause2_name, parent_map, clause_dict, length):
    # путь доказательства от пустой клаузы к начальным клаузам

    def get_all_ancestors(clause_name):
        # рекурсивно собирает всех предков клаузы
        ancestors = {clause_name}
        if clause_name in parent_map:
            parent1, parent2, _ = parent_map[clause_name]
            ancestors.update(get_all_ancestors(parent1))
            ancestors.update(get_all_ancestors(parent2))
        return ancestors

    def topological_sort(clause_names, parent_map):
        # сортировка клауз по зависимостям
        visited = set()
        result = []

        def visit(clause_name):
            if clause_name in visited:
                return
            visited.add(clause_name)
            # сначала родители (если они есть)
            if clause_name in parent_map:
                parent1, parent2, _ = parent_map[clause_name]
                # только производные клаузы (не начальные)
                if parent1 in parent_map or not parent1.startswith('C') or int(parent1[1:]) > length:
                    visit(parent1)
                if parent2 in parent_map or not parent2.startswith('C') or int(parent2[1:]) > length:
                    visit(parent2)
            result.append(clause_name)
        for clause in clause_names:
            visit(clause)
        return result

    # все клаузы, участвующие в доказательстве
    all_ancestors = get_all_ancestors(clause1_name).union(get_all_ancestors(clause2_name))
    # начальные и производные клаузы
    initial_clauses = []
    derived_clauses = []
    for clause_name in all_ancestors:
        if clause_name.startswith('C') and int(clause_name[1:]) <= length:
            initial_clauses.append(clause_name)
        else:
            derived_clauses.append(clause_name)

    # начальные клаузы по номеру - сортировка
    initial_clauses.sort(key=lambda x: int(x[1:]))

    # производные клаузы - сортировка
    sorted_derived = topological_sort(derived_clauses, parent_map)

    # упорядоченный вывод
    useful_steps = []
    # все начальные клаузы
    for clause_name in initial_clauses:
        useful_steps.append(f"Начальная {clause_name}: {clause_to_str(clause_dict[clause_name])}")
    # шаги доказательства с нумерацией
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

    # финальный шаг
    useful_steps.append(f"Шаг {step_number}: Резолюция {clause1_name} и {clause2_name} -> □ (пустая клауза)")
    return useful_steps
