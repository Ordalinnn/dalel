"""Расчётное ядро «Дәлел». Все числа продукта считаются здесь, без языковой модели."""
import re

import numpy as np
import pandas as pd
import statsmodels.api as sm

MIN_GROUP = 30          # меньше учеников: вывод не делаем
DISCRIMINATION_MIN = 0.10
TEXTBOOK_GAP = 0.08     # учебник слабее остальных по теме минимум на 8 п.п.
SCHOOL_GAP = 0.12       # школа слабее ожидаемого минимум на 12 п.п.
MAX_SHIFT = 0.20        # часы темы меняются не более чем на 20%

REQUIRED = {
    "results": ["student_id", "school_id", "textbook", "lang", "area", "prior_score", "item_id", "correct"],
    "items": ["item_id", "item_text", "topic_code"],
    "plan": ["topic_code", "topic_name", "hours", "prereq_count"],
}


def validate(results, items, plan):
    """Возвращает список понятных сообщений об ошибках; пустой список значит, что данные годятся."""
    errors = []
    for name, df in (("results", results), ("items", items), ("plan", plan)):
        missing = [c for c in REQUIRED[name] if c not in df.columns]
        if missing:
            errors.append(f"В файле {name} нет столбцов: {', '.join(missing)}")
    if errors:
        return errors
    if not set(results["correct"].dropna().unique()) <= {0, 1}:
        errors.append("Столбец correct должен содержать только 0 и 1")
    unknown = set(results["item_id"]) - set(items["item_id"])
    if unknown:
        errors.append(f"В результатах есть задания, которых нет в файле items: {sorted(unknown)[:5]}")
    unknown = set(items["topic_code"]) - set(plan["topic_code"])
    if unknown:
        errors.append(f"В items есть темы, которых нет в плане: {sorted(unknown)}")
    return errors


def prepare(results):
    meta = (results.drop_duplicates("student_id")
            .set_index("student_id")[["school_id", "textbook", "lang", "area", "prior_score"]])
    wide = results.pivot_table(index="student_id", columns="item_id", values="correct", aggfunc="first")
    return meta.loc[wide.index], wide


def item_stats(wide, items):
    """Доля верных ответов и различающая способность (связь задания с остальным тестом)."""
    total = wide.sum(axis=1)
    rows = []
    for item in wide.columns:
        rest = total - wide[item]
        disc = np.corrcoef(wide[item].astype(float), rest.astype(float))[0, 1]
        rows.append((item, wide[item].mean(), disc))
    st = pd.DataFrame(rows, columns=["item_id", "p_correct", "discrimination"])
    st = st.merge(items[["item_id", "item_text", "topic_code"]], on="item_id", how="left")
    st["flagged"] = st["discrimination"] < DISCRIMINATION_MIN
    return st


def topic_scores(wide, items, exclude=()):
    """Доля верных ответов ученика по каждой теме (0..1)."""
    out = {}
    for code, grp in items.groupby("topic_code"):
        cols = [i for i in grp["item_id"] if i in wide.columns and i not in exclude]
        if cols:
            out[code] = wide[cols].mean(axis=1)
    return pd.DataFrame(out)


def mastery_table(scores, meta, n_boot=300, seed=0):
    """Освоение тем с 95% интервалом. Бутстреп идёт по школам: ученики одной школы похожи друг на друга."""
    rng = np.random.default_rng(seed)
    schools = meta["school_id"].to_numpy()
    uniq, inv = np.unique(schools, return_inverse=True)
    vals = scores.to_numpy(dtype=float)
    sums = np.zeros((len(uniq), vals.shape[1]))
    np.add.at(sums, inv, vals)
    counts = np.bincount(inv, minlength=len(uniq)).astype(float)
    idx = rng.integers(0, len(uniq), size=(n_boot, len(uniq)))
    boot = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)[:, None]
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
    return pd.DataFrame({
        "topic_code": scores.columns,
        "mastery": vals.mean(axis=0),
        "lo": lo, "hi": hi,
        "n_students": len(scores), "n_schools": len(uniq),
    })


