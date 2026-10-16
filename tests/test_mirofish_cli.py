
import json

import pytest

from churn_targeting.simulation import mirofish_cli
from churn_targeting.simulation.mirofish_health import (
    MiroFishConnectionError,
)


def test_cli_success(monkeypatch, capsys):
    """CLI returns success when MiroFish is healthy."""

    def fake_check_health(self):
        return {
            "status": "ok",
            "service": "MiroFish Backend",
            "endpoint": "/health",
        }

    monkeypatch.setattr(
        mirofish_cli.MiroFishHealthClient,
        "check_health",
        fake_check_health,
    )
    monkeypatch.setattr("sys.argv", ["mirofish_cli"])

    assert mirofish_cli.main() == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ok"


def test_cli_unavailable(monkeypatch, capsys):
    """CLI returns an error when MiroFish is unavailable."""

    def fake_check_health(self):
        raise MiroFishConnectionError("Health check failed.")

    monkeypatch.setattr(
        mirofish_cli.MiroFishHealthClient,
        "check_health",
        fake_check_health,
    )
    monkeypatch.setattr("sys.argv", ["mirofish_cli"])

    assert mirofish_cli.main() == 1

    output = json.loads(capsys.readouterr().err)
    assert output["status"] == "unavailable"


def test_cli_rejects_invalid_timeout(monkeypatch):
    """CLI rejects a timeout of zero before making a request."""

    monkeypatch.setattr(
        "sys.argv",
        ["mirofish_cli", "--timeout", "0"],
    )

    with pytest.raises(SystemExit) as exc_info:
        mirofish_cli.main()

    assert exc_info.value.code == 2
