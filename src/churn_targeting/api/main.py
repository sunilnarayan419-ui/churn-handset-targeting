"""FastAPI application factory. Dependencies (model, data frame, graph store) can be injected for tests."""

import math
import secrets
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Query

from .. import __version__
from ..analytics import DIMENSIONS, churn_by_segment
from ..config import Settings
from ..finance import economics
from ..modeling import ModelBundle, load_bundle, missing_feature_count, score_frame
from ..pilot import n_per_arm
from .schemas import (
    BatchScoreRequest,
    BatchScoreResponse,
    CohortResponse,
    EconomicsRequest,
    EconomicsResponse,
    PilotRequest,
    PilotResponse,
    ScoreRequest,
    ScoreResponse,
)


def create_app(settings: Settings | None = None, bundle: ModelBundle | None = None,
               frame: pd.DataFrame | None = None, store=None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.bundle is None and settings.model_path.exists():
            app.state.bundle = load_bundle(settings.model_path)
        if app.state.store is None and settings.neo4j_uri:
            from ..graph import GraphStore

            app.state.store = GraphStore(settings.neo4j_uri, settings.neo4j_user,
                                         settings.neo4j_password, settings.neo4j_database)
            app.state.owns_store = True
        yield
        if getattr(app.state, "owns_store", False):
            app.state.store.close()

    app = FastAPI(title="Churn targeting API", version=__version__, lifespan=lifespan,
                  description="Risk scoring, retention economics, pilot sizing and cohort analytics.")
    app.state.bundle, app.state.frame, app.state.store = bundle, frame, store

    def require_key(x_api_key: str | None = Header(default=None)) -> None:
        if settings.api_key and not (x_api_key and secrets.compare_digest(x_api_key, settings.api_key)):
            raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")

    def get_bundle() -> ModelBundle:
        if app.state.bundle is None:
            raise HTTPException(status_code=503, detail="model not loaded; run `churn-targeting train`")
        return app.state.bundle

    secured = [Depends(require_key)]

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__, "model_loaded": app.state.bundle is not None,
                "graph_enabled": app.state.store is not None}

    @app.get("/model", dependencies=secured)
    def model_info(b: ModelBundle = Depends(get_bundle)) -> dict:
        return b.metadata

    @app.post("/score", response_model=ScoreResponse, dependencies=secured)
    def score(req: ScoreRequest, base_rate: float = Query(default=settings.base_rate, gt=0, lt=1),
              b: ModelBundle = Depends(get_bundle)) -> ScoreResponse:
        return _score_many(b, [req.customer], base_rate)[0]

    @app.post("/score/batch", response_model=BatchScoreResponse, dependencies=secured)
    def score_batch(req: BatchScoreRequest, base_rate: float = Query(default=settings.base_rate, gt=0, lt=1),
                    b: ModelBundle = Depends(get_bundle)) -> BatchScoreResponse:
        return BatchScoreResponse(results=_score_many(b, req.customers, base_rate))

    @app.post("/finance/economics", response_model=EconomicsResponse, dependencies=secured)
    def finance(req: EconomicsRequest) -> EconomicsResponse:
        try:
            result = economics(**req.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if math.isinf(result["breakeven_save_rate"]):      # no value per save: JSON cannot carry inf
            result["breakeven_save_rate"] = None
        return EconomicsResponse(**result)

    @app.post("/pilot/size", response_model=PilotResponse, dependencies=secured)
    def pilot(req: PilotRequest) -> PilotResponse:
        n = n_per_arm(req.baseline_churn_prob, req.relative_effect, req.alpha, req.power)
        return PilotResponse(n_per_arm=n, total_customers=2 * n)

    @app.get("/cohorts/{dimension}", response_model=CohortResponse, dependencies=secured)
    def cohorts(dimension: str) -> CohortResponse:
        if dimension not in DIMENSIONS:
            raise HTTPException(status_code=404, detail=f"unknown dimension; choose from {sorted(DIMENSIONS)}")
        if app.state.store is not None:
            table, source = app.state.store.churn_by(dimension), "neo4j"
        elif app.state.frame is not None:
            table, source = churn_by_segment(app.state.frame, dimension), "pandas"
        else:
            raise HTTPException(status_code=503, detail="no graph store or customer data configured")
        return CohortResponse(dimension=dimension, source=source, segments=table.to_dict("records"))

    return app


def _score_many(b: ModelBundle, customers: list[dict], base_rate: float) -> list[ScoreResponse]:
    frame = pd.DataFrame(customers)
    scored = score_frame(b, frame, base_rate)
    missing = missing_feature_count(b, frame)
    return [
        ScoreResponse(
            churn_probability_calibrated=float(scored["churn_prob_calibrated"].iloc[i]),
            churn_probability_at_base_rate=float(scored["churn_prob_at_base_rate"].iloc[i]),
            base_rate=base_rate,
            missing_features=int(missing.iloc[i]),
        )
        for i in range(len(frame))
    ]
