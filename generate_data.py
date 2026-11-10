"""Генератор СИНТЕТИЧЕСКИХ демо-данных для «Дәлел».

Данные выдуманы. В них намеренно заложены четыре эффекта, чтобы показать работу системы:
1. Учебник А чаще используют городские школы с сильными учениками (ловушка сырых средних).
2. Тема Т01 трудна везде.
3. Тема Т08 слаба только с учебником А.
4. Тема Т07 провалена в нескольких школах; в теме Т05 одно некачественное задание.

Запуск: python generate_data.py
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# код, название, часы, сколько последующих тем опираются, сдвиг сложности
TOPICS = [
    ("Т01", "Отношения и пропорции", 22, 4, 1.00),
    ("Т02", "Проценты", 14, 2, 0.00),
    ("Т03", "Рациональные числа", 16, 5, -0.50),
    ("Т04", "Действия с рациональными числами", 26, 5, -0.15),
    ("Т05", "Алгебраические выражения", 18, 3, -0.30),
    ("Т06", "Линейные уравнения", 20, 3, -0.25),
    ("Т07", "Линейные неравенства", 14, 1, 0.20),
    ("Т08", "Координатная плоскость", 14, 2, -0.10),
    ("Т09", "Статистика и комбинаторика", 12, 0, -0.95),
    ("Т10", "Фигуры в пространстве", 14, 0, -0.85),
]

TOPIC_KK = {"Т01": "Қатынастар мен пропорциялар", "Т02": "Пайыздар", "Т03": "Рационал сандар",
            "Т04": "Рационал сандарға амалдар", "Т05": "Алгебралық өрнектер", "Т06": "Сызықтық теңдеулер",
            "Т07": "Сызықтық теңсіздіктер", "Т08": "Координаталық жазықтық",
            "Т09": "Статистика және комбинаторика", "Т10": "Кеңістіктегі фигуралар"}

ITEM_TEXTS = {
    "Т01": ["Найдите неизвестный член пропорции 4 : x = 10 : 15.",
            "Из 6 кг муки получается 8 кг хлеба. Сколько хлеба получится из 15 кг муки?",
            "Масштаб карты 1 : 200 000. Чему равно расстояние на местности, если на карте оно 3,5 см?"],
    "Т02": ["Найдите 15% от числа 240.",
            "Цена товара выросла с 800 до 920 тенге. На сколько процентов выросла цена?",
            "Число уменьшили на 20% и получили 64. Найдите исходное число."],
    "Т03": ["Расположите числа в порядке возрастания: -3,5; 2; -7; 0; 1,2.",
            "Найдите модуль числа -12,4.",
            "Какое из чисел является противоположным числу -5/8?"],
    "Т04": ["Вычислите: -7 + 12 - (-5).",
            "Найдите значение выражения: (-2,5) · 4 : (-0,5).",
            "Вычислите: -3/4 + 5/6."],
    "Т05": ["Упростите выражение: 3a - 5 + 2a + 9.",
            "Раскройте скобки: -2(3x - 4).",
            "Найдите значение выражения 2x - 3y при x = -1, y = 2."],
    "Т06": ["Решите уравнение: 5x - 7 = 2x + 8.",
            "Решите уравнение: 3(x - 2) = 12.",
            "Сумма двух чисел равна 48, одно из них в 3 раза больше другого. Найдите меньшее число."],
    "Т07": ["Решите неравенство: 2x - 5 > 7.",
            "Укажите наибольшее целое решение неравенства 3x < 14.",
            "Решите неравенство: -4x ≥ 12."],
    "Т08": ["В какой координатной четверти лежит точка A(-3; 5)?",
            "Найдите координаты середины отрезка с концами B(2; -4) и C(6; 2).",
            "Точка M симметрична точке K(4; -1) относительно оси абсцисс. Найдите координаты M."],
    "Т09": ["Найдите среднее арифметическое чисел 12, 15, 9, 20.",
            "Найдите медиану ряда: 3, 8, 5, 12, 7.",
            "Сколькими способами можно выбрать старосту и его заместителя из 5 учеников?"],
    "Т10": ["Сколько рёбер у прямоугольного параллелепипеда?",
            "Найдите объём куба с ребром 4 см.",
            "Какая фигура получается при вращении прямоугольника вокруг одной из его сторон?"],
}

BAD_ITEM = "З15"          # третье задание темы Т05: не различает сильных и слабых
WEAK_SCHOOLS_TOPIC = "Т07"
TEXTBOOK_WEAK_TOPIC = "Т08"
TEXTBOOK_EFFECT = {"Учебник А": 0.0, "Учебник Б": 0.35, "Учебник В": 0.05}


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def main():
    plan = pd.DataFrame(
        [(c, n, h, p) for c, n, h, p, _ in TOPICS],
        columns=["topic_code", "topic_name", "hours", "prereq_count"],
    )

    plan["topic_name_kk"] = plan["topic_code"].map(TOPIC_KK)

    items = []
    k = 0
    for code, _, _, _, shift in TOPICS:
        for text in ITEM_TEXTS[code]:
            k += 1
            items.append((f"З{k:02d}", text, code, shift + rng.normal(0, 0.15)))
    items = pd.DataFrame(items, columns=["item_id", "item_text", "topic_code", "bdiff"])

    n_schools = 60
    schools = []
    for s in range(1, n_schools + 1):
        area = "город" if rng.random() < 0.45 else "село"
        probs = [0.78, 0.07, 0.15] if area == "город" else [0.08, 0.67, 0.25]
        textbook = rng.choice(list(TEXTBOOK_EFFECT), p=probs)
        lang = "казахский" if rng.random() < 0.7 else "русский"
        base = (1.25 if area == "город" else 0.05) + rng.normal(0, 0.22)
        size = int(rng.integers(35, 75)) if area == "город" else int(rng.integers(22, 55))
        schools.append((f"Ш{s:02d}", area, textbook, lang, base, size))
    schools = pd.DataFrame(schools, columns=["school_id", "area", "textbook", "lang", "base", "nsz"])
    schools.loc[schools.index[-1], "nsz"] = 18   # одна малая школа, чтобы показать метку «недостаточно данных»

    # школы, где провалена тема Т07 (с любым учебником)
    cand = schools.school_id.to_numpy()
    weak_schools = set(rng.choice(cand, size=8, replace=False))

    rows = []
    sid = 0
    for sc in schools.itertuples():
        for _ in range(sc.nsz):
            sid += 1
            pre = sc.base + rng.normal(0, 0.9)                 # уровень до изучения курса
            prior = float(np.clip(50 + 16 * pre + rng.normal(0, 6), 0, 100))
            theta = pre + TEXTBOOK_EFFECT[sc.textbook]
            for it in items.itertuples():
                if it.item_id == BAD_ITEM:
                    p = 0.30
                else:
                    extra = 0.0
                    if it.topic_code == TEXTBOOK_WEAK_TOPIC and sc.textbook == "Учебник А":
                        extra -= 1.35
                    if it.topic_code == WEAK_SCHOOLS_TOPIC and sc.school_id in weak_schools:
                        extra -= 2.4
                    p = sigmoid(theta - it.bdiff + extra)
                rows.append((f"У{sid:04d}", sc.school_id, sc.textbook, sc.lang, sc.area,
                             round(prior, 1), it.item_id, int(rng.random() < p)))

    results = pd.DataFrame(rows, columns=["student_id", "school_id", "textbook", "lang", "area",
                                          "prior_score", "item_id", "correct"])
    results.to_csv("data/results.csv", index=False)
    items.drop(columns="bdiff").to_csv("data/items.csv", index=False)
    plan.to_csv("data/plan.csv", index=False)
    print(f"учеников: {sid}, школ: {n_schools}, заданий: {len(items)}, строк: {len(results)}")
    print("школы со слабой Т07:", sorted(weak_schools))


if __name__ == "__main__":
    main()
