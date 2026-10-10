
"""VERVAIN backend engine."""

from pathlib import Path
import re
from collections import Counter

import joblib
import pandas as pd

try:
    from data_bank import NOTES, PREREQS
except ImportError:
    NOTES = {}
    PREREQS = {}

# Bayesian Knowledge Tracing settings
P_INIT = 0.30
P_LEARN = 0.15
P_GUESS = 0.20
P_SLIP = 0.10


def _as_float(value, default=0.0):
    """Safely convert a value to a float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _topic_of(item):
    """Get the topic associated with a record."""
    if isinstance(item, dict):
        return (
            item.get("topic")
            or item.get("subject")
            or item.get("skill")
            or "General"
        )
    return "General"


def _correct_of(item):
    """Determine whether an answer record is correct."""
    if isinstance(item, dict):
        for key in ("correct", "is_correct", "was_correct", "result"):
            if key in item:
                value = item[key]

                if isinstance(value, str):
                    return value.strip().lower() in {
                        "true", "1", "yes", "correct", "right"
                    }

                return bool(value)

        if "selected" in item and "answer" in item:
            return (
                str(item["selected"]).strip().lower()
                == str(item["answer"]).strip().lower()
            )

    return bool(item)


def compute_mastery(answers):
    """Estimate topic mastery using Bayesian Knowledge Tracing."""
    by_topic = {}

    if isinstance(answers, dict):
        for topic, records in answers.items():
            if isinstance(records, (list, tuple)):
                by_topic[str(topic)] = list(records)
            else:
                by_topic[str(topic)] = [records]

    elif isinstance(answers, (list, tuple)):
        for record in answers:
            topic = str(_topic_of(record))
            by_topic.setdefault(topic, []).append(record)

    output = {}

    for topic, records in by_topic.items():
        mastery = P_INIT
        correct_count = 0

        for record in records:
            is_correct = _correct_of(record)
            correct_count += int(is_correct)

            if is_correct:
                likelihood_mastered = (1 - P_SLIP) * mastery
                likelihood_unmastered = P_GUESS * (1 - mastery)
            else:
                likelihood_mastered = P_SLIP * mastery
                likelihood_unmastered = (
                    (1 - P_GUESS) * (1 - mastery)
                )

            denominator = (
                likelihood_mastered + likelihood_unmastered
            )

            if denominator:
                posterior = likelihood_mastered / denominator
            else:
                posterior = mastery

            mastery = posterior + (1 - posterior) * P_LEARN

        attempts = len(records)

        if mastery < 0.5:
            label = "weak"
        elif mastery >= 0.8:
            label = "strong"
        else:
            label = "medium"

        if attempts < 3:
            confidence = "low"
        elif attempts < 6:
            confidence = "medium"
        else:
            confidence = "high"

        output[topic] = {
            "mastery": round(mastery, 4),
            "attempts": attempts,
            "correct": correct_count,
            "accuracy": (
                round(correct_count / attempts, 4)
                if attempts else 0.0
            ),
            "label": label,
            "confidence": confidence,
        }

    return output


def depth(text):
    """Estimate the depth of learning requested by a question."""
    value = str(text or "").lower()

    if any(word in value for word in (
        "why", "compare", "derive", "prove",
        "analyze", "analyse", "trade-off", "tradeoff"
    )):
        return "deep"

    if any(word in value for word in (
        "explain", "how", "example", "steps", "work"
    )):
        return "medium"

    return "basic"


def is_greeting(text):
    """Check whether the input is a simple greeting."""
    value = re.sub(
        r"[^a-z ]", "", str(text or "").lower()
    ).strip()

    return value in {
        "hi", "hello", "hey", "hii", "hiii",
        "good morning", "good afternoon",
        "good evening", "howdy"
    }


def misconceptions(answers):
    """Return incorrect answers grouped by topic and misconception."""
    counts = Counter()

    if isinstance(answers, dict):
        iterable = []

        for topic, records in answers.items():
            if not isinstance(records, (list, tuple)):
                records = [records]

            for record in records:
                if isinstance(record, dict):
                    row = dict(record)
                    row.setdefault("topic", topic)
                    iterable.append(row)
                else:
                    iterable.append({
                        "topic": topic,
                        "correct": bool(record),
                    })

    elif isinstance(answers, (list, tuple)):
        iterable = list(answers)

    else:
        iterable = []

    for item in iterable:
        if not isinstance(item, dict) or not _correct_of(item):
            topic = _topic_of(item)
            description = "Review incorrect answers"

            if isinstance(item, dict):
                description = str(
                    item.get("misconception")
                    or item.get("concept")
                    or item.get("question")
                    or description
                )

            counts[(topic, description)] += 1

    return [
        {
            "topic": topic,
            "misconception": description,
            "times": times,
        }
        for (topic, description), times in counts.items()
    ]


def _prerequisites(topic):
    """Return the prerequisite topics for a topic."""
    value = (
        PREREQS.get(topic, [])
        if isinstance(PREREQS, dict)
        else []
    )

    if isinstance(value, str):
        return [value]

    if isinstance(value, (list, tuple, set)):
        return list(value)

    return []


def recommend(info, resources, usage=None, miscs=None):
    """
    Recommend resources according to mastery, quiz performance,
    misconceptions, and previous resource usage.

    Expected resource fields include:
    topic, id, type, difficulty, title, and description.
    """

    if not isinstance(info, dict):
        info = {}

    if not isinstance(resources, (list, tuple)):
        resources = []

    # Count previously used resources.
    usage_counts = Counter()

    if isinstance(usage, dict):
        for resource_id, count in usage.items():
            usage_counts[str(resource_id)] = _as_float(count)

    elif isinstance(usage, (list, tuple)):
        for item in usage:
            if isinstance(item, dict):
                resource_id = (
                    item.get("id")
                    or item.get("resource_id")
                    or item.get("resource")
                )

                if isinstance(resource_id, dict):
                    resource_id = (
                        resource_id.get("id")
                        or resource_id.get("title")
                    )

                if resource_id:
                    usage_counts[str(resource_id)] += 1

            elif isinstance(item, str):
                usage_counts[item] += 1

    # Count misconceptions by normalized topic.
    misc_counts = Counter()

    if isinstance(miscs, dict):
        for topic, count in miscs.items():
            misc_counts[str(topic).strip().lower()] = _as_float(count)

    elif isinstance(miscs, (list, tuple)):
        for item in miscs:
            if isinstance(item, dict) and item.get("topic"):
                topic_key = str(item["topic"]).strip().lower()
                misc_counts[topic_key] += _as_float(
                    item.get("times", 1), 1
                )

    recommendations = []

    for topic, stats in info.items():
        topic_key = str(topic).strip().lower()

        if isinstance(stats, dict):
            mastery = _as_float(stats.get("mastery", 0))

            quiz_score = stats.get(
                "quiz_score",
                stats.get("score", stats.get("accuracy"))
            )
        else:
            mastery = _as_float(stats)
            quiz_score = None

        # Normalize mastery from either 0–1 or 0–100.
        if mastery > 1:
            mastery /= 100.0

        mastery = max(0.0, min(1.0, mastery))
        mastery_percent = round(mastery * 100)

        # Normalize optional quiz score.
        if quiz_score is not None:
            quiz_score = _as_float(quiz_score, -1)

            if quiz_score >= 0:
                if quiz_score > 1:
                    quiz_score /= 100.0

                quiz_score = max(0.0, min(1.0, quiz_score))
            else:
                quiz_score = None

        # Find resources for this topic.
        topic_resources = [
            resource for resource in resources
            if isinstance(resource, dict)
            and str(resource.get("topic", "")).strip().lower()
            == topic_key
        ]

        if not topic_resources:
            recommendations.append({
                "topic": topic,
                "resource": {},
                "flag": "no_material",
                "label": "Study resource",
                "mastery": mastery_percent,
                "reason": (
                    f"No learning resource is available for {topic} yet."
                ),
            })
            continue

        # Choose a learning strategy.
        if mastery < 0.50:
            preferred_types = ["notes", "video", "practice"]
            preferred_difficulty = "beginner"

            reason = (
                f"Your estimated mastery is {mastery_percent}%. "
                "Review the fundamentals and then practise basic questions."
            )

        elif mastery < 0.80:
            preferred_types = ["practice", "notes", "video"]
            preferred_difficulty = "intermediate"

            reason = (
                f"Your estimated mastery is {mastery_percent}%. "
                "Practise this topic to strengthen your understanding."
            )

        else:
            preferred_types = ["practice", "notes", "video"]
            preferred_difficulty = "advanced"

            reason = (
                f"Your estimated mastery is {mastery_percent}%. "
                "Try a challenge or advanced practice to deepen your skills."
            )

        # Low quiz performance can override high estimated mastery.
        if quiz_score is not None and quiz_score < 0.50:
            preferred_types = ["practice", "notes", "video"]
            preferred_difficulty = "intermediate"

            reason = (
                f"Your quiz score is {round(quiz_score * 100)}%. "
                "Review the topic and practise similar questions."
            )

        # Rank resources by suitability before usage count.
        def resource_rank(resource):
            resource_type = str(
                resource.get("type", "")
            ).strip().lower()

            difficulty = str(
                resource.get("difficulty", "")
            ).strip().lower()

            resource_id = str(
                resource.get("id")
                or resource.get("title")
                or resource.get("name")
                or topic
            )

            if resource_type in preferred_types:
                type_rank = preferred_types.index(resource_type)
            else:
                type_rank = len(preferred_types)

            if difficulty == preferred_difficulty:
                difficulty_rank = 0
            elif difficulty in (
                "beginner", "intermediate", "advanced"
            ):
                difficulty_rank = 1
            else:
                difficulty_rank = 2

            return (
                type_rank,
                difficulty_rank,
                usage_counts.get(resource_id, 0),
            )

        resource = min(topic_resources, key=resource_rank)

        resource_id = str(
            resource.get("id")
            or resource.get("title")
            or resource.get("name")
            or topic
        )

        if misc_counts.get(topic_key, 0) > 0:
            reason += " Review your previous incorrect answers too."

        recommendations.append({
            "topic": topic,
            "resource": resource,
            "flag": (
                "stuck"
                if usage_counts.get(resource_id, 0) > 0
                and mastery < 0.50
                else "normal"
            ),
            "label": str(
                resource.get("type", "Study resource")
            ),
            "mastery": mastery_percent,
            "reason": reason,
        })

    return recommendations


def retrieve(query, notes=None, limit=5):
    """Find local notes that best match a user's question."""
    notes = NOTES if notes is None else notes

    query_words = set(
        re.findall(r"[a-z0-9]+", str(query or "").lower())
    )

    if not query_words:
        return []

    candidates = []

    if isinstance(notes, dict):
        source = []

        for topic, content in notes.items():
            if isinstance(content, (list, tuple)):
                for entry in content:
                    source.append({
                        "topic": topic,
                        "content": entry,
                    })
            else:
                source.append({
                    "topic": topic,
                    "content": content,
                })

    elif isinstance(notes, (list, tuple)):
        source = [
            entry if isinstance(entry, dict)
            else {"content": entry}
            for entry in notes
        ]

    else:
        source = []

    for entry in source:
        if isinstance(entry, dict):
            content = entry.get(
                "content",
                entry.get("text", entry.get("note", ""))
            )
            topic = entry.get("topic", "")
        else:
            content = str(entry)
            topic = ""

        combined = f"{topic} {content}"

        note_words = set(
            re.findall(r"[a-z0-9]+", combined.lower())
        )

        overlap = len(query_words & note_words)

        if overlap:
            relevance = overlap / len(query_words)

            candidates.append((
                relevance,
                {
                    "topic": topic,
                    "content": content,
                },
            ))

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        item for score, item in candidates[:max(1, int(limit))]
    ]


