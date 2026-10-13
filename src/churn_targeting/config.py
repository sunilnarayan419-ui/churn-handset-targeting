"""Runtime settings, read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

SEED = 42
# Anchor for the realistic monthly churn rate (about 1%); an assumption, not Company A's measured rate.
DEFAULT_BASE_RATE = 0.0099


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("data/raw")
    model_path: Path = Path("models/churn_model.joblib")
    base_rate: float = DEFAULT_BASE_RATE
    api_key: str | None = None
    neo4j_uri: str | None = None
    neo4j_user: str = "neo4j"
    neo4j_password: str | None = None
    neo4j_database: str = "neo4j"

    @classmethod
    def from_env(cls) -> Settings:
        env = os.environ
        return cls(
            data_dir=Path(env.get("DATA_DIR", "data/raw")),
            model_path=Path(env.get("MODEL_PATH", "models/churn_model.joblib")),
            base_rate=float(env.get("BASE_RATE", DEFAULT_BASE_RATE)),
            api_key=env.get("API_KEY") or None,
            neo4j_uri=env.get("NEO4J_URI") or None,
            neo4j_user=env.get("NEO4J_USER", "neo4j"),
            neo4j_password=env.get("NEO4J_PASSWORD") or None,
            neo4j_database=env.get("NEO4J_DATABASE", "neo4j"),
        )
