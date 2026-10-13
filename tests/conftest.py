"""Shared fixtures. All data is synthetic: no assignment data is needed to run the test suite."""

import numpy as np
import pandas as pd
import pytest

from churn_targeting.modeling import train

FAST_PARAMS = {"learning_rate": 0.1, "max_leaf_nodes": 15, "min_samples_leaf": 20, "l2_regularization": 0.0}


def make_customers(n: int = 3000, seed: int = 0) -> pd.DataFrame:
    """Customers with a planted churn step after 300 days of handset age, plus noise and some missing values."""
    rng = np.random.default_rng(seed)
    months = rng.integers(3, 60, n)
    eqpdays = rng.integers(0, 900, n)
    change = rng.normal(0, 150, n)
    z = -0.5 + 1.2 * (eqpdays > 300) - 0.015 * (months - 30) - 0.002 * change
    churn = (rng.random(n) < 1 / (1 + np.exp(-z))).astype(int)
    df = pd.DataFrame(
        {
            "Customer_ID": 1_000_001 + np.arange(n),
            "churn": churn,
            "eqpdays": eqpdays,
            "months": months,
            "rev_Mean": rng.gamma(4, 13, n),
            "mou_Mean": rng.gamma(3, 150, n),
            "change_mou": change,
            "hnd_price": rng.choice([29.99, 59.99, 99.99, 149.99, 299.99], n),
            "area": rng.choice(["NEW YORK CITY AREA", "DALLAS AREA", "CHICAGO AREA"], n),
            "crclscod": rng.choice(["A", "B", "C", "D"], n),
            "ethnic": rng.choice(["N", "S", "O"], n),
        }
    )
    df.loc[df.sample(frac=0.03, random_state=seed).index, "rev_Mean"] = np.nan
    return df


@pytest.fixture(scope="session")
def customers() -> pd.DataFrame:
    return make_customers()


@pytest.fixture
def client_record(customers):
    client = customers[["Customer_ID", "area", "crclscod", "ethnic", "hnd_price"]].copy()
    record = customers[["Customer_ID", "churn", "eqpdays", "months", "rev_Mean", "mou_Mean", "change_mou"]].copy()
    return client, record


@pytest.fixture(scope="session")
def trained(customers):
    return train(customers, params=FAST_PARAMS)
