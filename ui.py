"""Visual helpers: CSS theme, radar chart (SVG), prerequisite graph (DOT)."""
import math

from data_bank import PREREQS, SUBJECTS

CSS = """<style>
#MainMenu,footer,[data-testid=stToolbar],[data-testid=stDecoration],[data-testid=stStatusWidget]{display:none!important}
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Inter:wght@400;500;600&display=swap');
html,body,.stApp{font-family:'Inter',sans-serif}
.stApp{background:#FBF8F1;color:#1B2B24}
.block-container{padding-top:2rem;max-width:1180px}
h1,h2,h3,h4,.hero h1{font-family:'Fraunces',Georgia,serif!important;color:#14352B;font-weight:600!important}
[data-testid=stSidebar]{background:#12342A}
[data-testid=stSidebar] h1,[data-testid=stSidebar] h2,[data-testid=stSidebar] h3,[data-testid=stSidebar] label p,
[data-testid=stSidebar] [data-testid=stCaptionContainer],[data-testid=stSidebar] .stMarkdown p{color:#DCE9E0!important}
[data-testid=stSidebar] div[role=radiogroup]{gap:2px}
[data-testid=stSidebar] div[role=radiogroup] label{padding:10px 14px;border-radius:12px;width:100%;cursor:pointer}
[data-testid=stSidebar] div[role=radiogroup] label>div:first-child{display:none}
[data-testid=stSidebar] div[role=radiogroup] label:hover{background:rgba(255,255,255,.07)}
[data-testid=stSidebar] div[role=radiogroup] label:has(input:checked){background:rgba(255,255,255,.13)}
button[kind=primary],[data-testid=stBaseButton-primary]{background:#14532D!important;border:none!important;border-radius:999px!important;color:#fff!important}
.stButton>button{border-radius:999px}
[data-testid=stVerticalBlockBorderWrapper]{border-radius:18px!important;border-color:#E7E1D3!important}
.hero{background:linear-gradient(120deg,#12342A,#1F6B4A);padding:26px 30px;border-radius:20px;color:#F6F1E4;margin-bottom:14px}
.hero h1{margin:0;font-size:2.1rem;color:#F6F1E4!important}.hero p{margin:6px 0 0;opacity:.9}
.card{background:#fff;border:1px solid #E7E1D3;border-radius:18px;padding:16px 18px}
.kpi{font-size:1.9rem;font-weight:600;line-height:1.1;font-family:'Fraunces',Georgia,serif;color:#14352B}
.kpi-l{color:#6B7A72;font-size:.75rem;text-transform:uppercase;letter-spacing:.07em}
.bar{background:#E7E1D3;border-radius:99px;height:10px;overflow:hidden}.bar>div{height:100%;background:linear-gradient(90deg,#14532D,#4CAF7A)}
.pill{display:inline-block;border:1px solid #D9D2BF;border-radius:999px;padding:6px 14px;margin:0 8px 8px 0;font-size:.85rem;background:#FFFDF8}
.badge{display:inline-block;background:#E6F0E8;border:1px solid #A9CBB3;color:#14352B;border-radius:99px;padding:5px 14px;margin:3px;font-size:.85rem}
.badge.off{background:#F1ECDF;border-color:#E7E1D3;color:#8A948E;opacity:.7}
.feat{background:#fff;border:1px solid #E7E1D3;border-radius:16px;padding:14px;border-left:4px solid #14532D;height:100%;color:#1B2B24}
.sec{font-family:'Fraunces',Georgia,serif;letter-spacing:.1em;text-transform:uppercase;color:#4B5E54;font-size:.85rem;margin:24px 0 10px}
</style>"""


def kpi(label, value, sub=""):
    return f'<div class="card"><div class="kpi-l">{label}</div><div class="kpi">{value}</div><div style="color:#6B7A72;font-size:.8rem">{sub}</div></div>'


def bar(pct):
    return f'<div class="bar"><div style="width:{max(2, min(100, pct))}%"></div></div>'


