import io
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

import core
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
    font=dict(family="Nunito, sans-serif", color=GRAPHITE, size=14),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=PENCIL)),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=GRAPHITE)),
    hoverlabel=dict(font=dict(family="Nunito, sans-serif")),
    colorway=[INK, PENCIL, "#B8C2D6"],
))
pio.templates.default = "plotly_white+dalel"

st.markdown(f"""
<style>
{FONTS_CSS}
html, body, .stApp, .stMarkdown, p, li, label, input, textarea, button, [data-testid="stWidgetLabel"] {{
  font-family: 'Nunito', sans-serif;
}}
#MainMenu, footer {{visibility: hidden;}}
.block-container {{padding-top: 2.2rem; max-width: 1120px;}}
h1, h2, h3, h4 {{font-family: 'Nunito', sans-serif !important; color: {INK}; letter-spacing: -0.01em;}}
h2 {{font-size: 1.7rem !important; font-weight: 700 !important; line-height: 1.2 !important;}}
h3, h4, h5 {{font-weight: 500 !important;}}
p, li {{max-width: 75ch; line-height: 1.6;}}

/* боковая панель: поля тетради */
section[data-testid="stSidebar"] {{background: #FFFFFF; border-right: 2px solid #F2C4C4;}}
.brand {{font-family: 'Nunito', sans-serif; font-weight: 700; font-size: 1.6rem; color: {INK}; margin: 0;}}
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
.kpi .v {{font-family: 'Nunito', sans-serif; font-size: 1.9rem; font-weight: 500; color: {INK}; line-height: 1.15;}}
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
h5 {{font-size: 1rem !important; color: {GRAPHITE} !important; margin-top: .6rem;}}
[data-testid="stSegmentedControl"] button {{font-size: .95rem;}}
@media (max-width: 700px) {{ .diag .drow {{grid-template-columns: 1fr; gap: .1rem;}} }}
.verdict {{border-left: 3px solid {INK}; padding: .7rem 1rem; margin: .4rem 0 1rem 0; background: #F3F6FB; color: {GRAPHITE};}}
.verdict.wrong {{border-left-color: {RED}; background: #FDF3F3;}}
.verdict .pen {{font-family: 'Caveat', cursive; font-size: 1.35rem; color: {RED}; margin-left: .5rem; white-space: nowrap; line-height: 1;}}
.synth {{font-size:.82rem; color:{RED}; border-bottom: 1.5px solid {RED};}}
.side-note {{font-size: .82rem; color: {PENCIL}; line-height: 1.45;}}

/* главная */
.hero {{padding: 1.2rem 0 1.4rem 0; margin-bottom: 1rem;}}
.hero .eyebrow {{display:inline-block; font-weight:800; font-size:.85rem; letter-spacing:.06em; text-transform:uppercase;
  color:{INK}; background:#E6ECF8; border-radius:999px; padding:.35rem .9rem; margin-bottom:1.1rem;}}
.hero h1 {{font-size: clamp(2.2rem, 4.6vw, 3.6rem) !important; font-weight: 900 !important; line-height: 1.04 !important;
  color:#1F2430 !important; margin: 0 0 1rem 0; padding: 0; max-width: 19ch; letter-spacing:-.02em;}}
.hero h1 .acc {{color:{INK};}}
.hero .sub {{font-size: 1.2rem; font-weight:600; color: #4A5260; max-width: 52ch; margin: 0 0 1.8rem 0; line-height: 1.5;}}
.stats {{display:grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 0 0 1.8rem 0;}}
.stat {{background:#FFFFFF; border-radius:20px; padding:1.1rem 1.2rem; box-shadow:0 8px 24px rgba(31,36,48,.07);}}
.stat .v {{font-size: 2.1rem; font-weight: 900; color:{INK}; line-height:1.05;}}
.stat .v.red {{color:{RED};}}
.stat .l {{font-size:.9rem; font-weight:600; color:{PENCIL}; margin-top:.3rem; line-height:1.35;}}
.flip {{background:#FFFFFF; border-radius:24px; padding: 1.5rem 1.7rem 1.4rem 1.7rem; box-shadow:0 14px 40px rgba(31,36,48,.10); max-width:100%;}}
.flip .q {{font-weight: 900; font-size:1.25rem; color: #1F2430; margin-bottom: .9rem;}}
.flip .row {{display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap; padding: .5rem 0; border-top:1px solid #EFEBE2;}}
.flip .lbl {{width: 15rem; color: {PENCIL}; font-weight:600; font-size: .95rem;}}
.flip .ans {{font-weight:900; font-size: 1.45rem; color: {INK};}}
.flip .wrong {{text-decoration: line-through; text-decoration-color: {RED}; text-decoration-thickness: 3px; color: {PENCIL};}}
.flip .pen {{font-family: 'Caveat', cursive; font-size: 1.5rem; color: {RED}; line-height: 1;}}
.flip .src {{font-size: .82rem; color: {PENCIL}; margin-top: .8rem;}}
.ruled {{display:grid; grid-template-columns: repeat(3, 1fr); gap:1rem; margin: 1.6rem 0 1.4rem 0;}}
.ruled .r {{background:#FFFFFF; border-radius:20px; padding:1.3rem 1.3rem 1.4rem 1.3rem; box-shadow:0 8px 24px rgba(31,36,48,.07);}}
.ruled .n {{display:inline-flex; width:2.2rem; height:2.2rem; border-radius:50%; background:{INK}; color:#fff;
  font-weight:900; align-items:center; justify-content:center; margin-bottom:.7rem;}}
.ruled .t {{font-weight: 900; color: #1F2430; font-size: 1.2rem; margin-bottom:.35rem;}}
.ruled .d {{color: #4A5260; font-size:.97rem; line-height:1.5;}}
.stButton button[kind="primary"] {{border-radius:999px; font-weight:800; padding:.65rem 1.4rem; font-size:1.05rem;}}
section[data-testid="stSidebar"] {{background: #FFFFFF !important; border-right: 1px solid #ECE7DC !important;}}
section[data-testid="stSidebar"] div[role="radiogroup"] label {{border-radius: 12px !important; border-left: 0 !important; margin-bottom:2px;}}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] {{background:#E6ECF8 !important;}}
.brand {{font-weight: 900 !important; font-size: 1.9rem !important;}}
h2 {{font-weight: 900 !important; font-size: 2.1rem !important; color:#1F2430 !important;}}
.kpi {{background:#FFFFFF; border:0; border-radius:18px; padding:.9rem 1.1rem; box-shadow:0 8px 24px rgba(31,36,48,.07);}}
.kpi .v {{font-weight: 900 !important;}}

@media (max-width: 700px) {{
  .stats {{grid-template-columns: 1fr 1fr;}}
  .flip .lbl {{width: auto;}}
  .ruled {{grid-template-columns: 1fr;}}
}}

/* общий стиль страниц: карточки вместо линий */
[data-testid="stPlotlyChart"] {{background:#FFFFFF; border-radius:22px; padding:0; overflow:hidden;
  box-shadow:0 10px 30px rgba(31,36,48,.07); margin-bottom:.6rem;}}
[data-testid="stTable"], [data-testid="stDataFrame"] {{background:#FFFFFF; border-radius:18px; overflow:hidden;
  box-shadow:0 8px 24px rgba(31,36,48,.06);}}
[data-testid="stTable"] table {{border:0 !important;}}
[data-testid="stTable"] th {{background:#F4F1EA !important; font-weight:800 !important; color:#1F2430 !important; border:0 !important;}}
[data-testid="stTable"] td {{border:0 !important; border-top:1px solid #F0ECE3 !important;}}
div[data-baseweb="select"] > div {{background:#FFFFFF !important; border-radius:14px !important; border:1px solid #E7E2D7 !important;}}
[data-testid="stExpander"] details {{background:#FFFFFF; border-radius:16px !important; border:1px solid #E7E2D7 !important;}}
button[data-variant="segmented_control"] {{border-radius:999px !important; margin-right:.35rem; font-weight:700 !important; padding:.35rem 1rem !important;}}
button[data-variant="segmented_control"][aria-checked="true"] {{background:{INK} !important; color:#FFFFFF !important; border-color:{INK} !important;}}
button[data-variant="segmented_control"][aria-checked="true"] p {{color:#FFFFFF !important;}}
.stButton button {{border-radius:999px !important; font-weight:700 !important;}}
.stDownloadButton button {{border-radius:999px !important; font-weight:800 !important;}}
h3 {{font-weight:900 !important; color:#1F2430 !important; font-size:1.45rem !important; margin-top:1.2rem !important;}}
h4 {{font-weight:800 !important; color:#1F2430 !important;}}
.lead {{font-size:1.12rem !important; font-weight:600; color:#5F6878 !important;}}
.diag, .verdict {{border-left:0 !important; border-radius:18px; background:#FFFFFF !important;
  box-shadow:0 8px 24px rgba(31,36,48,.07); padding:1.1rem 1.3rem !important; position:relative;}}
.diag::before, .verdict::before {{content:""; position:absolute; left:0; top:14px; bottom:14px; width:5px; border-radius:0 4px 4px 0; background:{RED};}}
.verdict:not(.wrong)::before {{background:{INK};}}
.cause {{border-radius:999px !important; padding:3px 12px !important; background:#FDECEC !important; border:0 !important;}}
[data-testid="stAlert"] {{border-radius:16px !important;}}
[data-testid="stMetric"] {{background:#FFFFFF; border-radius:18px; padding:.9rem 1.1rem; box-shadow:0 8px 24px rgba(31,36,48,.07);}}
.st-key-weaklist {{background:#FFFFFF; border-radius:20px; border-top:0 !important; padding:.4rem 1.1rem;
  box-shadow:0 8px 24px rgba(31,36,48,.07);}}
.st-key-weaklist [data-testid="stHorizontalBlock"]:last-child {{border-bottom:0;}}
.side-note {{background:#F6F3EC; border-radius:14px; padding:.7rem .9rem;}}
.synth {{border:0 !important; background:#FDECEC; border-radius:999px; padding:3px 10px; font-weight:700;}}

/* лендинг */
.hero .eyebrow i {{display:inline-block; width:.5rem; height:.5rem; border-radius:50%; background:#E0A800; margin-right:.5rem; vertical-align:middle;}}
.hero .eyebrow {{background:#FFFFFF !important; box-shadow:0 2px 10px rgba(31,36,48,.06); text-transform:none !important; letter-spacing:0 !important; font-size:.9rem !important;}}
.hero h1 mark {{background: linear-gradient(transparent 62%, #FFD866 62%, #FFD866 92%, transparent 92%); color:{INK}; padding:0 .05em;}}
.trust {{font-size:.88rem; font-weight:700; color:{PENCIL}; margin-top:.6rem;}}
.visual {{position:relative; padding:1.6rem 0 2.4rem 0;}}
.shotcard {{background:linear-gradient(145deg,#E6ECF8,#F6EFD9); border-radius:28px; padding:1.1rem; box-shadow:0 18px 50px rgba(31,36,48,.12);}}
.shotcard img {{width:100%; border-radius:18px; display:block;}}
.chip {{position:absolute; background:#FFFFFF; border-radius:16px; padding:.7rem 1rem; box-shadow:0 12px 30px rgba(31,36,48,.14);
  font-size:.92rem; color:#1F2430; display:flex; gap:.6rem; align-items:center;}}
.chip.c1 {{top:.4rem; left:-1.2rem;}}
.chip.c2 {{bottom:.6rem; right:-.6rem; display:block;}}
.chip .cl {{font-size:.75rem; font-weight:800; color:{RED}; text-transform:uppercase; letter-spacing:.04em; margin-bottom:.15rem;}}
.chip .dot {{width:.7rem; height:.7rem; border-radius:50%; background:{RED}; flex:none;}}
.sec {{margin:3.2rem 0 0 0;}}
.sec .kicker {{font-weight:800; font-size:.85rem; color:{INK}; text-transform:uppercase; letter-spacing:.08em;}}
.sec .h, .closer .h {{font-size:clamp(1.7rem,3.4vw,2.5rem) !important; font-weight:900 !important; line-height:1.12 !important; color:#1F2430 !important; margin:.4rem 0 1.4rem 0 !important; max-width:24ch;}}
.bignums {{display:grid; grid-template-columns:repeat(3,1fr); gap:0; border-top:1px solid #E7E2D7;}}
.bn {{padding:1.4rem 1.4rem 1.2rem 0;}}
.bn + .bn {{border-left:1px solid #E7E2D7; padding-left:1.4rem;}}
.bn .v {{font-size:clamp(2.6rem,5vw,3.8rem); font-weight:900; color:{INK}; line-height:1;}}
.bn .v.red {{color:{RED};}}
.bn .l {{font-weight:700; color:#3F4757; margin-top:.6rem; line-height:1.45;}}
.bn .s {{font-size:.8rem; color:{PENCIL}; margin-top:.6rem; text-decoration:underline; text-decoration-color:#D9D3C6;}}
.callout {{background:#FFF3D6; border-radius:18px; padding:1.1rem 1.4rem; font-weight:800; color:#1F2430; margin-top:1.2rem; font-size:1.05rem;}}
.sec.dark {{background:#16223F; border-radius:28px; padding:2.2rem 2rem 2.4rem 2rem;}}
.sec.dark .kicker {{color:#FFD866;}}
.sec.dark .h {{color:#FFFFFF !important;}}
.steps {{display:grid; grid-template-columns:repeat(4,1fr); gap:1rem;}}
.steps .st {{background:rgba(255,255,255,.07); border-radius:20px; padding:1.2rem;}}
.steps .n {{width:2.3rem; height:2.3rem; border-radius:50%; background:#FFD866; color:#16223F; font-weight:900; display:flex; align-items:center; justify-content:center; margin-bottom:.8rem;}}
.steps .t {{font-weight:900; color:#FFFFFF; font-size:1.1rem; margin-bottom:.35rem;}}
.steps .d {{color:#C4CCE0; font-size:.95rem; line-height:1.5;}}
.plans {{display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; align-items:stretch;}}
.pl {{background:#FFFFFF; border-radius:22px; padding:1.5rem; box-shadow:0 8px 24px rgba(31,36,48,.07); border:2px solid transparent;}}
.pl.main {{border-color:{INK}; box-shadow:0 14px 36px rgba(29,58,138,.16);}}
.pl .who {{font-weight:800; color:{PENCIL};}}
.pl .pr {{font-size:2rem; font-weight:900; color:#1F2430; margin:.4rem 0 .6rem 0;}}
.pl .pr span {{font-size:1rem; color:{PENCIL}; font-weight:700; margin-left:.2rem;}}
.pl .d {{color:#4A5260; line-height:1.5;}}
.faq details {{background:#FFFFFF; border-radius:16px; padding:1rem 1.3rem; margin-bottom:.6rem; box-shadow:0 4px 14px rgba(31,36,48,.05);}}
.faq summary {{font-weight:800; color:#1F2430; cursor:pointer; font-size:1.05rem;}}
.faq details p {{margin:.6rem 0 0 0; color:#4A5260;}}
.closer {{background:#E6ECF8; border-radius:28px; padding:2rem; margin:3.2rem 0 1rem 0; text-align:center;}}
.closer .h {{margin:0 auto .5rem auto !important;}}
.closer p {{margin:0 auto; color:#4A5260; font-weight:600;}}
.block-container {{max-width: 1200px !important;}}
@media (max-width: 800px) {{
  .bignums, .steps, .plans {{grid-template-columns:1fr;}}
  .bn + .bn {{border-left:0; border-top:1px solid #E7E2D7; padding-left:0;}}
  .chip.c1 {{left:.4rem;}} .chip.c2 {{right:.4rem;}}
}}

.take {{background:#FFFFFF; border-radius:20px; padding:1.1rem 1.4rem; margin:.2rem 0 1.4rem 0; box-shadow:0 8px 24px rgba(31,36,48,.07);
  display:flex; gap:1rem; align-items:flex-start; border:2px solid #FFD866;}}
.take .tk {{flex:none; background:#FFD866; color:#1F2430; font-weight:900; font-size:.8rem; border-radius:999px; padding:.3rem .8rem; margin-top:.15rem;}}
.take p {{margin:0; font-size:1.12rem; font-weight:600; color:#1F2430; line-height:1.5; max-width:none;}}
.take b {{color:{INK};}}
.howto {{display:flex; flex-wrap:wrap; gap:.6rem 1.4rem; align-items:center; background:#F4F1EA; border-radius:16px; padding:.75rem 1rem; margin:.2rem 0 .8rem 0;}}
.howto .hl {{font-weight:900; font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; color:{PENCIL};}}
.howto .hi {{display:flex; gap:.5rem; align-items:center; font-size:.92rem; color:#3F4757; font-weight:600; max-width:60ch;}}
.howto svg {{flex:none;}}
.wl b {{font-size:1.02rem; color:#1F2430;}}
.wl .bar {{position:relative; height:10px; background:#EFEBE2; border-radius:999px; margin:.4rem 0 .3rem 0; max-width:420px;}}
.wl .bar i {{position:absolute; left:0; top:0; bottom:0; background:{RED}; border-radius:999px;}}
.wl .bar u {{position:absolute; top:-4px; bottom:-4px; width:2px; background:#1F2430;}}
.wl span {{font-size:.86rem; color:{PENCIL}; font-weight:600;}}
.pairs {{display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; margin-bottom:.4rem;}}
.pc {{background:#FFFFFF; border-radius:18px; padding:1rem 1.1rem; box-shadow:0 8px 24px rgba(31,36,48,.07); border:2px solid transparent;}}
.pc.ok {{border-color:{INK};}}
.pc .pt {{font-weight:800; color:#1F2430;}}
.pc .pv {{font-size:1.5rem; font-weight:900; color:{INK}; margin:.2rem 0;}}
.pc .pb {{display:inline-block; font-size:.85rem; font-weight:800; border-radius:999px; padding:.2rem .7rem; background:#F4F1EA; color:{PENCIL};}}
.pc.ok .pb {{background:#E6ECF8; color:{INK};}}
@media (max-width: 800px) {{ .pairs {{grid-template-columns:1fr;}} .take {{flex-direction:column; gap:.5rem;}} }}
@media (prefers-reduced-motion: reduce) {{ * {{transition: none !important; animation: none !important;}} }}

/* ===== DALEL PRODUCT UI/UX POLISH ===== */
:root {{
  --dl-bg: #F4F6FB;
  --dl-surface: #FFFFFF;
  --dl-ink: #243B80;
  --dl-text: #202A3B;
  --dl-muted: #77839A;
  --dl-border: #E5EAF3;
  --dl-shadow: 0 12px 32px rgba(28, 39, 71, .07);
}}
.stApp {{ background: var(--dl-bg); color: var(--dl-text); }}
[data-testid="stHeader"] {{ background: rgba(244,246,251,.9); }}
.block-container {{ max-width: 1360px !important; padding: 2rem 2.4rem 3.5rem !important; }}
h1, h2, h3, h4 {{ color: var(--dl-text) !important; letter-spacing: -.035em !important; }}
h1 {{ font-weight: 900 !important; letter-spacing: -.05em !important; }}
h2 {{ font-size: clamp(1.55rem, 2.4vw, 2rem) !important; font-weight: 850 !important; }}
h3 {{ font-weight: 800 !important; }}
p, li {{ line-height: 1.65; }}
section[data-testid="stSidebar"] {{
  background: #17233F !important;
  border-right: 1px solid rgba(255,255,255,.08);
}}
section[data-testid="stSidebar"] > div {{ background: transparent !important; }}
section[data-testid="stSidebar"] .brand {{ color: #FFFFFF !important; font-size: 1.8rem; font-weight: 900; letter-spacing: -.04em; }}
section[data-testid="stSidebar"] .brand-sub {{ color: #B8C4DC !important; }}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{ color: #E5EBF7; }}
section[data-testid="stSidebar"] div[role="radiogroup"] {{ gap: .3rem !important; }}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] {{
  border: 1px solid transparent !important;
  border-radius: 10px !important;
  margin: 2px 0 !important;
  padding: .55rem .75rem !important;
  transition: background .16s ease, border-color .16s ease;
}}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] {{
  background: rgba(112,139,255,.18) !important;
  border-color: rgba(160,178,255,.22) !important;
}}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] p {{
  color: #FFFFFF !important; font-weight: 850 !important;
}}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover {{
  background: rgba(255,255,255,.08) !important;
}}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color: #AEBBD4 !important; }}
.kpi {{
  background: var(--dl-surface);
  border: 1px solid var(--dl-border);
  border-left: 3px solid var(--dl-ink);
  border-radius: 14px;
  padding: 1rem 1.1rem !important;
  box-shadow: 0 5px 18px rgba(28,39,71,.035);
}}
.kpi .v {{ font-size: clamp(1.55rem, 2.2vw, 2rem) !important; font-weight: 900 !important; }}
.kpi .l {{ color: var(--dl-muted) !important; font-weight: 700; }}
.lead {{ color: #66738B !important; font-size: 1.02rem; max-width: 78ch; }}
.take, .verdict, .diag {{
  border-radius: 14px !important;
  box-shadow: 0 5px 18px rgba(28,39,71,.035);
}}
[data-testid="stPlotlyChart"] {{
  background: #FFFFFF;
  border: 1px solid var(--dl-border);
  border-radius: 16px;
  padding: .55rem;
  box-shadow: 0 5px 18px rgba(28,39,71,.035);
}}
[data-testid="stDataFrame"] {{
  border: 1px solid var(--dl-border);
  border-radius: 12px;
  overflow: hidden;
  background: #FFFFFF;
}}
[data-testid="stWidgetLabel"] p {{ color: #46536A !important; font-weight: 800 !important; }}
.stButton > button, .stDownloadButton > button {{
  border-radius: 10px !important;
  min-height: 2.65rem;
  font-weight: 800 !important;
  transition: transform .16s ease, box-shadow .16s ease, background .16s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  transform: translateY(-1px);
  box-shadow: 0 7px 18px rgba(36,59,128,.13);
}}
input, textarea, [data-baseweb="select"] > div {{
  border-radius: 10px !important;
}}
[data-testid="stAlert"] {{ border-radius: 12px !important; }}
[data-testid="stExpander"] {{
  border: 1px solid var(--dl-border) !important;
  border-radius: 12px !important;
  background: #FFFFFF;
}}
.stCaption, [data-testid="stCaptionContainer"] {{ color: var(--dl-muted) !important; }}
button:focus-visible, input:focus-visible, textarea:focus-visible {{
  outline: 3px solid rgba(64,87,214,.32) !important;
  outline-offset: 2px !important;
}}
@media (max-width: 900px) {{
  .block-container {{ padding: 1.25rem 1rem 2.5rem !important; }}
  .kpi {{ padding: .8rem !important; }}
}}
@media (max-width: 600px) {{
  h1 {{ font-size: 1.8rem !important; }}
  h2 {{ font-size: 1.45rem !important; }}
}}

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
    fig.update_layout(height=height, plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)


def lead(text):
    st.markdown(f'<p class="lead">{text}</p>', unsafe_allow_html=True)


def takeaway(text):
    st.markdown(f'<div class="take"><span class="tk">Главное</span><p>{text}</p></div>', unsafe_allow_html=True)


def howto(*items):
    glyph = {"dot": '<svg width="54" height="18" viewBox="0 0 54 18" aria-hidden="true"><line x1="6" y1="9" x2="48" y2="9" stroke="#1D3A8A" stroke-width="3" stroke-linecap="round"/><circle cx="27" cy="9" r="7" fill="#1D3A8A" stroke="#fff" stroke-width="2"/></svg>',
             "red": '<svg width="18" height="18" aria-hidden="true"><circle cx="9" cy="9" r="7" fill="#C62828"/></svg>',
             "goal": '<svg width="18" height="18" aria-hidden="true"><line x1="9" y1="1" x2="9" y2="17" stroke="#C62828" stroke-width="2" stroke-dasharray="3 3"/></svg>',
             "size": '<svg width="30" height="18" aria-hidden="true"><circle cx="6" cy="11" r="4" fill="#8A93A3"/><circle cx="21" cy="9" r="8" fill="#8A93A3"/></svg>'}
    body = "".join(f'<div class="hi">{glyph[g]}<span>{t}</span></div>' for g, t in items)
    st.markdown(f'<div class="howto"><span class="hl">Как читать</span>{body}</div>', unsafe_allow_html=True)


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
    st.markdown('<p class="brand">Дәлел</p><p class="brand-sub">Учебник выбирают доказательства, а не мнения</p>',
                unsafe_allow_html=True)
    page = st.radio("Раздел", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    target = st.slider(
        "Целевой уровень освоения темы", 0.50, 0.80, 0.60, 0.01,
        format="%.2f",
        help="Порог, с которым сравнивается доля верных ответов. Например, при 60% тема ниже цели, если ученики решают верно меньше 6 заданий из 10."
    )
    st.caption(f"Сейчас цель: {pct(target)} правильных ответов")
    with st.expander("Словарь показателей"):
        st.markdown(
            "**Освоение темы** — доля ответов, на которые ученики ответили правильно.\n\n"
            "**Целевой уровень** — желаемая доля правильных ответов.\n\n"
            "**95% интервал** — диапазон возможного значения результата с учётом различий между школами. Это не оценка отдельного ученика.\n\n"
            "**Поправка на состав школ** — сравнение учебников с учётом предыдущего уровня учеников, языка обучения и типа местности.\n\n"
            "**Различающая способность** — насколько задание помогает отличить учеников, хорошо освоивших материал, от тех, кому нужна поддержка."
        )
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
    _, qt = tagger_quality()
    q_ok, q_n = int(qt["ok"].sum()), len(qt)
    n_weak = len(demo["weak"])
    tb_diag = next((d for d in demo["diagnoses"] if d["cause"] == "textbook"), None)
    tb_name = load_demo()[2].set_index("topic_code")["topic_name"].get(tb_diag["topic_code"], "") if tb_diag else ""

    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        st.markdown("""
<div class="hero">
  <span class="eyebrow"><i></i>Для методистов, школ и отделов образования</span>
  <h1>Учебник выбирают <mark>доказательства</mark>, а не мнения</h1>
  <p class="sub">«Дәлел» берёт результаты теста и показывает, какие темы провалены, почему
  и что изменить: учебник, часы или работу со школами.</p>
</div>""", unsafe_allow_html=True)
        b1, b2 = st.columns([1, 1.25])
        if b1.button("Открыть демо", type="primary", use_container_width=True):
            st.session_state.data = load_demo()
            st.session_state.synthetic = True
            go_to("Обзор тем")
        with b2.expander("Загрузить свои данные"):
            st.markdown(
                "Загрузите три CSV-файла. Сначала подготовьте таблицы по шаблонам ниже. "
                "Имена и другие персональные данные учеников не нужны — используйте обезличенный student_id."
            )
            st.markdown("**1. Результаты учеников — results.csv**")
            st.caption("Одна строка = один ответ ученика на одно задание. correct: 1 — верно, 0 — неверно.")
            st.download_button(
                "Скачать шаблон results.csv",
                "student_id,school_id,textbook,lang,area,prior_score,item_id,correct\nS001,School_01,Учебник А,ru,urban,0.65,Q001,1\n",
                file_name="results_template.csv", mime="text/csv", key="tpl_results"
            )
            st.markdown("**2. Справочник заданий — items.csv**")
            st.caption("Для каждого item_id укажите текст задания и код темы.")
            st.download_button(
                "Скачать шаблон items.csv",
                "item_id,item_text,topic_code\nQ001,Пример задания,T01\n",
                file_name="items_template.csv", mime="text/csv", key="tpl_items"
            )
            st.markdown("**3. Учебный план — plan.csv**")
            st.caption("Укажите название каждой темы, количество часов и число предварительных тем.")
            st.download_button(
                "Скачать шаблон plan.csv",
                "topic_code,topic_name,hours,prereq_count\nT01,Пример темы,4,0\n",
                file_name="plan_template.csv", mime="text/csv", key="tpl_plan"
            )
            st.info("Для надёжных выводов нужно не менее 30 учеников в анализируемой группе. "
                    "Шаблоны содержат только примерные строки — замените их своими обезличенными данными.")
            fr = st.file_uploader("Файл результатов", type="csv", key="fr")
            fi = st.file_uploader("Файл заданий", type="csv", key="fi")
            fp = st.file_uploader("Файл учебного плана", type="csv", key="fp")
            ready = all(x is not None for x in (fr, fi, fp))
            if ready:
                st.caption("Все три файла выбраны. Нажмите кнопку, чтобы проверить структуру и данные.")
            if ready and st.button("Проверить данные и открыть анализ", type="primary"):
                try:
                    r, i, pl = pd.read_csv(fr), pd.read_csv(fi), pd.read_csv(fp)
                    errs = core.validate(r, i, pl)
                    for label, frame in (("results.csv", r), ("items.csv", i), ("plan.csv", pl)):
                        if frame.empty:
                            errs.append(f"Файл {label} пустой.")
                    required = {
                        "results.csv": (r, core.REQUIRED["results"]),
                        "items.csv": (i, core.REQUIRED["items"]),
                        "plan.csv": (pl, core.REQUIRED["plan"]),
                    }
                    for label, (frame, columns) in required.items():
                        if all(col in frame.columns for col in columns):
                            empty_cols = [col for col in columns if frame[col].isna().any()]
                            if empty_cols:
                                errs.append(f"В файле {label} есть пустые значения в столбцах: {', '.join(empty_cols)}.")
                    if "prior_score" in r.columns and pd.to_numeric(r["prior_score"], errors="coerce").isna().any():
                        errs.append("В results.csv столбец prior_score должен содержать только числа.")
                    if "hours" in pl.columns and pd.to_numeric(pl["hours"], errors="coerce").isna().any():
                        errs.append("В plan.csv столбец hours должен содержать только числа.")
                    if errs:
                        st.error("Проверка не пройдена. Исправьте пункты ниже и загрузите файлы снова:")
                        for e in errs:
                            st.write(f"• {e}")
                    else:
                        st.success(
                            f"Проверка пройдена: {r['student_id'].nunique()} учеников, "
                            f"{r['school_id'].nunique()} школ, {i['item_id'].nunique()} заданий, "
                            f"{pl['topic_code'].nunique()} тем."
                        )
                        st.session_state.data = (r, i, pl)
                        st.session_state.synthetic = False
                        go_to("Обзор тем")
                except Exception as e:
                    st.error(f"Не удалось прочитать CSV. Проверьте, что файлы сохранены в формате CSV UTF-8. "
                             f"Подробность: {type(e).__name__}: {e}")
        st.markdown('<p class="trust">Работает без интернета и ключа API · казахский и русский</p>',
                    unsafe_allow_html=True)
    with right:
        st.markdown(f"""
<div class="visual">
  <div class="shotcard"><img src="app/static/hero_overview.jpg" alt="Экран «Что провалено»: освоение тем с интервалами"></div>
  <div class="chip c1"><span class="dot red"></span><div><b>{n_weak} темы</b> ниже цели 60%</div></div>
  <div class="chip c2"><div class="cl">Причина найдена</div><div><b>Учебник</b> · {tb_name}</div></div>
</div>""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="sec">
  <span class="kicker">Проблема</span>
  <h2 class="h">Решения принимают на глаз, а результат никто не проверяет</h2>
  <div class="bignums">
    <div class="bn"><div class="v red">414</div><div class="l">баллов по математике в PISA-2025: на 12 меньше, чем в 2022. Среднее по ОЭСР 463</div><div class="s">ОЭСР, Forbes.kz</div></div>
    <div class="bn"><div class="v">8 000+</div><div class="l">школ в Казахстане выбирают учебники и делят часы между темами</div><div class="s">Бюро национальной статистики</div></div>
    <div class="bn"><div class="v">530</div><div class="l">школ в Жамбылской области: наш первый рынок</div><div class="s">baq-orda.kz, 28.08.2026</div></div>
  </div>
  <div class="callout">Методист видит общий балл, но не видит, в какой теме пробел и виноват ли в нём учебник.</div>
</div>

<div class="sec">
  <span class="kicker">Пример</span>
  <h2 class="h">Средний балл обманывает</h2>
  <div class="flip">
    <div class="q">Какой учебник даёт лучший результат?</div>
    <div class="row"><span class="lbl">По средним баллам</span>
      <span class="ans wrong">{raw['textbook']}, {pct(raw['mean'])}</span>
      <span class="pen">его чаще берут сильные городские школы</span></div>
    <div class="row"><span class="lbl">С поправкой на состав школ</span>
      <span class="ans">{adj['textbook']}, {pct(adj['mean'])}</span>
      <span class="pen">а у «{raw['textbook']}» {pct(adj_of_raw)}</span></div>
    <div class="src">Синтетические демо-данные: {n_txt} учеников, {demo['meta']['school_id'].nunique()} школ, математика 6 класса.</div>
  </div>
</div>

<div class="sec dark">
  <span class="kicker">Как работает</span>
  <h2 class="h">От результатов теста до решения методсовета</h2>
  <div class="steps">
    <div class="st"><div class="n">1</div><div class="t">Загрузите результаты</div><div class="d">Три таблицы CSV: ответы учеников, задания, учебный план. Без имён.</div></div>
    <div class="st"><div class="n">2</div><div class="t">ИИ размечает задания</div><div class="d">Своя модель относит каждое задание к теме программы: {q_ok} из {q_n} верно на новых заданиях.</div></div>
    <div class="st"><div class="n">3</div><div class="t">Система ищет причину</div><div class="d">Трудная тема, учебник, отдельные школы или плохое задание в тесте.</div></div>
    <div class="st"><div class="n">4</div><div class="t">Готовое решение</div><div class="d">Сравнение учебников с поправкой на состав школ, новый план часов и записка на двух языках.</div></div>
  </div>
</div>

<div class="sec">
  <span class="kicker">Тарифы</span>
  <h2 class="h">Каждый получает своё</h2>
  <div class="plans">
    <div class="pl"><div class="who">Учитель</div><div class="pr">15 000 ₸<span>/год</span></div><div class="d">Свои классы: какие темы провалены и что повторить.</div></div>
    <div class="pl main"><div class="who">Школа</div><div class="pr">150 000 ₸<span>/год</span></div><div class="d">Все учителя, сравнение учебников, план часов, записка для методсовета.</div></div>
    <div class="pl"><div class="who">Район или город</div><div class="pr">1 500 000 ₸<span>/год</span></div><div class="d">Все школы района, слабые школы и темы, решения по закупке учебников.</div></div>
  </div>
</div>

<div class="sec">
  <span class="kicker">Вопросы</span>
  <h2 class="h">Частые вопросы</h2>
  <div class="faq">
    <details><summary>Нужен ли интернет или платный ИИ?</summary><p>Нет. Модель разметки обучена заранее и работает на месте, записка строится по шаблону. Ключ API можно подключить по желанию.</p></details>
    <details><summary>Что с данными учеников?</summary><p>Имена не нужны: достаточно обезличенных ключей. Без ключа API расчёт идёт только в приложении. Демо на этом сайте открытое, поэтому реальные данные учеников сюда загружать не нужно: для пилота приложение можно установить на сервер школы или управления образования.</p></details>
    <details><summary>Цифры в демо настоящие?</summary><p>Нет, демо работает на синтетических данных, чтобы показать метод. Проверка на реальных результатах СОР — цель пилота.</p></details>
    <details><summary>Чем это отличается от электронного журнала?</summary><p>Журнал хранит оценки. «Дәлел» разбирает результаты по темам и объясняет причину: учебник, тема, школа или задание.</p></details>
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown('<div class="closer"><h2 class="h">Попробуйте на демо-данных</h2><p>Нажмите «Открыть демо» вверху страницы или выберите раздел в меню слева.</p></div>',
                unsafe_allow_html=True)
    st.stop()


if st.session_state.data is None:
    st.info("Сначала откройте демо или загрузите данные на главной странице.")
    if st.button("Открыть демо", type="primary"):
        st.session_state.data = load_demo()
        st.session_state.synthetic = True
        st.rerun()
    st.stop()

results, items, plan = st.session_state.data
try:
    A = run_analysis(results, items, plan, target)
except Exception:
    st.error("Не получилось посчитать эти данные. Проверьте, что дроби записаны через точку, "
             "нет пустых ячеек в prior_score и hours, а файл сохранён с разделителем «,». "
             "Демо-данные открываются на главной странице.")
    st.stop()
meta = A["meta"]
names = plan.set_index("topic_code")["topic_name"].to_dict()
diag = {d["topic_code"]: d for d in A["diagnoses"]}


# ---------- обзор тем ----------

if page == "Обзор тем":
    st.markdown("## Где нужно усилить обучение")
    lead("Сначала смотрите на темы ниже целевого уровня. Нажмите «Открыть», чтобы увидеть возможную причину, данные и рекомендуемое действие.")
    worst = A["mastery"].sort_values("mastery").iloc[0]
    takeaway(f"<b>{len(A['weak'])} из {len(plan)}</b> тем ниже цели {pct(target)}. Слабее всего «{names[worst['topic_code']]}»: "
             f"задания по ней решают верно только <b>{pct(worst['mastery'])}</b> учеников, то есть примерно "
             f"{round(worst['mastery'] * 10)} из 10.")
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
            hovertemplate="%{y}<br>решают верно %{x:.0%}<br>скорее всего от %{customdata[0]:.0%} до %{customdata[1]:.0%}<extra></extra>"))
        fig.add_trace(go.Scatter(   # подпись справа от интервала, чтобы не налезала на линию
            x=d["hi"], y=d["topic_name"], mode="text", text=[f"  <b>{pct(v)}</b>" for v in d["mastery"]],
            textposition="middle right", textfont=dict(color=col, size=13), cliponaxis=False, hoverinfo="skip"))
    lo_x = max(0.0, min(m["lo"].min(), target) - 0.08)
    fig.update_layout(showlegend=False, margin=dict(l=10, r=40, t=30, b=10),
                      xaxis=dict(range=[lo_x, 1.0], tickformat=".0%", showgrid=True, zeroline=False),
                      yaxis=dict(categoryorder="array", categoryarray=list(m["topic_name"])[::-1],
                                 showgrid=False, tickfont=dict(size=13)))
    chart(fig, 44 * len(m) + 70)
    howto(("dot", "точка: доля правильных ответов по теме"),
          ("red", "красные темы ниже цели"), ("goal", f"пунктир: целевой уровень {pct(target)}"))
    with st.expander("Как понимать график и 95% интервал"):
        st.markdown(
            "- **Точка** показывает наблюдаемую долю правильных ответов по теме.\n"
            "- **Горизонтальная линия** показывает 95% интервал неопределённости: диапазон возможных значений с учётом того, что ученики сгруппированы по школам.\n"
            "- **Чем короче линия**, тем точнее оценка. Длинная линия означает, что данных для точного вывода меньше.\n"
            "- **Красный пунктир** — выбранная цель. Если точка левее линии, тема ниже целевого уровня.\n\n"
            "Интервал не означает, что 95% учеников набрали такой результат; он описывает неопределённость общей оценки."
        )
    st.markdown(f'<div class="note">В расчёте {len(sub_meta)} учеников, {sub_meta["school_id"].nunique()} школ.</div>',
                unsafe_allow_html=True)

    st.markdown("#### Темы ниже цели")
    if area != "все" or lang != "все":
        st.markdown('<div class="note">Список и причины посчитаны по всем ученикам, фильтр меняет только график выше.</div>',
                    unsafe_allow_html=True)
    weak_box = st.container(key="weaklist")
    for d in A["diagnoses"]:
        cc = weak_box.columns([3, 2, 1], vertical_alignment="center")
        gap = (target - d["mastery"]) * 100
        cc[0].markdown(f'<div class="wl"><b>{names[d["topic_code"]]}</b><div class="bar"><i style="width:{d["mastery"] * 100:.0f}%"></i>'
                       f'<u style="left:{target * 100:.0f}%"></u></div><span>{pct(d["mastery"])} · не хватает {gap:.0f} пунктов до цели</span></div>',
                       unsafe_allow_html=True)
        cc[1].markdown(f'<span class="cause">{core.CAUSES.get(d["cause"], ("Недостаточно данных",))[0]}</span>',
                       unsafe_allow_html=True)
        if cc[2].button("Открыть", key=f"open_{d['topic_code']}"):
            st.session_state.topic = d["topic_code"]
            go_to("Тема")

    flagged = A["items"][A["items"]["flagged"]]
    if len(flagged):
        with st.expander(f"Подозрительные задания (не отличают сильных учеников от слабых): {len(flagged)}"):
            st.dataframe(flagged[["item_id", "topic_code", "item_text", "p_correct", "discrimination"]]
                         .rename(columns={"item_id": "Задание", "topic_code": "Тема", "item_text": "Текст",
                                          "p_correct": "Доля верных", "discrimination": "Отличает сильных от слабых"}),
                         hide_index=True, use_container_width=True)