def _design(meta, textbooks, extra=None, covariates=("prior_score", "area", "lang")):
    X = pd.DataFrame({"const": 1.0}, index=meta.index)
    for tb in textbooks[1:]:
        X[f"tb::{tb}"] = (meta["textbook"] == tb).astype(float)
    if "prior_score" in covariates:
        X["prior_score"] = meta["prior_score"].astype(float)
    for col in ("area", "lang"):
        if col in covariates:
            for lv in sorted(meta[col].unique())[1:]:
                X[f"{col}::{lv}"] = (meta[col] == lv).astype(float)
    if extra is not None:
        X["rest_score"] = extra.astype(float)
    return X


def _fit(y, X, meta):
    groups = pd.factorize(meta["school_id"])[0]
    return sm.OLS(y.astype(float), X).fit(cov_type="cluster", cov_kwds={"groups": groups})


def compare_textbooks(total, meta, adjusted=True):
    """Средний результат по учебникам.

    adjusted=False: сырые средние. adjusted=True: с поправкой на прошлый балл,
    тип местности и язык обучения (учебники сравниваются на «среднем» ученике).
    """
    textbooks = sorted(meta["textbook"].unique())
    X = _design(meta, textbooks, covariates=("prior_score", "area", "lang") if adjusted else ())
    res = _fit(total, X, meta)
    base = X.mean(axis=0)
    rows = []
    for tb in textbooks:
        c = base.copy()
        for other in textbooks[1:]:
            c[f"tb::{other}"] = 1.0 if other == tb else 0.0
        t = res.t_test(c.to_numpy())
        lo, hi = t.conf_int()[0]
        n = int((meta["textbook"] == tb).sum())
        rows.append((tb, float(t.effect[0]), lo, hi, n, meta.loc[meta["textbook"] == tb, "school_id"].nunique()))
    means = pd.DataFrame(rows, columns=["textbook", "mean", "lo", "hi", "n_students", "n_schools"])

    pairs = []
    for i, a in enumerate(textbooks):
        for b in textbooks[i + 1:]:
            c = pd.Series(0.0, index=X.columns)
            if a != textbooks[0]:
                c[f"tb::{a}"] = -1.0
            if b != textbooks[0]:
                c[f"tb::{b}"] = 1.0
            t = res.t_test(c.to_numpy())
            lo, hi = t.conf_int()[0]
            pairs.append((a, b, float(t.effect[0]), lo, hi, not (lo <= 0 <= hi)))
    pairs = pd.DataFrame(pairs, columns=["a", "b", "diff_b_minus_a", "lo", "hi", "confirmed"])
    return means, pairs


def textbook_topic_effect(scores, meta, topic):
    """Насколько тема слабее или сильнее с каждым учебником по сравнению с остальными учебниками.

    Контроль: результат ученика по остальным темам, тип местности, язык.
    Так общий уровень ученика и общий эффект учебника не путаются с эффектом именно этой темы.
    """
    textbooks = sorted(meta["textbook"].unique())
    if len(textbooks) < 2:
        return pd.DataFrame(columns=["textbook", "effect", "lo", "hi"])
    rest = scores.drop(columns=topic).mean(axis=1)
    X = _design(meta, textbooks, extra=rest, covariates=("area", "lang"))
    res = _fit(scores[topic], X, meta)
    rows = []
    for tb in textbooks:
        c = pd.Series(0.0, index=X.columns)
        for other in textbooks:
            w = 1.0 if other == tb else -1.0 / (len(textbooks) - 1)
            if other != textbooks[0]:
                c[f"tb::{other}"] = w
        t = res.t_test(c.to_numpy())
        lo, hi = t.conf_int()[0]
        rows.append((tb, float(t.effect[0]), lo, hi))
    return pd.DataFrame(rows, columns=["textbook", "effect", "lo", "hi"])


