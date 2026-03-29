import pytest
from scorer import (
    score_experience,
    score_tech_stack,
    score_problem_solving,
    score_collaboration,
    score_availability,
    compute_overall,
)


class TestScoreExperience:
    def test_senior_five_plus_years(self):
        result = score_experience("I've been a senior software engineer for 7 years at Google")
        assert result["score"] == 5
        assert "7" in result["rationale"] or "year" in result["rationale"].lower()

    def test_mid_level_three_years(self):
        result = score_experience("I have 3 years of experience as a developer")
        assert result["score"] == 4

    def test_junior_one_year(self):
        result = score_experience("I graduated last year and have been working for about 1 year")
        assert result["score"] == 3

    def test_no_signal(self):
        result = score_experience("I like computers")
        assert result["score"] == 1

    def test_title_boost(self):
        result = score_experience("I'm a lead engineer with 3 years experience")
        assert result["score"] == 5  # 4 (3 years) + 1 (lead) = 5


class TestScoreTechStack:
    def test_strong_stack(self):
        result = score_tech_stack("Python, TypeScript, React, PostgreSQL, Docker, AWS")
        assert result["score"] == 5

    def test_moderate_stack(self):
        result = score_tech_stack("I mainly use Java and Spring Boot with some Kubernetes")
        assert result["score"] == 4  # java, spring, kubernetes = 3

    def test_single_match(self):
        result = score_tech_stack("I only really use Python")
        assert result["score"] == 2

    def test_no_matches(self):
        result = score_tech_stack("I use Fortran and COBOL mostly")
        assert result["score"] == 1


class TestScoreProblemSolving:
    def test_strong_methodology(self):
        result = score_problem_solving(
            "We had a memory leak so I profiled the app, debugged the issue, "
            "tested a fix, and then refactored the module to prevent regression"
        )
        assert result["score"] == 5

    def test_some_signals(self):
        result = score_problem_solving("I investigated the issue and tested the fix")
        assert result["score"] == 3

    def test_no_signals(self):
        result = score_problem_solving("It was hard but I figured it out eventually")
        assert result["score"] == 1


class TestScoreCollaboration:
    def test_strong_collaboration(self):
        result = score_collaboration(
            "We do pair programming, async code reviews on PRs, "
            "and weekly retros to improve our process"
        )
        assert result["score"] == 5

    def test_some_collaboration(self):
        result = score_collaboration("We hold weekly retros with the team")
        assert result["score"] == 4

    def test_no_signals(self):
        result = score_collaboration("I just work on my tasks independently")
        assert result["score"] == 1


class TestScoreAvailability:
    def test_immediate(self):
        result = score_availability("I can start immediately, I'm between roles")
        assert result["score"] == 5

    def test_one_month(self):
        result = score_availability("I have a 1 month notice period")
        assert result["score"] == 4

    def test_two_months(self):
        result = score_availability("My notice period is 2 months")
        assert result["score"] == 3

    def test_three_months(self):
        result = score_availability("I'm on a 3 month notice period")
        assert result["score"] == 2

    def test_unclear(self):
        result = score_availability("I'm not sure, it depends on a few things")
        assert result["score"] == 1


class TestComputeOverall:
    def test_pass(self):
        scores = {
            "experience": {"score": 5, "rationale": ""},
            "tech_stack": {"score": 4, "rationale": ""},
            "problem_solving": {"score": 4, "rationale": ""},
            "collaboration": {"score": 3, "rationale": ""},
            "availability": {"score": 5, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 4.2
        assert result["overall_status"] == "pass"

    def test_flag(self):
        scores = {
            "experience": {"score": 3, "rationale": ""},
            "tech_stack": {"score": 3, "rationale": ""},
            "problem_solving": {"score": 3, "rationale": ""},
            "collaboration": {"score": 3, "rationale": ""},
            "availability": {"score": 2, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 2.8
        assert result["overall_status"] == "flag"

    def test_fail(self):
        scores = {
            "experience": {"score": 1, "rationale": ""},
            "tech_stack": {"score": 1, "rationale": ""},
            "problem_solving": {"score": 2, "rationale": ""},
            "collaboration": {"score": 1, "rationale": ""},
            "availability": {"score": 1, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 1.2
        assert result["overall_status"] == "fail"

    def test_boundary_pass(self):
        scores = {
            "experience": {"score": 4, "rationale": ""},
            "tech_stack": {"score": 3, "rationale": ""},
            "problem_solving": {"score": 4, "rationale": ""},
            "collaboration": {"score": 3, "rationale": ""},
            "availability": {"score": 3, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 3.4
        assert result["overall_status"] == "flag"

    def test_boundary_flag(self):
        scores = {
            "experience": {"score": 3, "rationale": ""},
            "tech_stack": {"score": 2, "rationale": ""},
            "problem_solving": {"score": 3, "rationale": ""},
            "collaboration": {"score": 2, "rationale": ""},
            "availability": {"score": 3, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 2.6
        assert result["overall_status"] == "flag"
