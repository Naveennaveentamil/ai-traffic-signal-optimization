"""
Train RandomForest on dummy vehicle_count vs congestion; save model; predict congestion score + level.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# Paths relative to this package (works regardless of cwd)
_AI_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH = os.path.join(_AI_DIR, "models", "congestion_rf.joblib")
_DATASET_PATH = os.path.join(_AI_DIR, "dataset", "traffic_data.csv")


def _ensure_dummy_dataset() -> str:
    """Create synthetic CSV if missing: vehicle_count vs congestion (0-100)."""
    os.makedirs(os.path.dirname(_DATASET_PATH), exist_ok=True)
    if os.path.isfile(_DATASET_PATH):
        return _DATASET_PATH
    rng = np.random.default_rng(42)
    rows = []
    for _ in range(200):
        v = int(rng.integers(0, 80))
        noise = rng.normal(0, 5)
        congestion = float(np.clip(0.8 * v + 5 + noise, 0, 100))
        rows.append({"vehicle_count": v, "congestion": congestion})
    pd.DataFrame(rows).to_csv(_DATASET_PATH, index=False)
    return _DATASET_PATH


def load_or_train_model() -> RandomForestRegressor:
    """Train RandomForest on dummy data and persist with joblib."""
    csv_path = _ensure_dummy_dataset()
    df = pd.read_csv(csv_path)
    X = df[["vehicle_count"]].values
    y = df["congestion"].values

    model = RandomForestRegressor(
        n_estimators=120,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)

    os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
    joblib.dump(model, _MODEL_PATH)
    return model


def load_model_if_exists() -> Optional[RandomForestRegressor]:
    if os.path.isfile(_MODEL_PATH):
        return joblib.load(_MODEL_PATH)
    return load_or_train_model()


def predict_congestion(
    model: RandomForestRegressor,
    features: Optional[Dict[str, Any]],
    last_vehicle_count: Optional[int] = None,
) -> Tuple[float, str]:
    """
    Predict congestion score (0-100) and level LOW/MEDIUM/HIGH.
    If features dict has 'vehicle_count', use it; else last_vehicle_count.
    """
    vc: int
    if features and isinstance(features, dict) and "vehicle_count" in features:
        vc = int(features["vehicle_count"])
    elif last_vehicle_count is not None:
        vc = int(last_vehicle_count)
    else:
        vc = 15

    X = np.array([[vc]], dtype=float)
    pred = float(model.predict(X)[0])
    pred = max(0.0, min(100.0, pred))

    if pred < 33:
        level = "LOW"
    elif pred < 66:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return pred, level
