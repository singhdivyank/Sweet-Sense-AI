"""
Trains a multi-class XGBoost classifier on the diabetes dataset produced
by data_pipeline.py, then tunes per-class decision thresholds on the
validation set to improve macro-F1 on the imbalanced label distribution.

Pipeline
--------
  1. Load train / val / test Parquet splits.
  2. Compute balanced sample weights for the training set.
  3. Train XGBClassifier with early stopping monitored on the val set.
  4. Grid-search optimal probability thresholds for classes 1 and 2
     using the validation set.
  5. Evaluate the tuned model on the held-out test set.
  6. Persist the model artefact as JSON.
"""

from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, f1_score
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from ..utils.consts import (
    TARGET_COL,
    NUM_CLASSES,
    N_ESTIMATORS,
    LEARNING_RATE,
    MAX_DEPTH,
    RANDOM_STATE,
)
from ..utils.logger import get_logger
from ..utils.settings import get_settings


class TrainModel:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        # applied to minority classes
        self.threshold_grid: np.ndarray = np.arange(0.10, 0.60, 0.05)
        self._build_model()

    def _build_model(self):
        """Instantiate the XGBClassifier with fixed architecture hyper-parameters."""
        self.clf = XGBClassifier(
            objective="multi:softprob",
            num_class=NUM_CLASSES,
            n_estimators=N_ESTIMATORS,
            learning_rate=LEARNING_RATE,
            max_depth=MAX_DEPTH,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="mlogloss",
            tree_method="hist",  # GPU-compatible; falls back to CPU automatically
            random_state=RANDOM_STATE,
        )

    def _load_data(
        self, split_name: str
    ) -> Tuple[Optional[pd.DataFrame], Optional[pd.Series]]:
        try:
            path = self.settings.output_dir / f"{split_name}.parquet"
            df = pd.read_parquet(path)
            X = df.drop(columns=[TARGET_COL])
            y = df[TARGET_COL]
            self.logger.info(
                "Loaded %-5s → %d rows, %d features", split_name, len(df), X.shape[1]
            )
            return X, y
        except Exception as e:
            self.logger.error("Unable to load dataset from given path: %s", str(e))
            return None, None

    def get_datasets(self):
        """Load train, val, and test datasets"""
        self.X_train, self.y_train = self._load_data("train")
        self.X_val, self.y_val = self._load_data("val")
        self.X_test, self.y_test = self._load_data("test")

    def train(self):
        """
        Fit the model with balanced sample weights.
        Validation loss is monitored but early stopping is left to the caller
        (pass early_stopping_rounds via model kwargs if desired).
        """

        try:
            if self.X_train is None and self.y_train is None:
                self.logger.error("No training set found ... Exiting")
                raise

            sample_weight = compute_sample_weight(
                class_weight="balanced", y=self.y_train
            )
            self.logger.info("Training XGBClassifier")
            self.clf.fit(
                self.X_train,
                self.y_train,
                sample_weight=sample_weight,
                eval_set=[(self.X_val, self.y_val)],
                verbose=False,
            )

            self.logger.info(
                "Training complete. Best iteration: %s", self.clf.best_iteration
            )
        except Exception as e:
            self.logger.error("Model training unsuccessful: %s", str(e))
            return

    def _make_pred(
        self, probs: np.ndarray, thresh_class1: float, thresh_class2: float
    ) -> np.ndarray:
        """
        Apply per-class probability thresholds to a (n_samples, 3) probability
        matrix.  Evaluation order: class 1 → class 2 → class 0 (majority)
        """

        preds = np.zeros(len(probs), dtype=int)
        mask2 = probs[:, 2] >= thresh_class2
        mask1 = probs[:, 1] >= thresh_class1

        preds[mask2] = 2
        preds[mask1] = 1
        return preds

    def optimise_thresholds(self) -> Tuple[float, float]:
        """Grid-search (thresh_class1, thresh_class2) on the validation set."""

        best_f1, best_t1, best_t2 = 0.0, 0.0, 0.0
        val_probs = self.clf.predict_proba(self.X_val)

        for t1 in self.threshold_grid:
            for t2 in self.threshold_grid:
                preds = self._make_pred(val_probs, thresh_class1=t1, thresh_class2=t2)
                score = f1_score(self.y_val, preds, average="macro", zero_division=0)

                if score > best_f1:
                    best_f1, best_t1, best_t2 = score, t1, t2

        self.logger.info(
            "Threshold search complete | best macro-F1 = %.4f  (t1=%.2f, t2=%.2f)",
            best_f1,
            best_t1,
            best_t2,
        )
        return best_t1, best_t2

    def evaluate_model(self, t1: float, t2: float):
        """Log classification report and macro-F1 for a given split."""

        probs = self.clf.predict_proba(self.X_test)
        preds = self._make_pred(probs, thresh_class1=t1, thresh_class2=t2)
        macro_f1 = f1_score(self.y_test, preds, average="macro", zero_division=0)

        self.logger.info("=== Test Results ===")
        self.logger.info(
            "\n%s", classification_report(self.y_test, preds, zero_division=0)
        )
        self.logger.info("Macro F1: %.4f", macro_f1)

    def train_model(self):
        """Main function to execute model training"""

        try:
            self.get_datasets()
            self.train()
            best_t1, best_t2 = self.optimise_thresholds()
            self.evaluate_model(t1=best_t1, t2=best_t2)
        except Exception as e:
            self.logger.error("Error in model training: %s", str(e))
