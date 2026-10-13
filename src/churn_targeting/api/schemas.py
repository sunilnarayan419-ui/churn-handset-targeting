"""Request and response models (pydantic v2)."""

from pydantic import BaseModel, Field

FeatureValue = float | int | str | None


class ScoreRequest(BaseModel):
    customer: dict[str, FeatureValue] = Field(
        description="Raw customer fields keyed by column name (see docs/DATA_CARD.md). Missing fields are "
        "treated as unknown; unknown fields are ignored."
    )


class BatchScoreRequest(BaseModel):
    customers: list[dict[str, FeatureValue]] = Field(min_length=1, max_length=5000)


class ScoreResponse(BaseModel):
    churn_probability_calibrated: float = Field(description="Probability on the (enriched) training-sample scale")
    churn_probability_at_base_rate: float = Field(description="Probability rescaled to the requested monthly base rate")
    base_rate: float
    missing_features: int = Field(description="Model inputs not supplied in the request")


class BatchScoreResponse(BaseModel):
    results: list[ScoreResponse]


class EconomicsRequest(BaseModel):
    n_treated: int = Field(gt=0, description="Customers contacted per wave")
    churn_prob: float = Field(gt=0, lt=1, description="Real-world monthly churn probability of the contacted group")
    avg_monthly_rev: float = Field(ge=0)
    save_rate: float = Field(ge=0, le=1, description="Incremental share of would-be churners the contact keeps")
    margin: float = Field(ge=0, le=1)
    months: int = Field(gt=0)
    contact_cost: float = Field(ge=0)
    accept_rate: float = Field(default=0.0, ge=0, le=1)
    incentive: float = Field(default=0.0, ge=0)


class EconomicsResponse(BaseModel):
    treated: float
    would_be_churners: float
    saved: float
    value_per_save: float
    gross_benefit: float
    variable_cost: float
    net_variable_benefit: float
    breakeven_save_rate: float | None = Field(description="null when a contact can never pay back (zero value per save)")


class PilotRequest(BaseModel):
    baseline_churn_prob: float = Field(gt=0, lt=1)
    relative_effect: float = Field(gt=0, lt=1)
    alpha: float = Field(default=0.05, gt=0, lt=1)
    power: float = Field(default=0.80, gt=0, lt=1)


class PilotResponse(BaseModel):
    n_per_arm: int
    total_customers: int


class Segment(BaseModel):
    segment: str
    customers: int
    churn_rate: float


class CohortResponse(BaseModel):
    dimension: str
    source: str
    segments: list[Segment]
