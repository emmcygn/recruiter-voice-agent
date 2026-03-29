import re


def score_experience(answer: str) -> dict:
    """Score experience answer based on years and title keywords."""
    text = answer.lower()
    score = 1
    rationale_parts = []

    year_patterns = [
        r'(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?',
    ]
    years = 0
    for pattern in year_patterns:
        match = re.search(pattern, text)
        if match:
            years = int(match.group(1))
            break

    if years >= 5:
        score = 5
        rationale_parts.append(f"{years} years experience")
    elif years >= 3:
        score = 4
        rationale_parts.append(f"{years} years experience")
    elif years >= 1:
        score = 3
        rationale_parts.append(f"{years} year(s) experience")
    elif years > 0:
        score = 2
        rationale_parts.append(f"Less than 1 year")
    else:
        score = 1
        rationale_parts.append("No experience signal detected")

    title_keywords = ["senior", "lead", "staff", "principal", "architect", "head of", "director"]
    for kw in title_keywords:
        if kw in text:
            score = min(score + 1, 5)
            rationale_parts.append(f"title keyword: {kw}")
            break

    return {"score": score, "rationale": ", ".join(rationale_parts)}


TECH_KEYWORDS = [
    "python", "typescript", "javascript", "react", "node", "nodejs",
    "postgresql", "postgres", "aws", "docker", "kubernetes", "k8s",
    "go", "golang", "java", "c#", "csharp", "ruby", "rust",
    "vue", "angular", "django", "fastapi", "flask", "spring",
    "mongodb", "redis", "graphql", "terraform",
]


def score_tech_stack(answer: str) -> dict:
    """Score tech stack answer by counting recognized technologies."""
    text = answer.lower()
    matches = [kw for kw in TECH_KEYWORDS if kw in text]
    unique = set()
    alias_map = {
        "nodejs": "node", "golang": "go", "postgres": "postgresql", "csharp": "c#", "k8s": "kubernetes",
    }
    for m in matches:
        unique.add(alias_map.get(m, m))

    count = len(unique)

    if count >= 5:
        score = 5
    elif count >= 3:
        score = 4
    elif count >= 2:
        score = 3
    elif count >= 1:
        score = 2
    else:
        score = 1

    rationale = f"{count} matching technologies" if count > 0 else "No recognized technologies"
    return {"score": score, "rationale": rationale}


PROBLEM_SOLVING_SIGNALS = [
    "debugged", "debug", "profiled", "profiling", "tested", "testing",
    "refactored", "refactoring", "scaled", "scaling", "optimized", "optimization",
    "root cause", "trade-off", "tradeoff", "trade off",
    "investigated", "diagnosed", "benchmarked", "monitored", "instrumented",
    "iterated", "prototyped", "architected",
]


def score_problem_solving(answer: str) -> dict:
    """Score problem-solving answer by counting methodology signals."""
    text = answer.lower()
    found = [s for s in PROBLEM_SOLVING_SIGNALS if s in text]
    count = len(found)

    if count >= 4:
        score = 5
    elif count >= 3:
        score = 4
    elif count >= 2:
        score = 3
    elif count >= 1:
        score = 2
    else:
        score = 1

    rationale = f"{count} methodology signals" if count > 0 else "No methodology signals detected"
    return {"score": score, "rationale": rationale}


COLLABORATION_KEYWORDS = [
    "pair", "pairing", "pair programming",
    "review", "code review", "pr", "pull request",
    "stand-up", "standup", "retro", "retrospective",
    "async", "sync",
    "mentor", "mentoring",
    "team", "mob programming",
]


def score_collaboration(answer: str) -> dict:
    """Score collaboration answer by counting collaboration keywords."""
    text = answer.lower()
    found = [kw for kw in COLLABORATION_KEYWORDS if kw in text]
    count = len(set(found))

    if count >= 3:
        score = 5
    elif count >= 2:
        score = 4
    elif count >= 1:
        score = 3
    else:
        score = 1

    rationale = f"{count} collaboration keywords" if count > 0 else "No collaboration signals detected"
    return {"score": score, "rationale": rationale}


def score_availability(answer: str) -> dict:
    """Score availability based on notice period parsing."""
    text = answer.lower()

    immediate_keywords = ["immediately", "immediate", "right away", "asap", "available now", "between roles", "no notice"]
    if any(kw in text for kw in immediate_keywords):
        return {"score": 5, "rationale": "Available immediately"}

    week_match = re.search(r'(\d+)\s*weeks?', text)
    if week_match:
        weeks = int(week_match.group(1))
        if weeks <= 2:
            return {"score": 5, "rationale": f"{weeks} week(s) notice"}
        elif weeks <= 4:
            return {"score": 4, "rationale": f"{weeks} weeks notice"}
        elif weeks <= 8:
            return {"score": 3, "rationale": f"{weeks} weeks notice"}
        else:
            return {"score": 2, "rationale": f"{weeks} weeks notice"}

    month_match = re.search(r'(\d+)\s*months?', text)
    if month_match:
        months = int(month_match.group(1))
        if months <= 1:
            return {"score": 4, "rationale": f"{months} month notice"}
        elif months <= 2:
            return {"score": 3, "rationale": f"{months} months notice"}
        else:
            return {"score": 2, "rationale": f"{months} months notice"}

    if "one month" in text:
        return {"score": 4, "rationale": "1 month notice"}
    if "two month" in text:
        return {"score": 3, "rationale": "2 months notice"}
    if "three month" in text:
        return {"score": 2, "rationale": "3 months notice"}

    return {"score": 1, "rationale": "Notice period unclear"}


def compute_overall(scores: dict) -> dict:
    """Compute overall score and pass/flag/fail status from individual scores."""
    values = [s["score"] for s in scores.values()]
    avg = round(sum(values) / len(values), 1)

    if avg >= 3.5:
        status = "pass"
    elif avg >= 2.5:
        status = "flag"
    else:
        status = "fail"

    return {"overall_score": avg, "overall_status": status}
