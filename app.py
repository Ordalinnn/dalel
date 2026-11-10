import io
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
import llm
import tagger

st.set_page_config(page_title="Дәлел — аналитика учебных программ", page_icon="📐", layout="wide",
                   initial_sidebar_state="expanded")

DATA = Path(__file__).parent / "data"
ACCENT = "#1F5FAE"
GREY = "#9AA3AE"
RED = "#B9473F"
GREEN = "#2E7D5B"

st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 2rem; max-width: 1150px;}
h1, h2, h3 {letter-spacing: -0.01em;}
.kpi {border: 1px solid rgba(128,128,128,.25); border-radius: 10px; padding: 14px 16px;}
.kpi .v {font-size: 1.9rem; font-weight: 650; line-height: 1.1;}
.kpi .l {font-size: .85rem; opacity: .7;}
.card {border: 1px solid rgba(128,128,128,.25); border-radius: 12px; padding: 18px 20px; height: 100%;}
.card h4 {margin: 0 0 .4rem 0;}
.cause {display:inline-block; padding: 3px 10px; border-radius: 999px; font-size:.85rem; font-weight:600;
        background: rgba(31,95,174,.12); color: #1F5FAE;}
.note {font-size: .85rem; opacity: .7;}
.synth {font-size:.8rem; padding: 2px 8px; border-radius: 6px; background: rgba(185,71,63,.12); color:#B9473F;}
</style>
""", unsafe_allow_html=True)


# ---------- данные ----------

@st.cache_data(show_spinner=False)
def load_demo():
    return (pd.read_csv(DATA / "results.csv"), pd.read_csv(DATA / "items.csv"), pd.read_csv(DATA / "plan.csv"))


@st.cache_resource(show_spinner="Обучаю модель разметки…")
def get_tagger():
    return tagger.train()


@st.cache_data(show_spinner=False)
def load_train():
    return pd.read_csv(DATA / "train_items.csv")


@st.cache_data(show_spinner=False)
def tagger_quality():
    return tagger.evaluate(get_tagger())


@st.cache_data(show_spinner="Считаю…")
def run_analysis(results, items, plan, target):
    return core.analyze(results, items, plan, target)


def pct(x):
    return f"{x * 100:.0f}%"


def kpi(col, value, label):
    col.markdown(f'<div class="kpi"><div class="v">{value}</div><div class="l">{label}</div></div>',
                 unsafe_allow_html=True)


if "data" not in st.session_state:
    st.session_state.data = None
    st.session_state.synthetic = False
if "page" not in st.session_state:
    st.session_state.page = "Главная"
if "nav_to" in st.session_state:          # переход по кнопке: меняем выбор меню до его отрисовки
    st.session_state.page = st.session_state.pop("nav_to")

PAGES = ["Главная", "Обзор тем", "Учебники", "Тема", "Часы", "ИИ-разметка", "Записка"]

with st.sidebar:
    st.markdown("### Дәлел")
    st.caption("Учебник выбирают доказательства, а не мнения")
    page = st.radio("Раздел", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    target = st.slider("Целевой уровень освоения темы", 0.50, 0.80, 0.60, 0.01, format="%.2f")
    if st.session_state.data is not None and st.session_state.synthetic:
        st.markdown('<span class="synth">Демо-данные синтетические</span>', unsafe_allow_html=True)
    p = llm.provider()
    st.caption("ИИ: " + (f"языковая модель через API ({p})" if p else
                         "собственная модель разметки, записка по шаблону (без ключа API)"))


def go_to(name):
    st.session_state.nav_to = name
    st.rerun()


# ---------- главная ----------

if page == "Главная":
    st.markdown("## Оқулықты пікір емес, дәлел таңдайды")
    st.markdown("#### Учебник выбирают доказательства, а не мнения")
    st.write("«Дәлел» превращает выгрузку результатов теста в три ответа для методиста: "
             "что провалено, почему и что изменить. Числа считает проверяемый код, "
             "ИИ размечает задания по темам и пишет записку для методсовета.")
    c1, c2, c3 = st.columns(3)
    for c, t, d in ((c1, "Что провалено", "Освоение каждой темы с интервалом и разрезами город/село, язык обучения."),
                    (c2, "Почему", "Диагноз причины: трудна тема, подводит учебник, отстают школы или плохое задание."),
                    (c3, "Что изменить", "Честное сравнение учебников и перераспределение часов при той же сумме.")):
        c.markdown(f'<div class="card"><h4>{t}</h4>{d}</div>', unsafe_allow_html=True)
    st.write("")
    b1, b2 = st.columns([1, 2])
    if b1.button("Открыть демо", type="primary", use_container_width=True):
        st.session_state.data = load_demo()
        st.session_state.synthetic = True
        go_to("Обзор тем")
    with b2.expander("Загрузить свои данные (3 файла CSV)"):
        st.markdown(
            "- **results.csv**: student_id, school_id, textbook, lang, area, prior_score, item_id, correct (0/1)\n"
            "- **items.csv**: item_id, item_text, topic_code\n"
            "- **plan.csv**: topic_code, topic_name, hours, prereq_count\n\n"
            "Имена учеников не нужны: используйте обезличенные ключи.")
        fr = st.file_uploader("results.csv", type="csv", key="fr")
        fi = st.file_uploader("items.csv", type="csv", key="fi")
        fp = st.file_uploader("plan.csv", type="csv", key="fp")
        if fr and fi and fp and st.button("Проверить и загрузить"):
            r, i, pl = pd.read_csv(fr), pd.read_csv(fi), pd.read_csv(fp)
            errs = core.validate(r, i, pl)
            if errs:
                for e in errs:
                    st.error(e)
            else:
                st.session_state.data = (r, i, pl)
                st.session_state.synthetic = False
                go_to("Обзор тем")
    st.stop()

if st.session_state.data is None:
    st.info("Сначала откройте демо или загрузите данные на главной странице.")
    if st.button("Открыть демо", type="primary"):
        st.session_state.data = load_demo()
        st.session_state.synthetic = True
        st.rerun()
    st.stop()

results, items, plan = st.session_state.data
A = run_analysis(results, items, plan, target)
meta = A["meta"]
names = plan.set_index("topic_code")["topic_name"].to_dict()
diag = {d["topic_code"]: d for d in A["diagnoses"]}


# ---------- обзор тем ----------

if page == "Обзор тем":
    st.markdown("## Что провалено")
    c = st.columns(4)
    kpi(c[0], f"{len(meta):,}".replace(",", " "), "учеников")
    kpi(c[1], meta["school_id"].nunique(), "школ")
    kpi(c[2], len(plan), "тем в программе")
    kpi(c[3], len(A["weak"]), f"тем ниже цели {pct(target)}")
    st.write("")

    f1, f2 = st.columns(2)
    area = f1.selectbox("Тип местности", ["все", *sorted(meta["area"].unique())])
    lang = f2.selectbox("Язык обучения", ["все", *sorted(meta["lang"].unique())])
    mask = pd.Series(True, index=meta.index)
    if area != "все":
        mask &= meta["area"] == area
    if lang != "все":
        mask &= meta["lang"] == lang
    sub_meta = meta[mask]
    if len(sub_meta) < core.MIN_GROUP:
        st.warning(f"В выбранной группе {len(sub_meta)} учеников. Недостаточно данных для вывода.")
        st.stop()
    m = core.mastery_table(A["scores_all"][mask], sub_meta).merge(plan[["topic_code", "topic_name"]], on="topic_code")
    m = m.sort_values("mastery")
    colors = [RED if v < target else GREY for v in m["mastery"]]
    fig = go.Figure(go.Bar(
        x=m["mastery"], y=m["topic_name"], orientation="h", marker_color=colors,
        error_x=dict(type="data", symmetric=False, array=m["hi"] - m["mastery"], arrayminus=m["mastery"] - m["lo"],
                     color="rgba(60,60,60,.6)", thickness=1.2, width=4),
        text=[pct(v) for v in m["mastery"]], textposition="inside", insidetextanchor="start",
        textfont=dict(color="white"),
        hovertemplate="%{y}: %{x:.0%}<extra></extra>"))
    fig.add_vline(x=target, line_dash="dash", line_color=ACCENT,
                  annotation_text=f"цель {pct(target)}", annotation_position="top")
    fig.update_layout(height=430, margin=dict(l=10, r=20, t=30, b=10), xaxis=dict(range=[0, 1], tickformat=".0%"),
                      showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f'<div class="note">Доля верных ответов по теме, линии — 95% интервал (бутстреп по школам). '
                f'В расчёте {len(sub_meta)} учеников, {sub_meta["school_id"].nunique()} школ.</div>',
                unsafe_allow_html=True)

    st.markdown("#### Темы ниже цели")
    for d in A["diagnoses"]:
        cc = st.columns([3, 2, 1])
        cc[0].markdown(f"**{names[d['topic_code']]}** — {pct(d['mastery'])}")
        cc[1].markdown(f'<span class="cause">{core.CAUSES.get(d["cause"], ("Недостаточно данных",))[0]}</span>',
                       unsafe_allow_html=True)
        if cc[2].button("Открыть", key=f"open_{d['topic_code']}"):
            st.session_state.topic = d["topic_code"]
            go_to("Тема")

    flagged = A["items"][A["items"]["flagged"]]
    if len(flagged):
        with st.expander(f"Задания с низкой различающей способностью: {len(flagged)}"):
            st.dataframe(flagged[["item_id", "topic_code", "item_text", "p_correct", "discrimination"]]
                         .rename(columns={"item_id": "Задание", "topic_code": "Тема", "item_text": "Текст",
                                          "p_correct": "Доля верных", "discrimination": "Различающая способность"}),
                         hide_index=True, use_container_width=True)


# ---------- учебники ----------

elif page == "Учебники":
    st.markdown("## Какой учебник работает лучше")
    mode = st.radio("Режим сравнения", ["Сырые средние", "С поправками"], horizontal=True)
    adj = mode == "С поправками"
    means = A["adj_means"] if adj else A["raw_means"]
    pairs = A["adj_pairs"] if adj else A["raw_pairs"]
    best = means.sort_values("mean").iloc[-1]["textbook"]

    fig = go.Figure()
    for r in means.itertuples():
        c = ACCENT if r.textbook == best else GREY
        fig.add_trace(go.Scatter(
            x=[r.mean], y=[r.textbook], mode="markers+text", marker=dict(size=16, color=c),
            error_x=dict(type="data", symmetric=False, array=[r.hi - r.mean], arrayminus=[r.mean - r.lo],
                         color=c, thickness=2, width=8),
            text=[pct(r.mean)], textposition="top center", cliponaxis=False,
            hovertemplate=f"{r.textbook}: %{{x:.1%}}<br>учеников {r.n_students}, школ {r.n_schools}<extra></extra>"))
    lo = min(means["lo"].min(), 0.55)
    hi = max(means["hi"].max(), 0.80)
    fig.update_layout(height=300, showlegend=False, margin=dict(l=10, r=20, t=40, b=10),
                      xaxis=dict(range=[lo - 0.02, hi + 0.02], tickformat=".0%", title="средний результат теста"),
                      yaxis=dict(autorange="reversed", range=None), )
    fig.update_yaxes(range=[len(means) - 0.4, -0.7])
    st.plotly_chart(fig, use_container_width=True)

    if adj:
        st.success(f"С поправкой на прошлый балл, тип местности и язык обучения лучший результат у «{best}».")
        st.markdown('<div class="note">Учебники сравниваются на одном и том же «среднем» ученике. '
                    'Интервалы учитывают, что ученики одной школы похожи друг на друга.</div>', unsafe_allow_html=True)
    else:
        st.warning(f"По сырым средним лучший — «{best}». Но учебники выбирают школы с разным составом учеников.")

    rows = []
    for r in pairs.itertuples():
        better = r.b if r.diff_b_minus_a > 0 else r.a
        lo_, hi_ = (r.lo, r.hi) if r.diff_b_minus_a > 0 else (-r.hi, -r.lo)
        rows.append({"Пара": f"{r.a} — {r.b}", "Разница": f"{abs(r.diff_b_minus_a) * 100:.1f} п.п. в пользу «{better}»",
                     "95% интервал разницы": f"{lo_ * 100:+.1f} … {hi_ * 100:+.1f} п.п.",
                     "Вывод": "подтверждено" if r.confirmed else "различие не подтверждено"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.markdown("#### Почему ответы расходятся")
    ba = A["by_area"]
    fig2 = go.Figure()
    for tb in sorted(ba["textbook"].unique()):
        d = ba[ba["textbook"] == tb]
        fig2.add_trace(go.Bar(name=tb, x=d["area"], y=d["mean"], text=[pct(v) for v in d["mean"]],
                              customdata=d["size"], hovertemplate=f"{tb}, %{{x}}: %{{y:.0%}}, учеников %{{customdata}}<extra></extra>"))
    fig2.update_layout(barmode="group", height=320, margin=dict(l=10, r=10, t=10, b=10),
                       yaxis=dict(tickformat=".0%", range=[0, 1]),
                       colorway=["#7C8A99", ACCENT, "#B9C3CE"], legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig2, use_container_width=True)
    share = meta.groupby("textbook")["area"].apply(lambda s: (s == "город").mean())
    st.write("Доля городских учеников: " + ", ".join(f"«{k}» {pct(v)}" for k, v in share.items()) +
             ". Внутри города и внутри села порядок учебников один, а в общем среднем он переворачивается: "
             "учебник с городскими школами выигрывает за счёт состава учеников (парадокс Симпсона).")


# ---------- тема ----------

elif page == "Тема":
    codes = list(plan["topic_code"])
    default = st.session_state.get("topic", A["weak"][0] if A["weak"] else codes[0])
    code = st.selectbox("Тема", codes, index=codes.index(default), format_func=lambda c: f"{c} · {names[c]}")
    st.session_state.topic = code
    mrow = A["mastery"].set_index("topic_code").loc[code]
    st.markdown(f"## {names[code]}")
    c = st.columns(3)
    kpi(c[0], pct(mrow["mastery"]), "освоение темы")
    kpi(c[1], f"{pct(mrow['lo'])}–{pct(mrow['hi'])}", "95% интервал")
    kpi(c[2], pct(target), "цель")
    st.write("")

    if code in diag:
        d = diag[code]
        title, action = core.CAUSES.get(d["cause"], ("Недостаточно данных", "Собрать больше данных."))
        st.markdown(f'<span class="cause">{title}</span>', unsafe_allow_html=True)
        st.markdown(f"**Почему:** {d['details']}")
        st.markdown(f"**Что делать:** {action}")
    else:
        st.success("Тема освоена на уровне цели или выше.")

    sc = A["scores_clean"] if code in A["scores_clean"] else A["scores_all"]
    t1, t2 = st.columns(2)
    with t1:
        st.markdown("##### По учебникам, с поправкой на общий уровень")
        eff = core.textbook_topic_effect(sc, meta, code)
        fig = go.Figure(go.Bar(x=eff["effect"] * 100, y=eff["textbook"], orientation="h",
                               marker_color=[RED if (e <= -core.TEXTBOOK_GAP and h < 0) else GREY
                                             for e, h in zip(eff["effect"], eff["hi"])],
                               error_x=dict(type="data", symmetric=False, array=(eff["hi"] - eff["effect"]) * 100,
                                            arrayminus=(eff["effect"] - eff["lo"]) * 100, color="rgba(60,60,60,.6)"),
                               hovertemplate="%{y}: %{x:+.1f} п.п.<extra></extra>"))
        fig.add_vline(x=0, line_color="rgba(120,120,120,.8)")
        fig.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10),
                          xaxis_title="п.п. относительно остальных учебников")
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        st.markdown("##### Школы ниже ожидаемого")
        sch = core.school_topic_effect(sc, meta, code)
        sch = sch.assign(**{"Отклонение, п.п.": (sch["shrunk"] * 100).round(1), "Освоение": (sch["score"] * 100).round(0)})
        sch["Статус"] = [("мало учеников" if n < 20 else "ниже ожидаемого" if s <= -core.SCHOOL_GAP else "")
                         for n, s in zip(sch["n"], sch["shrunk"])]
        st.dataframe(sch[["school_id", "n", "Освоение", "Отклонение, п.п.", "Статус"]].head(10)
                     .rename(columns={"school_id": "Школа", "n": "Учеников"}),
                     hide_index=True, use_container_width=True, height=230)

    st.markdown("##### Задания темы")
    ti = A["items"][A["items"]["topic_code"] == code].copy()
    ti["Статус"] = ["проверить задание" if f else "" for f in ti["flagged"]]
    ti["Доля верных"] = (ti["p_correct"] * 100).round(0)
    ti["Различающая способность"] = ti["discrimination"].round(2)
    st.dataframe(ti[["item_id", "item_text", "Доля верных", "Различающая способность", "Статус"]]
                 .rename(columns={"item_id": "Задание", "item_text": "Текст"}),
                 hide_index=True, use_container_width=True)
    st.markdown('<div class="note">Различающая способность ниже 0,10 значит, что задание одинаково часто решают '
                'сильные и слабые ученики: проблема в задании, а не в теме.</div>', unsafe_allow_html=True)


# ---------- часы ----------

elif page == "Часы":
    st.markdown("## Перераспределение часов")
    h = A["hours"].copy()
    total = int(h["hours"].sum())
    st.write(f"Сумма часов не меняется: **{total} ч**. Часы получают темы с диагнозом «трудна сама тема», "
             "отдают темы с запасом над целью не меньше 10 п.п. Изменение темы не больше 20% её часов.")
    view = h.assign(**{
        "Тема": h["topic_name"], "Освоение": (h["mastery"] * 100).round(0).astype(int).astype(str) + "%",
        "Было, ч": h["hours"], "Предлагается, ч": h["new_hours"],
        "Изменение": [f"{d:+d}" if d else "" for d in h["delta"]],
        "Причина": h["reason"], "Уверенность": h["confidence"]})
    view = view[["Тема", "Освоение", "Было, ч", "Предлагается, ч", "Изменение", "Причина", "Уверенность"]]

    def color(v):
        if isinstance(v, str) and v.startswith("+"):
            return f"color: {GREEN}; font-weight: 600"
        if isinstance(v, str) and v.startswith("-"):
            return f"color: {RED}; font-weight: 600"
        return ""

    st.dataframe(view.style.map(color, subset=["Изменение"]), hide_index=True, use_container_width=True,
                 column_config={"Причина": st.column_config.TextColumn(width="large")})
    st.markdown(f"**Итого:** было {total} ч, предлагается {int(h['new_hours'].sum())} ч.")
    st.info("Это гипотеза для пилота, а не доказанный эффект: на данных одного года влияние часа на результат "
            "измерить нельзя. Темы с причиной «учебник», «школы» или «задание» часов не получают: им нужны другие меры.")


# ---------- ИИ-разметка ----------

elif page == "ИИ-разметка":
    st.markdown("## ИИ-разметка заданий по темам программы")
    st.write("Результаты теста приходят по номерам заданий, а не по темам. Модель относит каждое задание "
             "к одной теме из закрытого списка и сообщает уверенность. Задания с низкой уверенностью "
             "уходят методисту на подтверждение.")
    use_api = bool(llm.provider())
    model = get_tagger()
    acc, test_df = tagger_quality()
    engine = "языковая модель через API" if use_api else "собственная модель, работает без ключа API и без интернета"
    st.caption(f"Сейчас работает: {engine}.")

    examples = test_df["text"].tolist()
    choice = st.selectbox("Пример задания (модель не видела его при обучении)", ["— свой текст —", *examples])
    text = st.text_area("Текст задания на русском или казахском", value="" if choice.startswith("—") else choice,
                        height=110)
    if st.button("Разметить", type="primary", disabled=not text.strip()):
        res, threshold = None, tagger.REVIEW_BELOW
        if use_api:
            try:
                with st.spinner("Языковая модель размечает задание…"):
                    res, threshold = llm.tag_item(text, plan), 0.7
            except Exception as e:
                st.warning(f"API недоступен ({type(e).__name__}), разметку сделала собственная модель.")
        if res is None:
            res = tagger.predict(model, text, plan)
        c = st.columns(3)
        name = names.get(res["topic_code"], "не подходит ни к одной теме")
        kpi(c[0], res["topic_code"], name)
        kpi(c[1], f"{res['confidence']:.2f}", "уверенность")
        kpi(c[2], "на проверку" if res["confidence"] < threshold else "принято", "статус")
        st.markdown(f"**Обоснование:** {res['reason']}")
        if res.get("alternatives"):
            st.markdown("**Другие варианты:** " + "; ".join(f"{n} ({p:.2f})" for _, n, p in res["alternatives"]))
        st.caption(f"Источник: {res['source']}. Порог проверки: {threshold:.2f}.")

    with st.expander(f"Как устроена собственная модель и насколько она точна: {acc:.0%} на отложенных заданиях"):
        st.markdown(
            f"- Признаки: буквенные n-граммы длиной 2–5 символов (TF-IDF). Они ловят корни и окончания "
            f"слов и одинаково работают для казахского и русского.\n"
            f"- Классификатор: логистическая регрессия, обучена на {len(load_train())} заданиях.\n"
            f"- Проверка: {len(test_df)} заданий, которых модель при обучении не видела. "
            f"Верно: {int(test_df['ok'].sum())} из {len(test_df)}.\n"
            f"- Ошибки модели обычно идут с низкой уверенностью, поэтому такие задания отправляются на проверку.\n"
            f"- Выборка проверки маленькая: на реальных заданиях точность нужно измерить заново.")
        view = test_df.assign(**{"Верно": test_df["ok"].map({True: "да", False: "нет"}),
                                 "Уверенность": test_df["confidence"].round(2)})
        st.dataframe(view[["text", "lang", "topic_code", "pred", "Уверенность", "Верно"]]
                     .rename(columns={"text": "Задание", "lang": "Язык", "topic_code": "Правильная тема",
                                      "pred": "Ответ модели"}),
                     hide_index=True, use_container_width=True)
    with st.expander("Закрытый список тем"):
        st.dataframe(plan[["topic_code", "topic_name"]], hide_index=True, use_container_width=True)


# ---------- записка ----------

elif page == "Записка":
    st.markdown("## Записка для методического совета")
    facts = core.build_facts(A)
    lang = st.radio("Язык", ["русский", "казахский"], horizontal=True)
    lcode = "ru" if lang == "русский" else "kk"
    if st.button("Сформировать записку", type="primary"):
        memo, source = None, "шаблон по таблице фактов (без API)"
        if llm.provider():
            try:
                with st.spinner("Модель пишет записку по таблице фактов…"):
                    memo, source = llm.write_memo(facts, lcode), "модель"
            except Exception as e:
                st.warning(f"Модель недоступна ({type(e).__name__}), записка собрана по шаблону.")
        if memo is None:
            memo = llm.template_memo(facts, lcode)
        st.session_state.memo = (memo, source, lcode)

    if "memo" in st.session_state:
        memo, source, lc = st.session_state.memo
        st.markdown(memo.replace("\n", "  \n"))
        n, bad = core.check_numbers(memo, facts)
        if bad:
            st.error(f"Проверка чисел: {len(bad)} из {n} чисел нет в расчёте: {', '.join(map(str, bad))}. "
                     "Записку нужно исправить.")
        else:
            st.success(f"Проверка чисел: все {n} чисел совпадают с расчётом.")
        st.caption(f"Источник текста: {source}")

        try:
            from docx import Document
            doc = Document()
            doc.add_heading("Записка для методического совета", 1)
            for line in memo.split("\n"):
                if line.strip():
                    doc.add_paragraph(line)
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("Скачать в Word", buf.getvalue(), file_name="zapiska_dalel.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except ImportError:
            pass

    with st.expander("Таблица фактов, которую получает модель"):
        st.json(facts)