def school_topic_effect(scores, meta, topic, shrink_k=20):
    """Отклонение школы от ожидаемого по теме. Оценки малых школ сжимаются к нулю."""
    textbooks = sorted(meta["textbook"].unique())
    rest = scores.drop(columns=topic).mean(axis=1)
    X = _design(meta, textbooks, extra=rest, covariates=("area", "lang"))
    res = _fit(scores[topic], X, meta)
    df = pd.DataFrame({"school_id": meta["school_id"], "resid": res.resid, "score": scores[topic]})
    g = df.groupby("school_id").agg(n=("resid", "size"), resid=("resid", "mean"), score=("score", "mean"))
    g["shrunk"] = g["resid"] * g["n"] / (g["n"] + shrink_k)
    return g.reset_index().sort_values("shrunk")


CAUSES = {
    "item": ("Некачественное задание",
             "Проверить задание: его одинаково часто решают сильные и слабые ученики."),
    "textbook": ("Вопрос к учебнику",
                 "Подготовить дополнительные материалы по теме для школ с этим учебником."),
    "schools": ("Отстают отдельные школы",
                "Оказать методическую поддержку учителям этих школ."),
    "topic": ("Трудна сама тема",
              "Добавить учебные часы на тему (см. раздел «Часы»)."),
}


def diagnose(topic, scores_all, scores_clean, meta, mastery_all, target, flagged_items):
    """Правила диагноза причины для темы ниже целевого уровня. Правила проверяются по порядку."""
    m_all = float(mastery_all.set_index("topic_code").loc[topic, "mastery"])
    d = {"topic_code": topic, "mastery": m_all, "cause": None, "details": ""}
    if len(meta) < MIN_GROUP:
        d.update(cause="nodata", details="Недостаточно данных для вывода.")
        return d

    # 1. Плохое задание: без него тема выше цели
    topic_flagged = [i for i in flagged_items.get(topic, [])]
    if topic_flagged and topic in scores_clean:
        m_clean = float(scores_clean[topic].mean())
        if m_clean >= target:
            d.update(cause="item", items=topic_flagged, mastery_clean=m_clean,
                     details=f"Без задания {', '.join(topic_flagged)} освоение темы {m_clean:.0%}, это выше цели.")
            return d

    sc = scores_clean if topic in scores_clean else scores_all

    # 2. Проваливают отдельные школы; без них тема выше цели
    sch = school_topic_effect(sc, meta, topic)
    weak = sch[(sch["shrunk"] <= -SCHOOL_GAP) & (sch["n"] >= 20)]
    if 0 < len(weak) <= 0.25 * len(sch):
        rest_mask = ~meta["school_id"].isin(weak["school_id"])
        m_rest = float(sc.loc[rest_mask, topic].mean())
        if m_rest >= target:
            d.update(cause="schools", schools=weak["school_id"].tolist(), mastery_rest=m_rest,
                     details=(f"В {len(weak)} школах тема усвоена намного хуже ожидаемого. "
                              f"В остальных школах освоение {m_rest:.0%}, это выше цели."))
            return d

    # 3. Один учебник заметно слабее остальных именно по этой теме
    eff = textbook_topic_effect(sc, meta, topic)
    if len(eff):
        worst = eff.sort_values("effect").iloc[0]
        if worst["effect"] <= -TEXTBOOK_GAP and worst["hi"] < 0:
            d.update(cause="textbook", textbook=worst["textbook"], effect=float(worst["effect"]),
                     details=(f"С учебником «{worst['textbook']}» тема усвоена на "
                              f"{abs(worst['effect']) * 100:.0f} п.п. хуже, чем с остальными, "
                              f"при том же общем уровне учеников."))
            return d

    # 4. Иначе трудна сама тема
    d.update(cause="topic", details="Тема усвоена ниже цели во всех учебниках и в большинстве школ.")
    return d


def confidence(row):
    if row["n_students"] < MIN_GROUP:
        return "недостаточно данных"
    half = (row["hi"] - row["lo"]) / 2
    return "высокая" if half < 0.03 else "средняя" if half < 0.06 else "низкая"


