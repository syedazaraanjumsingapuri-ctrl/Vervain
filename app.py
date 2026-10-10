
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

import auth
from agent import rule_based_plan, run_agent, tutor_answer
from data_bank import (DEMO1, DEMO_IMPROVED, DEMO_STUCK, NOTES, QUESTIONS, RESOURCES, SUBJECTS,
                       TOPIC_SUBJECT, PREREQS, make_answers)
from engine import (compute_mastery, depth, is_greeting, misconceptions, offline_answer,
                    predict_resource_need, recommend, retrieve)
from ui import CSS, bar, graph_dot, kpi, radar_svg

st.set_page_config(page_title="VERVAIN", page_icon="📚", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
ICON = {"weak": "🔴 weak", "medium": "🟡 medium", "strong": "🟢 strong"}
# Resource types are different from mastery labels. Keep them separate so a
# resource type such as "video" can never cause KeyError in Recommendations.
RESOURCE_ICON = {
    "video": "🎥", "article": "📄", "notes": "📝", "course": "🎓",
    "exercise": "💻", "practice": "✍️", "challenge": "🏆",
    "documentation": "📚", "tutorial": "📝", "book": "📖",
    "study resource": "📚", "resource": "📚",
}


def resource_icon(resource):
    """Choose an icon from the actual resource, not the mastery label."""
    title = str(resource.get("title", "")).lower()
    kind = str(resource.get("type", "resource")).strip().lower()
    if "challenge" in title:
        return "🏆"
    if "note" in title:
        return "📝"
    if "practice" in title or "problem" in title:
        return "✍️"
    return RESOURCE_ICON.get(kind, "📚")


def make_recommendations_consistent_with_quiz_scores(recommendations, topic_info, resources):
    """Prefer practice when measured quiz accuracy conflicts with high mastery."""
    fixed = []
    for original in recommendations:
        rec = dict(original)
        topic = rec.get("topic")
        stats = topic_info.get(topic, {})
        score = stats.get("quiz_score")
        if score is not None and score < 0.70:
            topic_resources = [r for r in resources if r.get("topic") == topic]
            practice = [
                r for r in topic_resources
                if "practice" in str(r.get("title", "")).lower()
                or str(r.get("type", "")).lower() in {"practice", "exercise"}
            ]
            if practice:
                # Prefer intermediate practice for a learner who needs reinforcement.
                chosen = next(
                    (r for r in practice if str(r.get("difficulty", "")).lower() == "intermediate"),
                    practice[0],
                )
                rec["resource"] = chosen
                rec["reason"] = (
                    f"Your quiz accuracy is {score:.0%}, so practice is a better next step "
                    f"than an advanced challenge. Work through similar questions, then retake the quiz."
                )
                if score < 0.50 or float(stats.get("mastery", 0)) < 0.50:
                    rec["flag"] = "stuck"
        fixed.append(rec)
    return fixed


@st.cache_resource
def _load_local_study_model():
    """Load the model beside app.py; return None if missing or incompatible."""
    model_path = Path(__file__).resolve().with_name("study_recommender.pkl")
    if not model_path.exists() or model_path.stat().st_size == 0:
        return None, f"Model file not found or empty: {model_path}"
    try:
        return joblib.load(model_path), None
    except Exception as exc:
        return None, f"Could not load study_recommender.pkl: {type(exc).__name__}: {exc}"


def _predict_study_need(quiz_score, mastery):
    """Return (prediction, error); model expects quiz_score and mastery columns."""
    model, error = _load_local_study_model()
    if model is None:
        return None, error
    try:
        features = pd.DataFrame(
            [{"quiz_score": float(quiz_score), "mastery": float(mastery)}],
            columns=["quiz_score", "mastery"],
        )
        prediction = int(model.predict(features)[0])
        return prediction, None
    except Exception as exc:
        return None, f"Prediction failed: {type(exc).__name__}: {exc}"
QBYID = {q["id"]: q for q in QUESTIONS}
NAMES = ["Dashboard", "Take a quiz", "Quiz history", "Recommendations", "Study plan", "Skill map", "AI Tutor", "Progress"]
GROUPS = {"Programming": ["Python", "Java", "C"], "Databases": ["SQL"], "Web Development": ["Web Development"],
          "Computer Science": ["DSA"]}
DESC = {"Python": "Syntax, control flow and loops.", "Java": "Types, classes and inheritance.",
        "C": "Arrays, pointers and functions.", "SQL": "Queries, joins and aggregation.",
        "Web Development": "HTML structure, CSS styling and JavaScript.",
        "DSA": "Complexity, linear structures and sorting."}
ss = st.session_state
for k, v in {"answers": [], "snapshots": [], "round": 0, "usage": [], "subjects": ["Python", "SQL", "DSA"],
             "name": "", "user": None, "cur": None, "fb": None, "chat": [], "focus": None}.items():
    ss.setdefault(k, v)


def snapshot():
    ss.snapshots.append({t: round(s["mastery"] * 100, 1) for t, s in compute_mastery(ss.answers).items()})


def add_profile(p):
    ss.answers = ss.answers + make_answers(p)
    snapshot()


def load_demo1():
    ss.answers, ss.snapshots, ss.usage, ss.cur, ss.fb = [], [], [], None, None
    ss.subjects = ["Python", "SQL", "DSA"]
    add_profile(DEMO1)


def add_improved():
    add_profile(DEMO_IMPROVED)


def add_stuck():
    ss.usage = ["python-loops-1", "python-loops-2"]
    add_profile(DEMO_STUCK)


def reset():
    ss.answers, ss.snapshots, ss.usage, ss.cur, ss.fb = [], [], [], None, None


def mark_used(rid):
    if rid not in ss.usage:
        ss.usage = ss.usage + [rid]


def start_quiz(s):
    ss.focus, ss.cur, ss.fb = s, None, None
    if s not in ss.subjects:
        ss.subjects = ss.subjects + [s]


def leave_quiz():
    ss.focus, ss.cur, ss.fb = None, None, None



# ---------------- register / login ----------------
if ss.user is None:
    # Login-page-only styling. The dashboard and all other features remain unchanged.
    st.markdown("""
    <style>
    .stApp:has(.login-hero-panel) { background: #F7F8F4; }
    .block-container:has(.login-hero-panel) {
        max-width: 1200px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .login-hero-panel {
        box-sizing: border-box;
        min-height: 570px;
        height: 100%;
        padding: 42px 32px;
        border-radius: 22px;
        color: #FFFFFF;
        background: linear-gradient(145deg, #12342A, #1F6B4A);
        box-shadow: 0 12px 40px rgba(18,52,42,.12);
    }
    .login-brand {
        color: #D4EBDD;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
        margin-bottom: 25px;
    }
    .login-hero-panel h1 {
        color: #FFFFFF !important;
        font-size: clamp(36px, 4vw, 52px) !important;
        font-weight: 800 !important;
        line-height: 1.1;
        margin: 0 0 14px;
    }
    .login-tagline { color: #E0F1E5; font-size: 20px; font-weight: 600; margin-bottom: 12px; }
    .login-description { color: #D4E5D9; font-size: 14px; line-height: 1.8; }
    .login-illustration {
        display: flex; align-items: center; justify-content: center; gap: 18px;
        margin: 26px 0; padding: 22px 10px;
        background: rgba(255,255,255,.07);
        border: 1px solid rgba(255,255,255,.12); border-radius: 18px;
    }
    .login-emoji { font-size: 42px; }
    .login-book { font-size: 34px; padding: 12px; border-radius: 14px; background: rgba(255,255,255,.12); }
    .login-feature-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .login-feature {
        padding: 12px; border-radius: 12px; background: rgba(255,255,255,.08);
        border: 1px solid rgba(255,255,255,.12); color: #F1F7F2;
        font-size: 12px; line-height: 1.6;
    }
    .login-welcome { text-align: center; color: #12342A; font-size: 30px; font-weight: 750; margin: 22px 0 5px; }
    .login-subtitle { text-align: center; color: #718078; font-size: 14px; margin-bottom: 22px; }
    @media (max-width: 700px) {
        .login-hero-panel { min-height: auto; padding: 30px 22px; }
    }
    </style>
    """, unsafe_allow_html=True)

    left_col, right_col = st.columns([1.05, 1], gap="large")

    with left_col:
        st.markdown("""
        <div class="login-hero-panel">
          <div class="login-brand">YOUR PERSONAL LEARNING COMPANION</div>
          <h1>AI TUTOR</h1>
          <div class="login-tagline">Learn smarter. Grow every day.</div>
          <div class="login-description">
            Your learning journey, made personal. Discover what you know,
            strengthen what you don't, and build your skills one step at a time.
          </div>
          <div class="login-illustration">
            <span class="login-emoji">🧠</span>
            <span class="login-book">📚</span>
            <span class="login-emoji">🎯</span>
          </div>
          <div class="login-feature-grid">
            <div class="login-feature">🧠 <b>Smart learning</b><br>Understand concepts</div>
            <div class="login-feature">🎯 <b>Track mastery</b><br>See your progress</div>
            <div class="login-feature">📝 <b>Adaptive quizzes</b><br>Practice at your level</div>
            <div class="login-feature">🤖 <b>AI Tutor</b><br>Get learning support</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="login-welcome">Welcome!</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Sign in or create an account to continue.</div>', unsafe_allow_html=True)
        t_login, t_reg = st.tabs(["🔑 Login", "🆕 Register"])

        with t_login:
            lu = st.text_input("Username", key="lu")
            lp = st.text_input("Password", type="password", key="lp")
            if st.button("Login", type="primary", use_container_width=True):
                d = auth.login(lu, lp)
                if d:
                    ss.user, ss.name = d["username"], d["username"].title()
                    ss.subjects = d["subjects"]
                    ss.answers = d["answers"]
                    ss.snapshots = d["snapshots"]
                    ss.usage = d["usage"]
                    st.rerun()
                else:
                    st.error("Wrong username or password.")

        with t_reg:
            ru = st.text_input("Choose a username", key="ru")
            rp = st.text_input("Choose a password (4+ characters)", type="password", key="rp")
            rs = st.multiselect("Your subjects", list(SUBJECTS), default=["Python"], key="rs")
            if st.button("Create account", use_container_width=True):
                ok, msg = auth.register(ru, rp, rs)
                (st.success if ok else st.error)(msg + (" Now open the Login tab." if ok else ""))

    st.stop()

# ---------------- sidebar ----------------
with st.sidebar:
    st.markdown("### 🌱 VERVAIN")
    page = st.radio("Navigate", NAMES, label_visibility="collapsed")
    st.divider()
    st.markdown(f"👤 **{ss.name}**")
    if st.button("Logout"):
        ss.user = None
        ss.answers, ss.snapshots, ss.usage, ss.cur, ss.fb, ss.chat, ss.focus = [], [], [], None, None, [], None
        st.rerun()
    st.multiselect("Subjects", list(SUBJECTS), key="subjects")
    hours = st.slider("Study hours this week", 1, 20, 5)
    api_key = st.text_input("Anthropic API key (optional)", type="password")
    st.divider()
    st.caption("DEMO CONTROLS")
    st.button("1. Load sample quiz results", on_click=load_demo1)
    st.button("2a. Student studies and improves", on_click=add_improved)
    st.button("2b. Student studies but is stuck", on_click=add_stuck)
    st.button("Reset", on_click=reset)
    st.divider()
    st.multiselect("Resources already studied", [r["id"] for r in RESOURCES], key="usage")

# ---------------- compute ----------------
auth.save_progress(ss.user, ss.subjects, ss.answers, ss.snapshots, ss.usage)
info_all = compute_mastery(ss.answers)

# Filter mastery information to the selected subjects. Copy each stats
# dictionary so adding quiz performance does not mutate info_all.
info = {
    topic: dict(stats)
    for topic, stats in info_all.items()
    if TOPIC_SUBJECT.get(topic) in ss.subjects
}

# Add cumulative topic quiz accuracy separately from BKT mastery.
# recommend() accepts quiz_score as a fraction from 0 to 1.
for topic, stats in info.items():
    topic_answers = [
        answer for answer in ss.answers
        if answer.get("topic") == topic
    ]
    if topic_answers:
        stats["quiz_score"] = sum(
            bool(answer.get("correct", False))
            for answer in topic_answers
        ) / len(topic_answers)
    else:
        stats["quiz_score"] = None

miscs = [m for m in misconceptions(ss.answers) if m["topic"] in info]
recs = recommend(info, RESOURCES, ss.usage, miscs)
# If quiz accuracy is below 70%, do not send the learner straight to an
# advanced challenge just because BKT mastery is high.
recs = make_recommendations_consistent_with_quiz_scores(recs, info, RESOURCES)
topics_sel = [t for s in ss.subjects for t in SUBJECTS[s]]
n_ans, n_ok = len(ss.answers), sum(a["correct"] for a in ss.answers)
xp = n_ans * 10 + n_ok * 5 + len(ss.usage) * 20
level = xp // 100 + 1
streak = 0
for a in reversed(ss.answers):
    if not a["correct"]:
        break
    streak += 1
overall = round(100 * sum(s["mastery"] for s in info.values()) / len(info)) if info else 0
strong_n = sum(s["label"] == "strong" for s in info.values())
weak_n = sum(s["label"] == "weak" for s in info.values())

if page == "Dashboard":
    st.markdown(f'<div class="hero"><h1>Welcome back, {ss.name} 👋</h1><p>Level {level} learner · {xp} XP · '
                f'{streak}🔥 answer streak</p></div>', unsafe_allow_html=True)
    st.markdown(bar(xp % 100), unsafe_allow_html=True)
    st.write("")
    k = st.columns(4)
    k[0].markdown(kpi("Overall mastery", f"{overall}%", f"{len(info)} topics assessed"), unsafe_allow_html=True)
    k[1].markdown(kpi("Strong topics", f"🟢 {strong_n}", "mastery 80%+"), unsafe_allow_html=True)
    k[2].markdown(kpi("Weak topics", f"🔴 {weak_n}", "need attention"), unsafe_allow_html=True)
    k[3].markdown(kpi("Accuracy", f"{round(100*n_ok/n_ans) if n_ans else 0}%", f"{n_ans} questions answered"), unsafe_allow_html=True)
    st.write("")
else:
    st.markdown(f"## {page}")

# ---------------- dashboard ----------------
if page == "Dashboard":
    if not info:
        st.info("No results yet. Open **Adaptive Quiz** and answer a few questions, or load the demo student from the sidebar.")
    else:
        c1, c2 = st.columns([3, 2])
        with c1:
            st.subheader("Skill radar")
            st.markdown(radar_svg([(t.split(": ")[1][:16], round(info[t]["mastery"] * 100) if t in info else 0)
                                   for t in topics_sel]), unsafe_allow_html=True)
        with c2:
            st.subheader("Topic mastery")
            for t, s in sorted(info.items(), key=lambda x: x[1]["mastery"]):
                st.markdown(f"**{t}** · {ICON[s['label']]} · {round(s['mastery']*100)}%", unsafe_allow_html=True)
                st.markdown(bar(s["mastery"] * 100), unsafe_allow_html=True)
            st.subheader("Misconceptions found")
            for m in miscs[:5]:
                st.write(f"⚠️ **{m['topic'].split(': ')[1]}**: {m['misconception']} ({m['times']}x)")
            if not miscs:
                st.write("None detected 🎉")

# ---------------- adaptive quiz ----------------
if page == "Take a quiz":
    qt = SUBJECTS.get(ss.focus, [])
    if ss.focus:
        st.button("← All subjects", on_click=leave_quiz)
        st.caption("The next question is chosen by your weakest topic, and only after its prerequisites are understood.")

    def pick():
        """Choose an unanswered question from the weakest eligible topic.

        Never fall back to an already-answered question. Return None when the
        selected subject has no unanswered questions remaining.
        """
        seen = {a["qid"] for a in ss.answers}

        def m(t):
            return info_all[t]["mastery"] if t in info_all else 0.3

        def fresh_questions(t):
            return [q for q in QUESTIONS if q["topic"] == t and q["id"] not in seen]

        available_topics = [t for t in qt if fresh_questions(t)]
        if not available_topics:
            return None

        ready = [t for t in available_topics
                 if all(p in info_all and info_all[p]["mastery"] >= 0.5
                        for p in PREREQS.get(t, []))]
        pool = ready or available_topics
        t = min(pool, key=lambda x: (m(x), depth(x)))
        return fresh_questions(t)[0]["id"], t

    if ss.focus is None:
        for grp, subs in GROUPS.items():
            st.markdown(f'<div class="sec">{grp}</div>', unsafe_allow_html=True)
            cols = st.columns(2)
            for n, s in enumerate(subs):
                with cols[n % 2]:
                    with st.container(border=True):
                        st.markdown(f"### {s}")
                        st.caption(DESC[s])
                        st.markdown("".join(f'<span class="pill">{t.split(": ")[1]} · 2q</span>' for t in SUBJECTS[s]),
                                    unsafe_allow_html=True)
                        st.button("Full quiz", key=f"fq_{s}", type="primary", on_click=start_quiz, args=(s,))
    elif ss.fb:
        fb = ss.fb
        (st.success if fb["ok"] else st.error)(
            "✅ Correct! +15 XP" if fb["ok"] else f"❌ Not quite. The answer is: {fb['answer']}")
        if fb["tag"]:
            st.warning(f"Possible misconception: **{fb['tag']}**")
        st.info(f"📖 {fb['note']}")
        st.write(f"Mastery of **{fb['topic']}**: {fb['before']}% → **{fb['after']}%**")
        if st.button("Next question ➜", type="primary"):
            ss.fb, ss.cur = None, None
            st.rerun()
    else:
        if ss.cur is None:
            picked = pick()
            if picked is None:
                st.success("You've answered all available questions for this subject. Choose another subject to continue.")
                st.stop()
            ss.cur = picked[0]
        q = QBYID[ss.cur]
        st.markdown(f"#### {q['topic']} · {q['difficulty']}")
        st.markdown(f"##### {q['q']}")
        ch = st.radio("Choose one", q["options"], index=None, key=f"rq_{len(ss.answers)}", label_visibility="collapsed")
        if st.button("Check answer", type="primary") and ch is not None:
            idx = q["options"].index(ch)
            ok = idx == q["answer"]
            before = round(info_all.get(q["topic"], {"mastery": 0.3})["mastery"] * 100)
            ss.answers = ss.answers + [{"qid": q["id"], "topic": q["topic"], "correct": ok, "chosen": idx,
                                        "tag": None if ok else q["mis"].get(idx)}]
            snapshot()
            after = round(compute_mastery(ss.answers)[q["topic"]]["mastery"] * 100)
            ss.fb = {"ok": ok, "answer": q["options"][q["answer"]], "tag": None if ok else q["mis"].get(idx),
                     "note": NOTES[q["topic"]], "topic": q["topic"], "before": before, "after": after}
            st.rerun()

# ---------------- recommendations ----------------
if page == "Recommendations":
    st.caption("Recommendations combine mastery tracking, resource suggestions, and a prototype ML study-need prediction.")
    if info:
        st.markdown("### Study-need prediction")
        model_rows = []
        for topic, stats in info.items():
            topic_answers = [a for a in ss.answers if a.get("topic") == topic]
            if not topic_answers:
                continue
            quiz_score = 100 * sum(bool(a.get("correct")) for a in topic_answers) / len(topic_answers)
            prediction, prediction_error = _predict_study_need(quiz_score, stats["mastery"])
            model_rows.append({"topic": topic, "score": quiz_score, "mastery": stats["mastery"], "prediction": prediction, "error": prediction_error})
        available = [row for row in model_rows if row["prediction"] is not None]
        if available:
            for row in available:
                if int(row["prediction"]) == 1:
                    st.warning(f"**{row['topic']}** — model suggests extra practice. Quiz score: {row['score']:.0f}% · BKT mastery: {row['mastery']:.0%}")
                else:
                    st.success(f"**{row['topic']}** — model does not flag extra practice right now. Quiz score: {row['score']:.0f}% · BKT mastery: {row['mastery']:.0%}")
            st.caption("Prototype prediction only; validate with real student outcomes before treating it as reliable.")
        else:
            errors = [row["error"] for row in model_rows if row.get("error")]
            if errors:
                st.error("The ML model could not make a prediction.")
                st.code(errors[0])
            else:
                st.info("No topic has quiz answers yet. Answer a few quiz questions or load sample results to see study-need predictions.")
    else:
        st.info("Answer a few quiz questions or load sample results to see study-need predictions.")
    st.divider()
    if not recs:
        st.info("Recommendations appear after you answer questions." if not info else "All topics are strong 🎉")
    for i, rec in enumerate(recs, 1):
        r = rec["resource"]
        with st.container(border=True):
            if rec["flag"] == "no_material":
                st.error(f"**{rec['topic']}**: {rec['reason']}")
                continue
            stats = info.get(rec.get("topic"), {})
            score = stats.get("quiz_score")
            needs_attention = rec.get("flag") == "stuck" or (score is not None and score < 0.50)
            badge = " ⚠️ Needs attention" if needs_attention else ""
            st.markdown(f"### {i}. {rec['topic']}{badge}")
            score_text = f" · quiz accuracy {score:.0%}" if score is not None else ""
            st.markdown(f"[{r['title']}]({r['url']})  \n{resource_icon(r)} · mastery {rec['mastery']}%{score_text} · "
                        f"{r['type']} · {r['difficulty']} · {r['minutes']} min")
            st.write("**Why this fits:** " + rec["reason"])
            st.button("✅ Mark as studied (+20 XP)", key=f"used_{r['id']}", on_click=mark_used, args=(r["id"],))

# ---------------- study plan ----------------
if page == "Study plan":
    plan = rule_based_plan(recs, hours)
    total = sum(it["minutes"] for v in plan.values() for it in v)
    st.write(f"**{total} minutes** planned out of {hours * 60} available")
    st.markdown(bar(100 * total / (hours * 60) if hours else 0), unsafe_allow_html=True)
    cols = st.columns(5)
    text = f"VERVAIN study plan for {ss.name}\n"
    for col, (day, items) in zip(cols, plan.items()):
        with col:
            body = "".join(f"<li>{it['title']}<br><span style='opacity:.6'>{it['minutes']} min · {it['type']}</span></li>"
                           for it in items) or "<li style='opacity:.5'>Rest day</li>"
            st.markdown(f'<div class="card"><b>{day}</b><ul style="padding-left:16px">{body}</ul></div>', unsafe_allow_html=True)
        text += f"\n{day}\n" + "".join(f"- {it['title']} ({it['minutes']} min)\n" for it in items)
    st.download_button("⬇️ Download plan", text, file_name="study_plan.txt")
    st.divider()
    if st.button("🤖 Generate AI plan with Claude"):
        with st.spinner("Agent is working..."):
            try:
                out, trace = run_agent(info, miscs, recs, RESOURCES, ss.usage, hours, api_key or None)
                if out is None:
                    st.warning("Add an API key in the sidebar to use the AI agent.")
                else:
                    st.markdown(out)
                    with st.expander("Tool calls the agent made"):
                        st.json(trace)
            except Exception as e:
                st.error(f"Agent error: {e}")

# ---------------- skill map ----------------
if page == "Skill map":
    st.caption("Arrows show prerequisites. 🔴 weak · 🟡 medium · 🟢 strong · grey = not assessed yet")
    st.graphviz_chart(graph_dot(info, ss.subjects), width="stretch")

# ---------------- AI tutor ----------------
if page == "AI Tutor":
    st.caption("Answers come only from trusted notes (RAG).")
    for role, msg in ss.chat:
        st.chat_message(role).markdown(msg)
    q = st.chat_input("Ask anything, e.g. why does range(3) run 3 times?")
    if q:
        ss.chat.append(("user", q))
        if is_greeting(q):
            ans = ("Hi! 👋 I'm your study tutor. Ask me about a concept, for example:\n\n"
                   "- Why does range(3) run 3 times?\n- What is the difference between INNER and LEFT JOIN?\n"
                   "- What does &x mean in C?")
        else:
            # Normalize snippets because engine.retrieve may return dictionaries
            # or (topic, content) pairs depending on the version in the project.
            raw_snip = retrieve(q)
            snip = []
            for item in raw_snip or []:
                if isinstance(item, dict):
                    topic = item.get("topic") or item.get("subject") or "Study notes"
                    content = item.get("content") or item.get("text") or ""
                elif isinstance(item, (tuple, list)) and len(item) >= 2:
                    topic, content = item[0], item[1]
                else:
                    topic, content = "Study notes", str(item)
                if str(content).strip():
                    snip.append((str(topic), str(content)))

            if not snip:
                ans = "I could not find that in my trusted notes. Try asking about a topic like loops, JOINs, pointers or arrays."
            else:
                try:
                    ans = tutor_answer(
                        q, snip,
                        [t for t, stats in info.items() if stats.get("label") == "weak"],
                        api_key or None,
                    )
                except Exception as e:
                    ans = f"Tutor error: {type(e).__name__}: {e}"

                if not ans:
                    try:
                        ans = offline_answer(q)
                    except TypeError:
                        ans = offline_answer(q, snip)
                source_names = ", ".join(dict.fromkeys(topic for topic, _ in snip))
                ans = (ans or "I found relevant notes, but could not compose an answer.") + "\n\n*Sources: " + source_names + "*"
        ss.chat.append(("assistant", ans))
        st.rerun()

# ---------------- progress ----------------
if page == "Progress":
    badges = [("🚀 First answer", n_ans >= 1), ("🎯 5 correct", n_ok >= 5), ("🔥 3 in a row", streak >= 3),
              ("🏆 Topic master", strong_n >= 1), ("📚 Studied a resource", len(ss.usage) >= 1),
              ("⭐ Level 3", level >= 3)]
    st.markdown("".join(f'<span class="badge{"" if on else " off"}">{n}</span>' for n, on in badges), unsafe_allow_html=True)
    if ss.snapshots:
        st.subheader("Mastery after each answer batch")
        st.line_chart(pd.DataFrame(ss.snapshots).rename(columns=lambda c: c.replace(":", " -")))
    else:
        st.info("Progress appears after your first answers.")

# ---------------- quiz history ----------------
if page == "Quiz history":
    if not ss.answers:
        st.info("No quiz history yet. Take a quiz first.")
    else:
        history_rows = []
        for n, item in enumerate(reversed(ss.answers), 1):
            qid = item.get("qid") or item.get("question_id") or item.get("id")
            question = QBYID.get(qid, {}).get("q", item.get("question", "—"))
            history_rows.append({
                "#": n,
                "topic": item.get("topic", "General"),
                "question": question,
                "result": "✅ correct" if bool(item.get("correct", item.get("is_correct", False))) else "❌ wrong",
                "misconception": item.get("tag") or item.get("misconception") or "",
            })
        st.dataframe(pd.DataFrame(history_rows), width="stretch", hide_index=True)