def offline_answer(question, notes=None):
    """Create an answer using locally stored study notes."""
    matches = retrieve(
        question,
        notes=notes,
        limit=3
    )

    if not matches:
        return (
            "I couldn't find a matching explanation in the "
            "local notes yet. Try including the subject or "
            "topic name in your question."
        )

    parts = []

    for match in matches:
        topic = match.get("topic", "")
        content = match.get("content", "")

        if topic:
            parts.append(f"{topic}: {content}")
        else:
            parts.append(str(content))

    return "\n\n".join(parts)


def load_study_model():
    """Load the trained study recommendation model."""
    model_path = (
        Path(__file__).resolve().parent
        / "study_recommender.pkl"
    )

    if not model_path.exists():
        print(f"ML model file not found: {model_path}")
        return None

    if model_path.stat().st_size == 0:
        print("ML model file is empty.")
        return None

    try:
        model = joblib.load(model_path)
        print("ML study recommendation model loaded.")
        return model

    except Exception as error:
        print(f"Could not load ML model: {error}")
        return None


def predict_resource_need(quiz_score, mastery):
    """
    Predict whether a student may need additional study resources.

    Inputs may be fractions (0–1) or percentages (0–100).

    Returns:
        1: the model predicts extra resources may be useful.
        0: the model predicts extra resources may not be needed.
        None: the model could not load or predict.
    """
    model = load_study_model()

    if model is None:
        return None

    score = _as_float(quiz_score, 0.0)
    mastery_value = _as_float(mastery, 0.0)

    if score > 1:
        score /= 100.0

    if mastery_value > 1:
        mastery_value /= 100.0

    score = max(0.0, min(1.0, score))
    mastery_value = max(0.0, min(1.0, mastery_value))

    features = pd.DataFrame(
        [{
            "quiz_score": score,
            "mastery": mastery_value,
        }],
        columns=["quiz_score", "mastery"]
    )

    try:
        prediction = model.predict(features)[0]
        return int(prediction)

    except Exception as error:
        print(f"ML prediction failed: {error}")
        return None


def search_resources(query, resources=None, limit=5):
    """Find learning resources relevant to a search query."""
    if resources is None:
        try:
            from data_bank import RESOURCES
            resources = RESOURCES
        except ImportError:
            return []

    if not isinstance(resources, (list, tuple)):
        return []

    query_words = set(
        re.findall(r"[a-z0-9]+", str(query or "").lower())
    )

    if not query_words:
        return []

    results = []

    for resource in resources:
        if not isinstance(resource, dict):
            continue

        searchable = " ".join(
            str(resource.get(key, ""))
            for key in (
                "title", "topic", "type",
                "difficulty", "description", "label"
            )
        ).lower()

        score = sum(
            1 for word in query_words if word in searchable
        )

        if score > 0:
            results.append((score, resource))

    results.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        resource
        for _, resource in results[:max(1, int(limit))]
    ]
