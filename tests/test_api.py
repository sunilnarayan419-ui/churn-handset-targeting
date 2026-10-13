"""API tests. Skipped automatically when the 'api' extra (fastapi, httpx) is not installed."""

import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from churn_targeting.api.main import create_app  # noqa: E402
from churn_targeting.config import Settings  # noqa: E402


@pytest.fixture
def client(trained, customers):
    return TestClient(create_app(Settings(), bundle=trained.bundle, frame=customers))


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["model_loaded"] is True


def test_model_info_reports_metrics_and_exclusions(client):
    body = client.get("/model").json()
    assert body["metrics_test"]["roc_auc"] > 0.6 and "ethnic" in body["excluded_features"]


def test_score_single_customer(client, customers):
    row = json.loads(customers.iloc[[0]].drop(columns=["Customer_ID", "churn"]).to_json(orient="records"))[0]
    r = client.post("/score", json={"customer": row})
    assert r.status_code == 200
    body = r.json()
    assert 0 < body["churn_probability_at_base_rate"] < body["churn_probability_calibrated"] < 1
    assert body["missing_features"] == 0


def test_score_counts_missing_features(client):
    r = client.post("/score", json={"customer": {"eqpdays": 350}})
    assert r.status_code == 200 and r.json()["missing_features"] > 0


def test_score_batch_and_limits(client, customers):
    rows = customers.head(3)[["eqpdays", "months"]].to_dict("records")
    assert len(client.post("/score/batch", json={"customers": rows}).json()["results"]) == 3
    assert client.post("/score/batch", json={"customers": []}).status_code == 422


def test_base_rate_validation(client):
    assert client.post("/score?base_rate=1.5", json={"customer": {"eqpdays": 1}}).status_code == 422


def test_economics_endpoint_matches_hand_calculation(client):
    body = client.post("/finance/economics", json={
        "n_treated": 1000, "churn_prob": 0.05, "avg_monthly_rev": 50, "save_rate": 0.1,
        "margin": 0.4, "months": 12, "contact_cost": 0.5}).json()
    assert body["net_variable_benefit"] == pytest.approx(700)


def test_economics_rejects_invalid_probability(client):
    r = client.post("/finance/economics", json={
        "n_treated": 10, "churn_prob": 2, "avg_monthly_rev": 1, "save_rate": 0.1,
        "margin": 0.4, "months": 12, "contact_cost": 0.5})
    assert r.status_code == 422


def test_pilot_size_endpoint(client):
    body = client.post("/pilot/size", json={"baseline_churn_prob": 0.1, "relative_effect": 0.2}).json()
    assert 3100 <= body["n_per_arm"] <= 3300 and body["total_customers"] == 2 * body["n_per_arm"]


def test_cohorts_from_pandas_fallback(client, customers):
    body = client.get("/cohorts/handset_age").json()
    assert body["source"] == "pandas" and sum(s["customers"] for s in body["segments"]) == len(customers)
    assert client.get("/cohorts/nope").status_code == 404


def test_scoring_without_model_returns_503(customers):
    c = TestClient(create_app(Settings(), bundle=None, frame=customers))
    assert c.post("/score", json={"customer": {"eqpdays": 1}}).status_code == 503
    assert c.get("/health").json()["model_loaded"] is False


def test_api_key_is_enforced_when_configured(trained):
    c = TestClient(create_app(Settings(api_key="secret"), bundle=trained.bundle))
    assert c.get("/health").status_code == 200                        # health stays open for probes
    assert c.get("/model").status_code == 401
    assert c.get("/model", headers={"X-API-Key": "wrong"}).status_code == 401
    assert c.get("/model", headers={"X-API-Key": "secret"}).status_code == 200


def test_economics_with_zero_revenue_returns_null_break_even(client):
    body = client.post("/finance/economics", json={
        "n_treated": 10, "churn_prob": 0.05, "avg_monthly_rev": 0, "save_rate": 0.1,
        "margin": 0.4, "months": 12, "contact_cost": 0.5}).json()
    assert body["breakeven_save_rate"] is None