def radar_svg(vals):
    """vals: list of (label, 0-100)."""
    n, cx, cy, R = len(vals), 190, 175, 105

    def pt(i, r):
        a = -math.pi / 2 + 2 * math.pi * i / n
        return cx + r * math.cos(a), cy + r * math.sin(a)

    rings = "".join('<polygon points="%s" fill="none" stroke="#D9D2BF" stroke-width="0.8"/>' %
                    " ".join("%.1f,%.1f" % pt(i, R * k / 4) for i in range(n)) for k in (1, 2, 3, 4))
    axes = "".join('<line x1="%d" y1="%d" x2="%.1f" y2="%.1f" stroke="#D9D2BF" stroke-width="0.8"/>' %
                   ((cx, cy) + pt(i, R)) for i in range(n))
    poly = " ".join("%.1f,%.1f" % pt(i, R * v / 100) for i, (_, v) in enumerate(vals))
    labels = ""
    for i, (lab, _) in enumerate(vals):
        x, y = pt(i, R + 14)
        anc = "middle" if abs(x - cx) < 12 else "start" if x > cx else "end"
        labels += f'<text x="{x:.1f}" y="{y:.1f}" fill="#4B5E54" font-size="9" text-anchor="{anc}">{lab}</text>'
    return (f'<svg viewBox="0 0 380 350" style="width:100%;max-width:520px">{rings}{axes}'
            f'<polygon points="{poly}" fill="rgba(20,83,45,.28)" stroke="#14532D" stroke-width="2"/>{labels}</svg>')


def graph_dot(info, subjects):
    def color(t):
        if t not in info:
            return "#64748b"
        m = info[t]["mastery"]
        return "#ef4444" if m < 0.5 else "#f59e0b" if m < 0.8 else "#22c55e"

    lines = ['digraph G {rankdir=LR; bgcolor="transparent"; node [shape=box, style="rounded,filled", '
             'fontcolor=white, fontname="Helvetica", fontsize=11, color="#0f172a"]; edge [color="#94a3b8"];']
    for s in subjects:
        for t in SUBJECTS[s]:
            lines.append(f'"{t}" [fillcolor="{color(t)}"];')
            for p in PREREQS.get(t, []):
                if p in SUBJECTS[s] and PREREQS.get(t, [None])[0] == p:
                    lines.append(f'"{p}" -> "{t}";')
    lines.append("}")
    return "\n".join(lines)


SIMPLE_CSS = """<style>
.stApp{background:radial-gradient(circle at 50% 0,#cfe9d8 0,transparent 52%),#FBF8F1!important}
[data-testid=stHeader]{background:transparent}
.block-container{max-width:440px!important;margin-left:auto!important;margin-right:auto!important;padding:7vh 1rem 3rem!important}
.crest{width:84px;height:84px;margin:0 auto 14px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:2.4rem;background:linear-gradient(145deg,#14532D,#3aa874);box-shadow:0 10px 26px rgba(20,83,45,.35)}
.ttl{font-family:'Fraunces',Georgia,serif!important;text-align:center;font-size:2.4rem!important;margin:0!important;color:#14352B!important}
.tag{text-align:center;color:#5b6d63;margin:4px 0 22px;font-size:1.05rem}
[data-testid="stForm"]{background:#fff;border:1px solid #E7E1D3;border-radius:24px;padding:26px 24px 18px;box-shadow:0 18px 44px rgba(20,53,43,.12)}
.ftitle{font-family:'Fraunces',Georgia,serif;font-size:1.5rem;color:#14352B;margin:0 0 2px}
.fsub{color:#6b7a72;margin:0 0 10px}
[data-testid^="stBaseButton-primary"]{width:100%;background:#14532D!important;color:#fff!important;border:none!important;border-radius:999px!important;padding:.6rem 1rem;font-weight:600}
[data-testid="stBaseButton-secondary"]{width:100%;background:transparent;border:none;color:#14532D;font-weight:600;text-decoration:underline}
.frow{background:#fff;border:1px solid #E7E1D3;border-radius:16px;padding:12px 16px;margin-top:10px;display:flex;gap:14px;align-items:center}
.frow .ic{font-size:1.5rem}.frow b{display:block;color:#14352B}.frow span{color:#6b7a72;font-size:.88rem}
</style>"""


LOGIN_CSS = """<style>
.stApp{background:#061712!important}
[data-testid=stHeader],[data-testid=stSidebar]{display:none!important}
.block-container{padding:0!important;max-width:100%!important}
[data-testid=stVerticalBlock]{gap:0!important}
iframe{display:block;border:0}
</style>"""