def reallocate(plan, mastery, diagnoses, target):
    """Перераспределение часов при неизменной сумме.

    Получатели: темы с диагнозом «трудна сама тема». Запрос: 1 час на каждые 5 п.п. отставания,
    не больше 20% часов темы. Доноры: темы, освоенные минимум на 10 п.п. выше цели;
    у каждой берётся не больше 20% часов. Порядок: приоритет = отставание × (1 + число тем,
    которые опираются на эту тему).
    """
    df = plan.merge(mastery[["topic_code", "mastery", "lo", "hi", "n_students"]], on="topic_code")
    df["new_hours"] = df["hours"].astype(int)
    df["reason"] = ""
    df["confidence"] = ""
    cause = {d["topic_code"]: d["cause"] for d in diagnoses}

    want = {}
    for r in df.itertuples():
        if cause.get(r.topic_code) == "topic":
            gap = max(0.0, target - r.mastery)
            req = min(int(np.floor(r.hours * MAX_SHIFT)), max(1, int(round(gap * 100 / 5))))
            want[r.topic_code] = (gap * (1 + r.prereq_count), req)

    donors = {}
    for r in df.itertuples():
        if r.topic_code not in cause and r.mastery >= target + 0.10:
            donors[r.topic_code] = [int(np.floor(r.hours * MAX_SHIFT)), r.mastery - target, r.prereq_count]

    pool = sum(v[0] for v in donors.values())
    given = {}
    for code, (_, req) in sorted(want.items(), key=lambda kv: -kv[1][0]):
        take = min(req, pool)
        given[code] = take
        pool -= take
    need = sum(given.values())

    taken = {c: 0 for c in donors}
    order = sorted(donors, key=lambda c: (donors[c][2], -donors[c][1]))   # сначала темы, на которые никто не опирается
    while need > 0 and any(taken[c] < donors[c][0] for c in order):
        for c in order:
            if need > 0 and taken[c] < donors[c][0]:
                taken[c] += 1
                need -= 1

    idx = df.set_index("topic_code")
    for code, h in given.items():
        if h:
            row = idx.loc[code]
            idx.loc[code, "new_hours"] = int(row["hours"]) + h
            idx.loc[code, "reason"] = (f"Освоение {row['mastery']:.0%} при цели {target:.0%}; "
                                       f"на тему опираются {int(row['prereq_count'])} последующих тем")
            idx.loc[code, "confidence"] = confidence(row)
    for code, h in taken.items():
        if h:
            row = idx.loc[code]
            idx.loc[code, "new_hours"] = int(row["hours"]) - h
            idx.loc[code, "reason"] = f"Тема освоена на {row['mastery']:.0%}, запас над целью"
            idx.loc[code, "confidence"] = confidence(row)
    out = idx.reset_index()
    out["delta"] = out["new_hours"] - out["hours"]
    assert out["new_hours"].sum() == out["hours"].sum()
    return out


def analyze(results, items, plan, target=0.60):
    """Полный расчёт. Возвращает словарь, из которого читают все экраны."""
    meta, wide = prepare(results)
    ist = item_stats(wide, items)
    flagged = ist.loc[ist["flagged"], "item_id"].tolist()
    flagged_by_topic = ist[ist["flagged"]].groupby("topic_code")["item_id"].apply(list).to_dict()

    scores_all = topic_scores(wide, items)
    scores_clean = topic_scores(wide, items, exclude=flagged)
    mastery = mastery_table(scores_all, meta).merge(plan[["topic_code", "topic_name"]], on="topic_code")
    weak = mastery[mastery["mastery"] < target]["topic_code"].tolist()

    diagnoses = [diagnose(t, scores_all, scores_clean, meta, mastery, target, flagged_by_topic) for t in weak]
    total = scores_clean.mean(axis=1)
    raw_means, raw_pairs = compare_textbooks(total, meta, adjusted=False)
    adj_means, adj_pairs = compare_textbooks(total, meta, adjusted=True)
    by_area = (pd.DataFrame({"total": total, "textbook": meta["textbook"], "area": meta["area"]})
               .groupby(["area", "textbook"])["total"].agg(["mean", "size"]).reset_index())
    hours = reallocate(plan, mastery, diagnoses, target)
    return dict(meta=meta, wide=wide, items=ist, scores_all=scores_all, scores_clean=scores_clean,
                mastery=mastery, weak=weak, diagnoses=diagnoses, total=total,
                raw_means=raw_means, raw_pairs=raw_pairs, adj_means=adj_means, adj_pairs=adj_pairs,
                by_area=by_area, hours=hours, target=target, plan=plan)


