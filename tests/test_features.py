from churn_targeting.features import FAIRNESS_EXCLUDED, build_pipeline, column_types, select_features


def test_select_features_excludes_id_target_and_protected(customers):
    X, y = select_features(customers)
    assert "Customer_ID" not in X and "churn" not in X
    assert all(c not in X for c in FAIRNESS_EXCLUDED)
    assert set(y.unique()) <= {0, 1}
    assert len(X) == len(y) == len(customers)


def test_column_types_partition(customers):
    X, _ = select_features(customers)
    cat, num = column_types(X)
    assert set(cat) == {"area", "crclscod"}
    assert set(cat).isdisjoint(num) and len(cat) + len(num) == X.shape[1]


def test_pipeline_fits_and_predicts_with_missing_values(customers):
    X, y = select_features(customers)
    cat, num = column_types(X)
    pipe = build_pipeline(cat, num, params={"learning_rate": 0.1, "max_leaf_nodes": 8,
                                            "min_samples_leaf": 20, "l2_regularization": 0.0})
    pipe.fit(X, y)
    proba = pipe.predict_proba(X.head(10))
    assert proba.shape == (10, 2)
