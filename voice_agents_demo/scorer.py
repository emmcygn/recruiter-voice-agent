import re

# Spoken number words to digits
WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100,
}


def _parse_spoken_number(text: str) -> int:
    """Parse spoken numbers like 'seventy five' -> 75, 'three' -> 3."""
    words = text.split()
    total = 0
    current = 0
    found_any = False

    for word in words:
        word = word.strip(",").lower()
        if word in WORD_TO_NUM:
            found_any = True
            val = WORD_TO_NUM[word]
            if val == 100:
                current = (current if current else 1) * 100
            elif val >= 10 and val <= 90 and val % 10 == 0:
                current += val
            else:
                current += val
        elif word == "thousand":
            found_any = True
            current = (current if current else 1) * 1000
            total += current
            current = 0
        elif found_any:
            # Stop when we hit a non-number word after finding numbers
            break

    total += current
    return total if found_any else 0


def score_experience(answer: str) -> dict:
    """Score experience answer based on years and title keywords."""
    text = answer.lower()
    score = 1
    rationale_parts = []

    # Try digit-based patterns first
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

    # Try spoken number patterns: "three years", "twenty years"
    if years == 0:
        spoken_match = re.search(r'((?:\w+\s+){1,3})years?', text)
        if spoken_match:
            years = _parse_spoken_number(spoken_match.group(1))

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


def score_work_preference(answer: str) -> dict:
    """Score work preference — extracts preference and flexibility."""
    text = answer.lower()

    preference = "unclear"
    if any(kw in text for kw in ["remote", "from home", "work from home", "wfh"]):
        preference = "remote"
    elif any(kw in text for kw in ["hybrid", "mix", "split", "few days"]):
        preference = "hybrid"
    elif any(kw in text for kw in ["office", "in-office", "on-site", "onsite", "in person"]):
        preference = "in-office"

    flexible = "unknown"
    # Check negative flexibility FIRST (before positive, since "not flexible" contains "flexible")
    if any(kw in text for kw in ["not flexible", "no flexibility", "only", "must be", "need to be", "strictly"]):
        flexible = "no"
    elif any(kw in text for kw in ["flexible", "open to", "don't mind", "happy to", "either", "any", "adaptable"]):
        flexible = "yes"

    if preference == "unclear":
        score = 1
        rationale = "Work preference unclear"
    elif flexible == "yes":
        score = 5
        rationale = f"Prefers {preference}, flexible"
    elif flexible == "no":
        score = 3
        rationale = f"Prefers {preference}, not flexible"
    else:
        score = 4
        rationale = f"Prefers {preference}, flexibility unknown"

    return {"score": score, "rationale": rationale}


def score_current_salary(answer: str) -> dict:
    """Extract current salary from answer."""
    text = answer.lower()

    # Match patterns like £50k, £50,000, 50k, 50000, £50
    salary = _extract_salary(text)

    if salary:
        return {"score": 5, "rationale": f"Current salary: £{salary:,}"}
    elif any(kw in text for kw in ["prefer not", "rather not", "confidential", "private"]):
        return {"score": 3, "rationale": "Declined to share current salary"}
    else:
        return {"score": 1, "rationale": "Current salary unclear"}


def score_target_salary(answer: str) -> dict:
    """Extract target/minimum salary from answer."""
    text = answer.lower()

    salary = _extract_salary(text)

    if salary:
        return {"score": 5, "rationale": f"Target floor salary: £{salary:,}"}
    elif any(kw in text for kw in ["negotiable", "open", "flexible", "depends"]):
        return {"score": 4, "rationale": "Target salary negotiable/open"}
    elif any(kw in text for kw in ["prefer not", "rather not", "confidential", "private"]):
        return {"score": 3, "rationale": "Declined to share target salary"}
    else:
        return {"score": 1, "rationale": "Target salary unclear"}


def _extract_salary(text: str) -> int:
    """Extract a salary figure from text. Returns int or 0 if not found."""
    # £80,000 or 80,000 or £80000 or 80000
    match = re.search(r'[£$]?\s*(\d{2,3})[,.]?(\d{3})', text)
    if match:
        return int(match.group(1) + match.group(2))

    # 80k or £80k
    match = re.search(r'[£$]?\s*(\d{2,3})\s*k\b', text)
    if match:
        return int(match.group(1)) * 1000

    # Spoken numbers: "seventy five thousand", "eighty thousand"
    spoken = _parse_spoken_number(text)
    if spoken >= 20000:  # Only accept as salary if >= 20k
        return spoken

    return 0


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
