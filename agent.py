"""AI layer: Claude agent with tools, study plan, and RAG tutor. Works without a key (fallbacks)."""
import json
import os

from engine import search_resources

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")

TOOLS = [
    {"name": "analyze_performance",
     "description": "Get per-topic mastery %, label (weak/medium/strong), confidence and detected misconceptions.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "search_resources",
     "description": "Search study materials by topic and optional difficulty (beginner/intermediate/advanced).",
     "input_schema": {"type": "object",
                      "properties": {"topic": {"type": "string"}, "difficulty": {"type": "string"}},
                      "required": ["topic"]}},
]


def rule_based_plan(recs, hours, days=5):
    """Study sequence that fits the available time (prerequisites first)."""
    budget, used, plan = int(hours * 60), 0, []
    for rec in recs:
        r = rec["resource"]
        if r and used + r["minutes"] <= budget:
            plan.append({"title": r["title"], "minutes": r["minutes"], "type": r["type"]})
            used += r["minutes"]
    per_day = {f"Day {i+1}": [] for i in range(days)}
    for i, item in enumerate(plan):
        per_day[f"Day {i % days + 1}"].append(item)
    return per_day


def run_agent(info, miscs, recs, resources, usage, hours, api_key=None):
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None, []
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    summary = {t: {"mastery_pct": round(s["mastery"] * 100), "label": s["label"], "confidence": s["confidence"]}
               for t, s in info.items()}
    system = ("You are a study coach agent. Use the tools to inspect the student's performance and find "
              "resources. Study prerequisite topics before dependent ones. Write a personalized plan for the "
              "available time, weakest foundations first. For EVERY resource explain why it was chosen "
              "(mastery, difficulty, misconception). If a student keeps failing with the same material, switch "
              "the format. Be concise and encouraging.")
    messages = [{"role": "user", "content": f"I have {hours} hours this week. Already used: {usage}. Build my plan."}]
    trace = []
    for _ in range(6):
        resp = client.messages.create(model=MODEL, max_tokens=1500, system=system, tools=TOOLS, messages=messages)
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text"), trace
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                if b.name == "analyze_performance":
                    out = {"topics": summary, "misconceptions": miscs}
                else:
                    out = search_resources(resources, b.input["topic"], b.input.get("difficulty"), usage)
                trace.append({"tool": b.name, "input": b.input})
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(out)})
        messages.append({"role": "user", "content": results})
    return "Agent stopped early.", trace


def tutor_answer(question, snippets, weak_topics, api_key=None):
    """RAG: answer ONLY from retrieved trusted notes."""
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    context = "\n".join(f"[{t}] {x}" for t, x in snippets) or "(no relevant notes found)"
    system = ("You are a friendly programming tutor. Answer using ONLY the provided notes. If the notes do not "
              "cover the question, say so. Give a short explanation, one example, then step-by-step guidance. "
              f"The student's weak topics are: {weak_topics}.")
    resp = client.messages.create(model=MODEL, max_tokens=800, system=system,
                                  messages=[{"role": "user", "content": f"Notes:\n{context}\n\nQuestion: {question}"}])
    return "".join(b.text for b in resp.content if b.type == "text")