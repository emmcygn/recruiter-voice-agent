import pytest
from scorer import (
    score_experience,
    score_tech_stack,
    score_problem_solving,
    score_work_preference,
    score_availability,
    score_current_salary,
    score_target_salary,
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

    def test_spoken_three_years(self):
        result = score_experience("I've been working for three years and my current role is with a startup")
        assert result["score"] == 4

    def test_spoken_ten_years(self):
        result = score_experience("I have ten years of experience as a software engineer")
        assert result["score"] == 5


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


class TestScoreWorkPreference:
    def test_remote_flexible(self):
        result = score_work_preference("I prefer remote but I'm flexible and open to hybrid")
        assert result["score"] == 5
        assert "flexible" in result["rationale"]

    def test_hybrid_not_flexible(self):
        result = score_work_preference("I need to be hybrid only, not flexible on that")
        assert result["score"] == 3

    def test_office_clear(self):
        result = score_work_preference("I prefer working in the office")
        assert result["score"] == 4
        assert "in-office" in result["rationale"]

    def test_unclear(self):
        result = score_work_preference("I don't know really")
        assert result["score"] == 1


class TestScoreCurrentSalary:
    def test_salary_with_k(self):
        result = score_current_salary("I'm currently on about 85k")
        assert result["score"] == 5
        assert "85,000" in result["rationale"]

    def test_salary_full_number(self):
        result = score_current_salary("My salary is £65,000")
        assert result["score"] == 5
        assert "65,000" in result["rationale"]

    def test_declined(self):
        result = score_current_salary("I'd prefer not to say")
        assert result["score"] == 3

    def test_unclear(self):
        result = score_current_salary("It varies a lot")
        assert result["score"] == 1

    def test_spoken_salary(self):
        result = score_current_salary("I'm at seventy five thousand")
        assert result["score"] == 5
        assert "75,000" in result["rationale"]


class TestScoreTargetSalary:
    def test_target_with_k(self):
        result = score_target_salary("I'm looking for at least 95k")
        assert result["score"] == 5
        assert "95,000" in result["rationale"]

    def test_spoken_target(self):
        result = score_target_salary("I would be hoping for eighty thousand")
        assert result["score"] == 5
        assert "80,000" in result["rationale"]

    def test_negotiable(self):
        result = score_target_salary("I'm pretty open and flexible on salary")
        assert result["score"] == 4

    def test_declined(self):
        result = score_target_salary("I'd rather not say at this stage")
        assert result["score"] == 3

    def test_unclear(self):
        result = score_target_salary("Hmm not sure")
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
            "work_preference": {"score": 5, "rationale": ""},
            "availability": {"score": 5, "rationale": ""},
            "current_salary": {"score": 5, "rationale": ""},
            "target_salary": {"score": 5, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 4.7
        assert result["overall_status"] == "pass"

    def test_flag(self):
        scores = {
            "experience": {"score": 3, "rationale": ""},
            "tech_stack": {"score": 3, "rationale": ""},
            "problem_solving": {"score": 3, "rationale": ""},
            "work_preference": {"score": 3, "rationale": ""},
            "availability": {"score": 2, "rationale": ""},
            "current_salary": {"score": 3, "rationale": ""},
            "target_salary": {"score": 3, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 2.9
        assert result["overall_status"] == "flag"

    def test_fail(self):
        scores = {
            "experience": {"score": 1, "rationale": ""},
            "tech_stack": {"score": 1, "rationale": ""},
            "problem_solving": {"score": 2, "rationale": ""},
            "work_preference": {"score": 1, "rationale": ""},
            "availability": {"score": 1, "rationale": ""},
            "current_salary": {"score": 1, "rationale": ""},
            "target_salary": {"score": 1, "rationale": ""},
        }
        result = compute_overall(scores)
        assert result["overall_score"] == 1.1
        assert result["overall_status"] == "fail"


import os
import json
from fastapi.testclient import TestClient

# Ensure DEMO_MODE is off for most tests
os.environ["DEMO_MODE"] = "false"

from main import app, DATA_FILE

# Import webhook_handler to register its routes on the app
import webhook_handler  # noqa: F401

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_data_file():
    """Remove screenings.json before and after each test."""
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    yield
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)


VALID_PAYLOAD = {
    "candidate_name": "Jane Smith",
    "candidate_phone": "07123456789",
    "role_applied": "software_engineer",
    "consent_given": True,
    "answers": {
        "experience": "I have 5 years of experience as a senior software engineer at a fintech startup",
        "tech_stack": "Python, TypeScript, React, PostgreSQL, Docker, AWS",
        "problem_solving": "We had a memory leak so I profiled the service, debugged the issue, tested a fix, and refactored the module",
        "work_preference": "I prefer hybrid and I'm flexible on that",
        "availability": "I can start in about 1 month",
        "current_salary": "I'm currently on 85k",
        "target_salary": "I'm looking for at least 95k"
    },
    "transcript": "Full transcript of the call..."
}


class TestHealthEndpoint:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSubmitScreening:
    def test_valid_submission(self):
        response = client.post("/submit-screening", json=VALID_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert data["candidate_name"] == "Jane Smith"
        assert data["overall_status"] in ("pass", "flag", "fail")
        assert data["id"].startswith("SCR-")
        assert len(data["scores"]) == 7
        assert all(cat in data["scores"] for cat in ["experience", "tech_stack", "problem_solving", "work_preference", "availability", "current_salary", "target_salary"])
        for cat_score in data["scores"].values():
            assert 1 <= cat_score["score"] <= 5
            assert isinstance(cat_score["rationale"], str)

    def test_missing_fields(self):
        bad_payload = {"candidate_name": "Jane"}
        response = client.post("/submit-screening", json=bad_payload)
        assert response.status_code == 422

    def test_no_consent(self):
        payload = {**VALID_PAYLOAD, "consent_given": False}
        response = client.post("/submit-screening", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "rejected"
        assert data["overall_score"] == 0
        assert data["scores"] == {}


class TestScreeningsEndpoints:
    def test_list_screenings(self):
        client.post("/submit-screening", json=VALID_PAYLOAD)
        response = client.get("/screenings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["candidate_name"] == "Jane Smith"

    def test_get_screening_by_id(self):
        submit_resp = client.post("/submit-screening", json=VALID_PAYLOAD)
        screening_id = submit_resp.json()["id"]
        response = client.get(f"/screenings/{screening_id}")
        assert response.status_code == 200
        assert response.json()["id"] == screening_id

    def test_get_screening_not_found(self):
        response = client.get("/screenings/SCR-ZZZZZ")
        assert response.status_code == 404


RETELL_FUNCTION_PAYLOAD = {
    "name": "submit_screening",
    "call": {
        "call_id": "test-call-123",
        "transcript": "Agent: Hello... Candidate: Hi..."
    },
    "args": {
        "candidate_name": "John Doe",
        "candidate_phone": "07987654321",
        "role_applied": "software_engineer",
        "consent_given": "true",
        "answer_experience": "I have 6 years as a senior engineer",
        "answer_tech_stack": "Python, Go, PostgreSQL, Docker, Kubernetes",
        "answer_problem_solving": "I profiled and debugged a latency issue, then optimized the query layer",
        "answer_work_preference": "I prefer remote but I'm open to hybrid, I'm flexible",
        "answer_availability": "I can start in 2 weeks",
        "answer_current_salary": "I'm on about 90k",
        "answer_target_salary": "Looking for at least 100k"
    }
}


class TestRetellFunctionRouting:
    def test_submit_screening_via_retell(self):
        response = client.post("/retell/function", json=RETELL_FUNCTION_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert data["candidate_name"] == "John Doe"
        assert data["id"].startswith("SCR-")
        assert data["overall_status"] in ("pass", "flag", "fail")
        assert len(data["scores"]) == 7

    def test_unknown_function(self):
        payload = {"name": "unknown_function", "call": {}, "args": {}}
        response = client.post("/retell/function", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestWebhook:
    def test_call_ended_webhook(self):
        webhook_payload = {
            "event": "call_ended",
            "call": {
                "call_id": "webhook-test-123",
                "transcript": "Test transcript from webhook",
                "start_timestamp": 1714608475945,
                "end_timestamp": 1714608491736
            }
        }
        response = client.post("/webhook/retell", json=webhook_payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestDemoMode:
    def test_demo_mode_deterministic(self):
        import main
        original = main.DEMO_MODE
        main.DEMO_MODE = True

        try:
            resp1 = client.post("/submit-screening", json=VALID_PAYLOAD)
            resp2 = client.post("/submit-screening", json=VALID_PAYLOAD)
            data1 = resp1.json()
            data2 = resp2.json()

            assert data1["id"] == data2["id"]
            assert data1["overall_status"] == "pass"
            assert data2["overall_status"] == "pass"
            assert data1["scores"] == data2["scores"]
            assert data1["demo_mode"] is True
        finally:
            main.DEMO_MODE = original


class TestScoringThresholds:
    def test_strong_candidate_passes(self):
        payload = {
            "candidate_name": "Strong Candidate",
            "candidate_phone": "07111111111",
            "role_applied": "software_engineer",
            "consent_given": True,
            "answers": {
                "experience": "I have 8 years as a senior staff engineer at Google",
                "tech_stack": "Python, TypeScript, React, PostgreSQL, Docker, AWS, Kubernetes",
                "problem_solving": "I profiled the service, debugged a memory leak, tested the fix, refactored the module, and optimized the query path",
                "work_preference": "I prefer hybrid but I'm flexible and open to anything",
                "availability": "I can start immediately",
                "current_salary": "I'm on 95k",
                "target_salary": "Looking for at least 110k"
            },
            "transcript": "strong candidate transcript"
        }
        response = client.post("/submit-screening", json=payload)
        data = response.json()
        assert data["overall_status"] == "pass"
        assert data["overall_score"] >= 3.5

    def test_weak_candidate_fails(self):
        payload = {
            "candidate_name": "Weak Candidate",
            "candidate_phone": "07222222222",
            "role_applied": "software_engineer",
            "consent_given": True,
            "answers": {
                "experience": "I like computers",
                "tech_stack": "I use Fortran",
                "problem_solving": "Things were hard but I managed",
                "work_preference": "I dunno",
                "availability": "Not sure really",
                "current_salary": "Not sure",
                "target_salary": "Dunno"
            },
            "transcript": "weak candidate transcript"
        }
        response = client.post("/submit-screening", json=payload)
        data = response.json()
        assert data["overall_status"] == "fail"
        assert data["overall_score"] < 2.5

    def test_mixed_candidate_flags(self):
        payload = {
            "candidate_name": "Mixed Candidate",
            "candidate_phone": "07333333333",
            "role_applied": "software_engineer",
            "consent_given": True,
            "answers": {
                "experience": "I have 2 years as a developer",
                "tech_stack": "Python and JavaScript",
                "problem_solving": "I debugged an issue in production",
                "work_preference": "I prefer remote only, not flexible",
                "availability": "I have a 3 month notice period",
                "current_salary": "I'd prefer not to say",
                "target_salary": "It depends on the role"
            },
            "transcript": "mixed candidate transcript"
        }
        response = client.post("/submit-screening", json=payload)
        data = response.json()
        assert data["overall_status"] == "flag"
        assert 2.5 <= data["overall_score"] < 3.5
