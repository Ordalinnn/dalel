import io
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

import core
import library
import llm
import tagger

st.set_page_config(page_title="Дәлел — аналитика учебных программ", page_icon="✒️", layout="wide",
                   initial_sidebar_state="auto")

DATA = Path(__file__).parent / "data"
INK = "#1D3A8A"        # синяя паста
RED = "#C62828"        # красная ручка учителя
PENCIL = "#8A93A3"     # карандаш: нейтральные данные
GRAPHITE = "#2B3140"   # основной текст
GRID = "#E4EBF5"       # клетка тетради
GREEN = "#2E7D5B"
ACCENT, GREY = INK, PENCIL

FONTS_CSS = (Path(__file__).parent / "static" / "fonts.css").read_text(encoding="utf-8")

pio.templates["dalel"] = go.layout.Template(layout=go.Layout(
    font=dict(family="Golos Text, sans-serif", color=GRAPHITE, size=13),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=PENCIL)),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=GRAPHITE)),
    hoverlabel=dict(font=dict(family="Golos Text, sans-serif")),
    colorway=[INK, PENCIL, "#B8C2D6"],
))
pio.templates.default = "plotly_white+dalel"

st.markdown(f"""
<style>
{FONTS_CSS}
html, body, .stApp, .stMarkdown, p, li, label, input, textarea, button, [data-testid="stWidgetLabel"] {{
  font-family: 'Golos Text', sans-serif;
}}
#MainMenu, footer {{visibility: hidden;}}
.block-container {{padding-top: 2.2rem; max-width: 1120px;}}
h1, h2, h3, h4 {{font-family: 'Unbounded', sans-serif !important; color: {INK}; letter-spacing: -0.01em;}}
h2 {{font-size: 1.7rem !important; font-weight: 700 !important; line-height: 1.2 !important;}}
h3, h4, h5 {{font-weight: 500 !important;}}
p, li {{max-width: 75ch; line-height: 1.6;}}

/* боковая панель: поля тетради */
section[data-testid="stSidebar"] {{background: #FFFFFF; border-right: 2px solid #F2C4C4;}}
.brand {{font-family: 'Unbounded', sans-serif; font-weight: 700; font-size: 1.6rem; color: {INK}; margin: 0;}}
.brand-sub {{color: {PENCIL}; font-size: .88rem; margin: .2rem 0 1.2rem 0; line-height: 1.4;}}
section[data-testid="stSidebar"] div[role="radiogroup"] {{gap: 0;}}
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
  padding: .45rem .7rem; margin: 0; border-left: 3px solid transparent; border-radius: 0; width: 100%;
}}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div:first-child:not([data-testid]) {{display: none;}}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] {{
  border-left-color: {INK}; background: #EEF2FA;
}}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] p {{color: {INK}; font-weight: 600;}}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover p {{color: {INK};}}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"]:has(input:focus-visible) {{outline: 2px solid {INK}; outline-offset: -2px;}}

/* показатели */
.kpi {{border-left: 2px solid {GRID}; padding: .2rem 0 .2rem 1rem;}}
.kpi .v {{font-family: 'Unbounded', sans-serif; font-size: 1.9rem; font-weight: 500; color: {INK}; line-height: 1.15;}}
.kpi .l {{font-size: .88rem; color: {PENCIL}; margin-top: .2rem;}}

.cause {{display:inline-block; padding: 2px 10px; border: 1.5px solid {RED}; border-radius: 4px;
         font-size:.85rem; font-weight:600; color: {RED}; background: #FFFFFF;}}
.note {{font-size: .86rem; color: {PENCIL};}}
.lead {{font-size: 1.05rem; color: {PENCIL}; margin: -.3rem 0 1.4rem 0; max-width: 70ch;}}
.st-key-weaklist [data-testid="stHorizontalBlock"] {{border-bottom: 1px solid {GRID}; padding: .35rem 0;}}
.st-key-weaklist {{border-top: 1px solid {GRID}; gap: 0 !important;}}
.st-key-weaklist p {{margin: 0;}}
.diag {{border-left: 3px solid {RED}; background: #FDF6F6; padding: .9rem 1.1rem; margin: .2rem 0 1.4rem 0;}}
.diag .drow {{display: grid; grid-template-columns: 8.5rem 1fr; gap: .8rem; margin-top: .55rem; line-height: 1.5;}}
.diag .dk {{color: {PENCIL};}}
.book {{padding: .45rem 0; border-bottom: 1px solid {GRID}; line-height: 1.5;}}
.book .why {{color: {PENCIL}; font-size: .92rem;}}
h5 {{font-size: 1rem !important; color: {GRAPHITE} !important; margin-top: .6rem;}}
[data-testid="stSegmentedControl"] button {{font-size: .95rem;}}
@media (max-width: 700px) {{ .diag .drow {{grid-template-columns: 1fr; gap: .1rem;}} }}
.verdict {{border-left: 3px solid {INK}; padding: .7rem 1rem; margin: .4rem 0 1rem 0; background: #F3F6FB; color: {GRAPHITE};}}
.verdict.wrong {{border-left-color: {RED}; background: #FDF3F3;}}
.verdict .pen {{font-family: 'Caveat', cursive; font-size: 1.35rem; color: {RED}; margin-left: .5rem; white-space: nowrap; line-height: 1;}}
.synth {{font-size:.82rem; color:{RED}; border-bottom: 1.5px solid {RED};}}
.side-note {{font-size: .82rem; color: {PENCIL}; line-height: 1.45;}}

/* главная: лист в клетку */
.hero {{
  position: relative; padding: 2.4rem 2rem 2.2rem 3.2rem; margin-bottom: 1.6rem;
  background-color: #FFFFFF;
  background-image: linear-gradient({GRID} 1px, transparent 1px), linear-gradient(90deg, {GRID} 1px, transparent 1px);
  background-size: 22px 22px; border: 1px solid {GRID};
}}
.hero::before {{content: ""; position: absolute; top: 0; bottom: 0; left: 2rem; width: 2px; background: #F2A6A6;}}
.hero h1 {{font-size: clamp(1.7rem, 4vw, 2.9rem) !important; font-weight: 700 !important; line-height: 1.12 !important;
          margin: 0 0 .7rem 0; padding: 0; max-width: 16ch;}}
.hero .sub {{font-size: 1.12rem; color: {GRAPHITE}; max-width: 54ch; margin: 0 0 2rem 0; line-height: 1.55;}}
.flip {{background: rgba(255,255,255,.92); display: inline-block; padding: 1.1rem 1.4rem 1.2rem 1.4rem;
        border: 1px solid {GRID}; max-width: 100%;}}
.flip .q {{font-weight: 600; color: {GRAPHITE}; margin-bottom: .9rem;}}
.flip .row {{display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap; padding: .35rem 0;}}
.flip .lbl {{width: 15rem; color: {PENCIL}; font-size: .95rem;}}
.flip .ans {{font-family: 'Unbounded', sans-serif; font-size: 1.25rem; color: {INK};}}
.flip .wrong {{text-decoration: line-through; text-decoration-color: {RED}; text-decoration-thickness: 2.5px; color: {PENCIL};}}
.flip .pen {{font-family: 'Caveat', cursive; font-size: 1.45rem; color: {RED}; line-height: 1;}}
.flip .src {{font-size: .82rem; color: {PENCIL}; margin-top: .7rem;}}

/* три вопроса: строки тетради, не карточки */
.ruled {{border-top: 1px solid {GRID}; margin: .4rem 0 1.4rem 0;}}
.ruled .r {{display: grid; grid-template-columns: 13rem 1fr; gap: 1.2rem; padding: .9rem 0; border-bottom: 1px solid {GRID};}}
.ruled .t {{font-family: 'Unbounded', sans-serif; font-weight: 500; color: {INK}; font-size: 1rem;}}
.ruled .d {{color: {GRAPHITE}; max-width: 62ch;}}

@media (max-width: 700px) {{
  .hero {{padding: 1.6rem 1rem 1.6rem 2rem;}}
  .hero::before {{left: 1.1rem;}}
  .flip .lbl {{width: auto;}}
  .ruled .r {{grid-template-columns: 1fr; gap: .3rem;}}
}}
@media (prefers-reduced-motion: reduce) {{ * {{transition: none !important; animation: none !important;}} }}
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


PLOT_CFG = {"displayModeBar": False, "responsive": True}
TB_COLORS = ["#5B6475", INK, "#8FA3D1", "#B07A3E", "#6E9E86"]   # постоянный цвет каждого учебника


def tb_color(tb, all_tbs):
    return TB_COLORS[sorted(all_tbs).index(tb) % len(TB_COLORS)]


def chart(fig, height):
    fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)


def lead(text):
    st.markdown(f'<p class="lead">{text}</p>', unsafe_allow_html=True)


def books_html(books, lang="ru"):
    return "".join(f'<div class="book"><b>{library.title_line(b)}</b><br>'
                   f'<span class="why">{b["why_kk"] if lang == "kk" else b["why_ru"]}</span></div>'
                   for b in books)


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

PAGES = ["Главная", "Обзор тем", "Учебники", "Тема", "Часы", "ИИ-разметка", "Записка", "Библиотека"]

with st.sidebar:
    st.markdown('<p class="brand">Дәлел</p><p class="brand-sub">Учебник выбирают доказательства, а не мнения</p>',
                unsafe_allow_html=True)
    page = st.radio("Раздел", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    target = st.slider("Целевой уровень освоения темы", 0.50, 0.80, 0.60, 0.01, format="%.2f")
    if st.session_state.data is not None and st.session_state.synthetic:
        st.markdown('<span class="synth">Демо-данные синтетические</span>', unsafe_allow_html=True)
    p = llm.provider()
    st.markdown('<p class="side-note">' + ("ИИ: языковая модель через API" if p else
                "ИИ: собственная модель разметки, записка по шаблону. Работает без ключа API.") + "</p>",
                unsafe_allow_html=True)


def go_to(name):
    st.session_state.nav_to = name
    st.rerun()


# ---------- главная ----------

if page == "Главная":
    demo = run_analysis(*load_demo(), 0.60)
    raw = demo["raw_means"].sort_values("mean", ascending=False).iloc[0]
    adj = demo["adj_means"].sort_values("mean", ascending=False).iloc[0]
    adj_of_raw = demo["adj_means"].set_index("textbook").loc[raw["textbook"], "mean"]
    n_txt = f"{len(demo['meta']):,}".replace(",", " ")
    st.markdown(f"""
<div class="hero">
  <h1>Оқулықты пікір емес, дәлел таңдайды</h1>
  <p class="sub">Учебник выбирают доказательства, а не мнения. «Дәлел» берёт результаты теста и показывает
  методисту, какие темы провалены, почему и что изменить.</p>
  <div class="flip">
    <div class="q">Какой учебник даёт лучший результат?</div>
    <div class="row"><span class="lbl">По средним баллам</span>
      <span class="ans wrong">{raw['textbook']}, {pct(raw['mean'])}</span>
      <span class="pen">его чаще берут городские школы</span></div>
    <div class="row"><span class="lbl">С поправкой на состав школ</span>
      <span class="ans">{adj['textbook']}, {pct(adj['mean'])}</span>
      <span class="pen">а у «{raw['textbook']}» {pct(adj_of_raw)}</span></div>
    <div class="src">Синтетические демо-данные: {n_txt} учеников, {demo['meta']['school_id'].nunique()} школ,
    математика 6 класса.</div>
  </div>
</div>
""", unsafe_allow_html=True)
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
    st.markdown("""
<div class="ruled">
  <div class="r"><div class="t">Что провалено</div>
    <div class="d">Освоение каждой темы с 95% интервалом. Можно сравнить город и село, казахский и русский язык обучения.</div></div>
  <div class="r"><div class="t">Почему</div>
    <div class="d">Для каждой слабой темы система называет причину: трудна сама тема, подводит учебник,
    отстают отдельные школы или в тесте плохое задание.</div></div>
  <div class="r"><div class="t">Что изменить</div>
    <div class="d">Честное сравнение учебников, перераспределение часов при той же сумме и готовая записка
    для методсовета на казахском и русском.</div></div>
</div>
<p class="note">Все числа считает проверяемый код. ИИ размечает задания по темам программы и пишет текст записки.</p>
""", unsafe_allow_html=True)
    st.stop()


# ---------- библиотека ----------

if page == "Библиотека":     # данные не нужны: библиотека открывается без загрузки теста
    st.markdown("## Библиотека")
    lead("Что почитать по каждому диагнозу. Система называет причину провала темы, "
         "а здесь книги, которые помогают с этой причиной работать.")
    r1, r2 = st.columns([2, 1])
    role = r1.segmented_control("Для кого", ["Все", *library.ROLES], default="Все", key="lib_role") or "Все"
    lang = r2.radio("Язык пояснений", ["русский", "казахский"], horizontal=True, key="lib_lang")
    causes = list(library.BOOKS) if role == "Все" else library.ROLES[role]
    for cause in causes:
        st.markdown(f'<span class="cause">{core.CAUSES[cause][0]}</span>', unsafe_allow_html=True)
        st.markdown(books_html(library.books_for(cause), "kk" if lang == "казахский" else "ru"),
                    unsafe_allow_html=True)
        st.write("")
    st.markdown('<div class="note">Книги к диагнозу темы также показаны на странице «Тема» '
                'в блоке «Что почитать».</div>', unsafe_allow_html=True)
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
    lead("Какие темы ученики освоили ниже целевого уровня и насколько это надёжно.")
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
    m = m.sort_values("mastery", ascending=False).reset_index(drop=True)
    below = m["mastery"] < target
    fig = go.Figure()
    fig.add_vrect(x0=0, x1=target, fillcolor=RED, opacity=0.05, line_width=0, layer="below")
    fig.add_vline(x=target, line_dash="dot", line_color=RED, line_width=1.5)
    fig.add_annotation(x=target, y=1.02, yref="paper", text=f"цель {pct(target)}", showarrow=False,
                       font=dict(color=RED, size=12), xanchor="left", xshift=4)
    for ok, col in ((False, INK), (True, RED)):
        d = m[below == ok]
        fig.add_trace(go.Scatter(
            x=d["mastery"], y=d["topic_name"], mode="markers",
            marker=dict(size=13, color=col, line=dict(color="white", width=1.5)),
            error_x=dict(type="data", symmetric=False, array=d["hi"] - d["mastery"],
                         arrayminus=d["mastery"] - d["lo"], color=col, thickness=2.2, width=0),
            customdata=d[["lo", "hi"]].to_numpy(),
            hovertemplate="%{y}<br>освоение %{x:.0%}<br>интервал %{customdata[0]:.0%}–%{customdata[1]:.0%}<extra></extra>"))
        fig.add_trace(go.Scatter(   # подпись справа от интервала, чтобы не налезала на линию
            x=d["hi"], y=d["topic_name"], mode="text", text=[f"  <b>{pct(v)}</b>" for v in d["mastery"]],
            textposition="middle right", textfont=dict(color=col, size=13), cliponaxis=False, hoverinfo="skip"))
    lo_x = max(0.0, min(m["lo"].min(), target) - 0.08)
    fig.update_layout(showlegend=False, margin=dict(l=10, r=40, t=30, b=10),
                      xaxis=dict(range=[lo_x, 1.0], tickformat=".0%", showgrid=True, zeroline=False),
                      yaxis=dict(categoryorder="array", categoryarray=list(m["topic_name"])[::-1],
                                 showgrid=False, tickfont=dict(size=13)))
    chart(fig, 44 * len(m) + 70)
    st.markdown(f'<div class="note">Точка — доля верных ответов по теме, линия — 95% интервал (бутстреп по школам). Красным — темы ниже цели. '
                f'В расчёте {len(sub_meta)} учеников, {sub_meta["school_id"].nunique()} школ.</div>',
                unsafe_allow_html=True)

    st.markdown("#### Темы ниже цели")
    weak_box = st.container(key="weaklist")
    for d in A["diagnoses"]:
        cc = weak_box.columns([3, 2, 1], vertical_alignment="center")
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
    lead("Переключите режим: сырые средние смешивают эффект учебника с составом школ, которые его выбрали.")
    mode = st.segmented_control("Режим сравнения", ["Сырые средние", "С поправками"], default="Сырые средние",
                                key="tb_mode") or "Сырые средние"
    adj = mode == "С поправками"
    means = A["adj_means"] if adj else A["raw_means"]
    pairs = A["adj_pairs"] if adj else A["raw_pairs"]
    best = means.sort_values("mean").iloc[-1]["textbook"]

    win_col = INK if adj else RED
    fig = go.Figure()
    for r in means.itertuples():
        c = win_col if r.textbook == best else PENCIL
        fig.add_trace(go.Scatter(
            x=[r.mean], y=[r.textbook], mode="markers+text",
            marker=dict(size=18, color=c, line=dict(color="white", width=2)),
            error_x=dict(type="data", symmetric=False, array=[r.hi - r.mean], arrayminus=[r.mean - r.lo],
                         color=c, thickness=3, width=0),
            text=[f"<b>{pct(r.mean)}</b>"], textposition="top center", textfont=dict(color=c, size=15),
            cliponaxis=False,
            hovertemplate=(f"{r.textbook}: %{{x:.1%}}<br>интервал {r.lo:.1%}–{r.hi:.1%}"
                           f"<br>учеников {r.n_students}, школ {r.n_schools}<extra></extra>")))
    lo = min(A["raw_means"]["lo"].min(), A["adj_means"]["lo"].min()) - 0.02
    hi = max(A["raw_means"]["hi"].max(), A["adj_means"]["hi"].max()) + 0.02
    fig.update_layout(showlegend=False, margin=dict(l=10, r=20, t=20, b=10),
                      xaxis=dict(range=[lo, hi], tickformat=".0%", title="средний результат теста"),
                      yaxis=dict(categoryorder="array", categoryarray=sorted(means["textbook"])[::-1],
                                 showgrid=True, tickfont=dict(size=14)))
    chart(fig, 300)
    st.markdown('<div class="note">Шкала одинакова в обоих режимах, поэтому видно, как сдвигаются точки.</div>',
                unsafe_allow_html=True)

    if adj:
        st.markdown(f'<div class="verdict">С поправкой на прошлый балл, тип местности и язык обучения '
                    f'лучший результат у «{best}».</div>', unsafe_allow_html=True)
        st.markdown('<div class="note">Учебники сравниваются на одном и том же «среднем» ученике. '
                    'Интервалы учитывают, что ученики одной школы похожи друг на друга.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="verdict wrong">По сырым средним лучший — «{best}». Но учебники выбирают школы '
                    f'с разным составом учеников.<span class="pen">проверьте с поправками</span></div>',
                    unsafe_allow_html=True)

    rows = []
    for r in pairs.itertuples():
        better = r.b if r.diff_b_minus_a > 0 else r.a
        lo_, hi_ = (r.lo, r.hi) if r.diff_b_minus_a > 0 else (-r.hi, -r.lo)
        rows.append({"Пара": f"{r.a} — {r.b}", "Разница": f"{abs(r.diff_b_minus_a) * 100:.1f} п.п. в пользу «{better}»",
                     "95% интервал разницы": f"{lo_ * 100:+.1f} … {hi_ * 100:+.1f} п.п.",
                     "Вывод": "подтверждено" if r.confirmed else "различие не подтверждено"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.markdown("#### Почему ответы расходятся")
    ba = A["by_area"].copy()
    tbs = sorted(ba["textbook"].unique())
    allrow = (A["raw_means"][["textbook", "mean", "n_students"]]
              .rename(columns={"n_students": "size"}).assign(area="все ученики"))
    rows_ = pd.concat([ba, allrow], ignore_index=True)
    order = [*sorted(ba["area"].unique()), "все ученики"]
    smax = rows_["size"].max()
    fig2 = go.Figure()
    fig2.add_hrect(y0=-0.5, y1=0.5, fillcolor=PENCIL, opacity=0.08, line_width=0)   # строка «все ученики»
    for tb in tbs:
        d = rows_[rows_["textbook"] == tb].set_index("area").reindex(order).reset_index()
        col = tb_color(tb, tbs)
        fig2.add_trace(go.Scatter(
            x=d["mean"], y=d["area"], mode="markers+text", name=tb,
            marker=dict(size=10 + 34 * (d["size"] / smax) ** 0.5, color=col, opacity=0.9,
                        line=dict(color="white", width=1.5)),
            text=[f"{tb.split()[-1]} {pct(v)}" for v in d["mean"]], textposition="top center",
            textfont=dict(color=col, size=13), cliponaxis=False, customdata=d["size"],
            hovertemplate=f"{tb}, %{{y}}: %{{x:.1%}}<br>учеников %{{customdata}}<extra></extra>"))
    fig2.update_layout(margin=dict(l=10, r=20, t=10, b=10), showlegend=False,
                       xaxis=dict(tickformat=".0%", title="средний результат теста"),
                       yaxis=dict(categoryorder="array", categoryarray=order[::-1], tickfont=dict(size=14),
                                  range=[-0.6, len(order) - 0.3]))
    chart(fig2, 330)
    share = meta.groupby("textbook")["area"].apply(lambda s: (s == "город").mean())
    st.markdown('<div class="note">Размер точки — число учеников. Нижняя строка — общее среднее без поправки.</div>',
                unsafe_allow_html=True)
    st.write("Доля городских учеников: " + ", ".join(f"«{k}» {pct(v)}" for k, v in share.items()) +
             ". И в городе, и в селе порядок учебников один, а в общем среднем он переворачивается: "
             "учебник, который чаще берут городские школы, выигрывает за счёт состава учеников. "
             "Это парадокс Симпсона.")


# ---------- тема ----------

elif page == "Тема":
    codes = list(plan["topic_code"])
    default = st.session_state.get("topic", A["weak"][0] if A["weak"] else codes[0])
    code = st.selectbox("Тема", codes, index=codes.index(default), format_func=lambda c: f"{c} · {names[c]}")
    st.session_state.topic = code
    mrow = A["mastery"].set_index("topic_code").loc[code]
    st.markdown(f"## {names[code]}")
    lead("Почему тема проседает и какую меру выбрать: часы, материалы к учебнику, поддержку школ или замену задания.")
    c = st.columns(3)
    kpi(c[0], pct(mrow["mastery"]), "освоение темы")
    kpi(c[1], f"{pct(mrow['lo'])}–{pct(mrow['hi'])}", "95% интервал")
    kpi(c[2], pct(target), "цель")
    st.write("")

    if code in diag:
        d = diag[code]
        title, action = core.CAUSES.get(d["cause"], ("Недостаточно данных", "Собрать больше данных."))
        st.markdown(f'''<div class="diag"><span class="cause">{title}</span>
<div class="drow"><span class="dk">Почему</span><span>{d['details']}</span></div>
<div class="drow"><span class="dk">Что делать</span><span>{action}</span></div></div>''', unsafe_allow_html=True)
        books = library.books_for(d["cause"])
        if books:
            with st.expander("Что почитать"):
                st.markdown(books_html(books), unsafe_allow_html=True)
    else:
        st.markdown('<div class="verdict">Тема освоена на уровне цели или выше. Мер не требуется.</div>',
                    unsafe_allow_html=True)

    sc = A["scores_clean"] if code in A["scores_clean"] else A["scores_all"]
    t1, t2 = st.columns(2)
    with t1:
        st.markdown("##### С каким учебником тема проседает")
        eff = core.textbook_topic_effect(sc, meta, code)
        gap = core.TEXTBOOK_GAP * 100
        span = max(gap + 4, float((eff[["lo", "hi"]].abs().max().max()) * 100) + 3)
        fig = go.Figure()
        fig.add_vrect(x0=-span, x1=-gap, fillcolor=RED, opacity=0.06, line_width=0, layer="below")
        fig.add_annotation(x=-span, y=0, yref="paper", text=" заметно хуже", showarrow=False,
                           font=dict(color=RED, size=11), xanchor="left", yanchor="bottom")
        fig.add_vline(x=0, line_color=PENCIL, line_width=1)
        for r in eff.itertuples():
            bad = r.effect <= -core.TEXTBOOK_GAP and r.hi < 0
            col = RED if bad else INK
            fig.add_trace(go.Scatter(
                x=[r.effect * 100], y=[r.textbook], mode="markers+text",
                marker=dict(size=13, color=col, line=dict(color="white", width=1.5)),
                error_x=dict(type="data", symmetric=False, array=[(r.hi - r.effect) * 100],
                             arrayminus=[(r.effect - r.lo) * 100], color=col, thickness=2.2, width=0),
                text=[f"{r.effect * 100:+.0f} п.п."], textposition="top center", textfont=dict(color=col, size=12),
                cliponaxis=False, hovertemplate=f"{r.textbook}: %{{x:+.1f}} п.п.<extra></extra>"))
        fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=24, b=10),
                          xaxis=dict(range=[-span, span], title="п.п. относительно других учебников",
                                     zeroline=False),
                          yaxis=dict(categoryorder="array", categoryarray=sorted(eff["textbook"])[::-1],
                                     tickfont=dict(size=13)))
        chart(fig, 250)
    with t2:
        st.markdown("##### Какие школы отстают")
        sch = core.school_topic_effect(sc, meta, code)
        sch = sch.assign(**{"Отклонение, п.п.": (sch["shrunk"] * 100).round(1), "Освоение": (sch["score"] * 100).round(0)})
        sch["Статус"] = [("мало учеников" if n < 20 else "ниже ожидаемого" if s <= -core.SCHOOL_GAP else "")
                         for n, s in zip(sch["n"], sch["shrunk"])]
        st.dataframe(sch[["school_id", "n", "Освоение", "Отклонение, п.п.", "Статус"]].head(10)
                     .rename(columns={"school_id": "Школа", "n": "Учеников"}),
                     hide_index=True, use_container_width=True, height=250)

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
    lead(f"Сумма часов не меняется: {total} ч. Часы получают темы с диагнозом «трудна сама тема», "
         "отдают темы с запасом над целью не меньше 10 п.п. Изменение темы не больше 20% её часов.")
    ch = h[h["delta"] != 0].sort_values("delta", ascending=False)
    if len(ch):
        fig = go.Figure(go.Bar(
            x=ch["delta"], y=ch["topic_name"], orientation="h",
            marker_color=[INK if v > 0 else PENCIL for v in ch["delta"]],
            text=[f"{v:+d} ч  ({o} → {n})" for v, o, n in zip(ch["delta"], ch["hours"], ch["new_hours"])],
            textposition="outside", cliponaxis=False, textfont=dict(size=13),
            hovertemplate="%{y}: %{x:+d} ч<extra></extra>"))
        fig.add_vline(x=0, line_color=GRAPHITE, line_width=1)
        m_ = max(ch["delta"].abs()) + 2.5
        fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10), bargap=0.45,
                          xaxis=dict(range=[-m_, m_], title="изменение, часов", dtick=1, zeroline=False),
                          yaxis=dict(categoryorder="array", categoryarray=list(ch["topic_name"])[::-1],
                                     tickfont=dict(size=13)))
        chart(fig, 52 * len(ch) + 80)
    else:
        st.markdown('<div class="verdict">При текущей цели перераспределять часы не нужно.</div>',
                    unsafe_allow_html=True)
    view = h.assign(**{
        "Тема": h["topic_name"], "Освоение": (h["mastery"] * 100).round(0).astype(int).astype(str) + "%",
        "Было, ч": h["hours"], "Предлагается, ч": h["new_hours"],
        "Изменение": [f"{d:+d}" if d else "" for d in h["delta"]],
        "Причина": h["reason"], "Уверенность": h["confidence"]})
    view = view[["Тема", "Освоение", "Было, ч", "Предлагается, ч", "Изменение", "Причина", "Уверенность"]]

    def color(v):
        if isinstance(v, str) and v.startswith("+"):
            return f"color: {INK}; font-weight: 600"
        if isinstance(v, str) and v.startswith("-"):
            return f"color: {PENCIL}; font-weight: 600"
        return ""

    st.dataframe(view.style.map(color, subset=["Изменение"]), hide_index=True, use_container_width=True,
                 column_config={"Причина": st.column_config.TextColumn(width="large")})
    st.markdown(f"**Итого:** было {total} ч, предлагается {int(h['new_hours'].sum())} ч.")
    st.info("Это гипотеза для пилота, а не доказанный эффект: на данных одного года влияние часа на результат "
            "измерить нельзя. Темы с причиной «учебник», «школы» или «задание» часов не получают: им нужны другие меры.")


# ---------- ИИ-разметка ----------

elif page == "ИИ-разметка":
    st.markdown("## ИИ-разметка заданий")
    lead("Результаты теста приходят по номерам заданий, а не по темам. Модель относит каждое задание "
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
            f"- Классификатор: логистическая регрессия. Заданий для обучения: {len(load_train())}.\n"
            f"- Проверка на заданиях, которых модель при обучении не видела: "
            f"верно {int(test_df['ok'].sum())} из {len(test_df)}.\n"
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
    lead("Текст собирается только из рассчитанных чисел, а каждое число в нём сверяется с расчётом.")
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