def build_facts(a, subject="Математика, 6 класс"):
    """Таблица фактов для записки. Языковая модель получает только её и не считает ничего сама."""
    names = a["plan"].set_index("topic_code")["topic_name"].to_dict()
    names_kk = (a["plan"].set_index("topic_code")["topic_name_kk"].to_dict()
                if "topic_name_kk" in a["plan"] else names)
    m = a["mastery"].set_index("topic_code")
    facts = {
        "subject": subject,
        "n_students": int(len(a["meta"])),
        "n_schools": int(a["meta"]["school_id"].nunique()),
        "target_pct": int(round(a["target"] * 100)),
        "weak_topics": [],
        "textbooks_adjusted": [],
        "textbook_pairs": [],
        "hours": [],
        "total_hours": int(a["plan"]["hours"].sum()),
    }
    for d in a["diagnoses"]:
        r = m.loc[d["topic_code"]]
        item = {
            "topic": names[d["topic_code"]],
            "topic_kk": names_kk[d["topic_code"]],
            "mastery_pct": int(round(r["mastery"] * 100)),
            "ci_low_pct": int(round(r["lo"] * 100)),
            "ci_high_pct": int(round(r["hi"] * 100)),
            "cause": d["cause"],
            "cause_title": CAUSES.get(d["cause"], ("Недостаточно данных", ""))[0],
            "action": CAUSES.get(d["cause"], ("", "Собрать больше данных."))[1],
        }
        if d["cause"] == "textbook":
            item["textbook"] = d["textbook"]
            item["gap_pp"] = int(round(abs(d["effect"]) * 100))
        if d["cause"] == "schools":
            item["schools_count"] = len(d["schools"])
        facts["weak_topics"].append(item)
    for r in a["adj_means"].itertuples():
        facts["textbooks_adjusted"].append({"textbook": r.textbook, "mean_pct": int(round(r.mean * 100)),
                                            "ci_low_pct": int(round(r.lo * 100)),
                                            "ci_high_pct": int(round(r.hi * 100))})
    for r in a["adj_pairs"].itertuples():
        facts["textbook_pairs"].append({"a": r.a, "b": r.b, "diff_pp": round(abs(r.diff_b_minus_a) * 100, 1),
                                        "better": r.b if r.diff_b_minus_a > 0 else r.a,
                                        "confirmed": bool(r.confirmed)})
    for r in a["hours"].itertuples():
        if r.delta != 0:
            facts["hours"].append({"topic": r.topic_name, "topic_kk": names_kk[r.topic_code], "old": int(r.hours), "new": int(r.new_hours),
                                   "delta": int(abs(r.delta)), "direction": "добавить" if r.delta > 0 else "сократить"})
    return facts


NUM_RE = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?(?![\w])")


def _numbers(text):
    return [float(x.replace(",", ".")) for x in NUM_RE.findall(text)]


def check_numbers(memo, facts):
    """Сверяет каждое число в тексте записки с таблицей фактов. Возвращает список чисел, которых в фактах нет."""
    allowed = set()

    def walk(v):
        if isinstance(v, bool):
            return
        if isinstance(v, (int, float)):
            allowed.add(round(float(v), 1))
        elif isinstance(v, str):
            allowed.update(round(x, 1) for x in _numbers(v))
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(facts)
    found = _numbers(memo)
    bad = sorted({x for x in found if round(x, 1) not in allowed})
    return len(found), bad
