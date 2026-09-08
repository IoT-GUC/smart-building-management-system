from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings


def test_webhook_rejects_when_secret_not_configured(client: TestClient, monkeypatch):
    """
    An unset secret must reject, not wave the request through.

    The check used to be `if expected:` -- and the secret is empty by default,
    so the signature verification was skipped entirely and anyone could POST
    arbitrary telemetry into the processing queue.
    """
    monkeypatch.setattr(settings, "TTN_WEBHOOK_SECRET", "")

    response = client.post("/ttn-webhook", json={"end_device_ids": {}})
    assert response.status_code == 503, response.text
    assert "TTN_WEBHOOK_SECRET" in response.text


def test_webhook_rejects_wrong_secret(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "TTN_WEBHOOK_SECRET", "the-real-secret")

    response = client.post(
        "/ttn-webhook",
        json={"end_device_ids": {}},
        headers={"X-Webhook-Secret": "not-the-secret"},
    )
    assert response.status_code == 401, response.text


def test_webhook_rejects_missing_header(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "TTN_WEBHOOK_SECRET", "the-real-secret")

    response = client.post("/ttn-webhook", json={"end_device_ids": {}})
    assert response.status_code == 401, response.text


def test_webhook_accepts_correct_secret(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "TTN_WEBHOOK_SECRET", "the-real-secret")

    response = client.post(
        "/ttn-webhook",
        json={"end_device_ids": {}},
        headers={"X-Webhook-Secret": "the-real-secret"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "queued"
