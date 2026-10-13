"""Needs a running Neo4j: set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD (CI starts one as a service)."""

import os

import pandas as pd
import pytest

pytestmark = pytest.mark.integration
pytest.importorskip("neo4j")

from churn_targeting.analytics import churn_by_segment  # noqa: E402
from churn_targeting.graph import GraphStore  # noqa: E402

needs_db = pytest.mark.skipif(not os.environ.get("NEO4J_URI"), reason="NEO4J_URI not set")


@needs_db
@pytest.mark.parametrize("dimension", ["handset_age", "tenure", "price_tier", "area", "credit_class"])
def test_graph_matches_pandas(customers, dimension):
    with GraphStore(os.environ["NEO4J_URI"], os.environ.get("NEO4J_USER", "neo4j"),
                    os.environ["NEO4J_PASSWORD"]) as g:
        g.ensure_schema()
        g.clear()
        g.load(customers)
        assert g.customer_count() == len(customers)
        from_graph = g.churn_by(dimension)
        g.clear()
    expected = churn_by_segment(customers, dimension)
    pd.testing.assert_frame_equal(
        from_graph.reset_index(drop=True), expected.reset_index(drop=True), check_dtype=False, rtol=1e-9
    )