# ---------- учебники ----------

elif page == "Учебники":
    st.markdown("## Какой учебник работает лучше")
    lead("Простое среднее нечестно: сильные школы чаще выбирают один учебник. Режим «С поправками» сравнивает учебники на одинаковых учениках.")
    mode = st.segmented_control("Режим сравнения", ["Простое среднее", "С поправками"], default="Простое среднее",
                                key="tb_mode") or "Простое среднее"
    adj = mode == "С поправками"
    means = A["adj_means"] if adj else A["raw_means"]
    pairs = A["adj_pairs"] if adj else A["raw_pairs"]
    best = means.sort_values("mean").iloc[-1]["textbook"]

    if adj:
        takeaway(f"На одинаковых учениках лучший результат у <b>«{best}»</b>: {pct(means.set_index('textbook').loc[best, 'mean'])}.")
    else:
        takeaway(f"По простому среднему впереди «{best}». Но это может быть заслуга сильных школ, а не учебника. "
                 "Переключите на <b>«С поправками»</b>.")
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
            hovertemplate=(f"{r.textbook}: %{{x:.1%}}<br>скорее всего от {r.lo:.1%} до {r.hi:.1%}"
                           f"<br>учеников {r.n_students}, школ {r.n_schools}<extra></extra>")))
    lo = min(A["raw_means"]["lo"].min(), A["adj_means"]["lo"].min()) - 0.02
    hi = max(A["raw_means"]["hi"].max(), A["adj_means"]["hi"].max()) + 0.02
    fig.update_layout(showlegend=False, margin=dict(l=10, r=20, t=20, b=10),
                      xaxis=dict(range=[lo, hi], tickformat=".0%", title="средний результат теста"),
                      yaxis=dict(categoryorder="array", categoryarray=sorted(means["textbook"])[::-1],
                                 showgrid=True, tickfont=dict(size=14)))
    chart(fig, 300)
    howto(("dot", "точка: средний результат по учебнику; полоска: где почти наверняка лежит настоящий результат"),
          ("goal", "шкала одна в обоих режимах: переключите и посмотрите, как сдвинутся точки"))

    if adj:
        st.markdown(f'<div class="verdict">С поправкой на прошлый балл, тип местности и язык обучения '
                    f'лучший результат у «{best}».</div>', unsafe_allow_html=True)
        st.markdown('<div class="note">Учебники сравниваются на одном и том же «среднем» ученике. '
                    'Интервалы учитывают, что ученики одной школы похожи друг на друга.</div>', unsafe_allow_html=True)

    st.markdown("#### Попарно: чья разница надёжна")
    cards = ""
    for r in pairs.itertuples():
        better, worse = (r.b, r.a) if r.diff_b_minus_a > 0 else (r.a, r.b)
        ok = bool(r.confirmed)
        dtxt = f"{abs(r.diff_b_minus_a) * 100:.1f}".replace(".", ",")
        cards += (f'<div class="pc{" ok" if ok else ""}"><div class="pt">«{better}» лучше «{worse}»</div>'
                  f'<div class="pv">на {dtxt} пункта</div>'
                  f'<div class="pb">{"✓ разница надёжная" if ok else "≈ может быть случайностью"}</div></div>')
    st.markdown(f'<div class="pairs">{cards}</div>', unsafe_allow_html=True)
    st.markdown('<div class="note">«Надёжная» значит, что разница остаётся, даже если взять другие школы того же типа '
                '(95% интервал не пересекает ноль).</div>', unsafe_allow_html=True)

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
    howto(("size", "чем больше кружок, тем больше учеников"), ("goal", "серая нижняя строка: общее среднее без поправки"))
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
    kpi(c[1], f"{pct(mrow['lo'])}–{pct(mrow['hi'])}", "надёжный диапазон")
    kpi(c[2], pct(target), "цель")
    st.write("")

    if code in diag:
        d = diag[code]
        title, action = core.CAUSES.get(d["cause"], ("Недостаточно данных", "Собрать больше данных."))
        st.markdown(f'''<div class="diag"><span class="cause">{title}</span>
<div class="drow"><span class="dk">Почему</span><span>{d['details']}</span></div>
<div class="drow"><span class="dk">Что делать</span><span>{action}</span></div></div>''', unsafe_allow_html=True)
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
                text=[f"{r.effect * 100:+.0f} пунктов"], textposition="top center", textfont=dict(color=col, size=12),
                cliponaxis=False, hovertemplate=f"{r.textbook}: %{{x:+.1f}} пунктов<extra></extra>"))
        fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=24, b=10),
                          xaxis=dict(range=[-span, span], title="пунктов выше или ниже других учебников",
                                     zeroline=False),
                          yaxis=dict(categoryorder="array", categoryarray=sorted(eff["textbook"])[::-1],
                                     tickfont=dict(size=13)))
        chart(fig, 250)
    with t2:
        st.markdown("##### Какие школы отстают")
        sch = core.school_topic_effect(sc, meta, code)
        sch = sch.assign(**{"Отстаёт от района, пунктов": (sch["shrunk"] * 100).round(1), "Освоение": (sch["score"] * 100).round(0)})
        sch["Статус"] = [("мало учеников" if n < 20 else "ниже ожидаемого" if s <= -core.SCHOOL_GAP else "")
                         for n, s in zip(sch["n"], sch["shrunk"])]
        st.dataframe(sch[["school_id", "n", "Освоение", "Отстаёт от района, пунктов", "Статус"]].head(10)
                     .rename(columns={"school_id": "Школа", "n": "Учеников"}),
                     hide_index=True, use_container_width=True, height=250)

    st.markdown("##### Задания темы")
    ti = A["items"][A["items"]["topic_code"] == code].copy()
    ti["Статус"] = ["проверить задание" if f else "" for f in ti["flagged"]]
    ti["Доля верных"] = (ti["p_correct"] * 100).round(0)
    ti["Отличает сильных от слабых"] = ti["discrimination"].round(2)
    st.dataframe(ti[["item_id", "item_text", "Доля верных", "Отличает сильных от слабых", "Статус"]]
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
         "отдают темы с запасом над целью не меньше 10 пунктов Изменение темы не больше 20% её часов.")
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
    lead("Текст собирается только из рассчитанных чисел, а числа в нём автоматически сверяются с расчётом.")
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
        st.session_state.memo_target = target

    if "memo" in st.session_state and st.session_state.get("memo_target") != target:
        del st.session_state["memo"]
        st.info("Цель изменилась. Соберите записку заново.")
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
