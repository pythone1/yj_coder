"""
LSTM predictive maintenance template.

Input CSV requirements:
- equipment_id: machine identifier
- timestamp: sortable event/sample time
- target: 0/1 label, e.g. failure within forecast horizon
- feature columns: numeric sensor/process features from MES/SCADA/PLC

Run:
    conda run -n LSTM python lstm_predictive_maintenance_template.py data.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow import keras
from tensorflow.keras import layers


WINDOW = 120
STEP = 5
FORECAST_TARGET = "target"
ID_COL = "equipment_id"
TIME_COL = "timestamp"


def build_windows(df: pd.DataFrame, feature_cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []
    for _, g in df.sort_values([ID_COL, TIME_COL]).groupby(ID_COL):
        values = g[feature_cols].to_numpy(dtype="float32")
        labels = g[FORECAST_TARGET].to_numpy(dtype="int32")
        if len(g) < WINDOW:
            continue
        for end in range(WINDOW, len(g) + 1, STEP):
            xs.append(values[end - WINDOW:end])
            ys.append(labels[end - 1])
    if not xs:
        raise ValueError("No windows built. Check data length per equipment_id and WINDOW.")
    return np.stack(xs), np.array(ys)


def main(csv_path: str):
    df = pd.read_csv(csv_path)
    required = {ID_COL, TIME_COL, FORECAST_TARGET}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    feature_cols = [
        c for c in df.columns
        if c not in {ID_COL, TIME_COL, FORECAST_TARGET}
        and pd.api.types.is_numeric_dtype(df[c])
    ]
    if not feature_cols:
        raise ValueError("No numeric feature columns found.")

    df = df.sort_values([ID_COL, TIME_COL]).copy()
    scaler = StandardScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols].fillna(method="ffill").fillna(0))

    x, y = build_windows(df, feature_cols)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    model = keras.Sequential([
        layers.Input(shape=(WINDOW, len(feature_cols))),
        layers.Masking(mask_value=0.0),
        layers.LSTM(64, return_sequences=True),
        layers.Dropout(0.2),
        layers.LSTM(32),
        layers.Dropout(0.2),
        layers.Dense(16, activation="relu"),
        layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="binary_crossentropy",
        metrics=[keras.metrics.AUC(name="auc"), keras.metrics.Recall(name="recall")],
    )
    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_auc", mode="max", patience=8, restore_best_weights=True),
        keras.callbacks.ModelCheckpoint("lstm_predictive_maintenance.keras", monitor="val_auc", mode="max", save_best_only=True),
    ]
    model.fit(
        x_train, y_train,
        validation_split=0.2,
        epochs=80,
        batch_size=128,
        callbacks=callbacks,
        verbose=2,
    )

    pred = model.predict(x_test).ravel()
    print("AUC:", roc_auc_score(y_test, pred) if len(set(y_test)) > 1 else "undefined")
    print(classification_report(y_test, (pred >= 0.5).astype(int), digits=4))
    print("Saved: lstm_predictive_maintenance.keras")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python lstm_predictive_maintenance_template.py data.csv")
    main(sys.argv[1])
