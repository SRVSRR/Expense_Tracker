"""ML-based transaction categorization using LightGBM.

Falls back to rule-based keyword matching when:
- No trained model exists (cold start)
- Fewer than 50 training samples
- Model confidence is below threshold
"""
import os
import json
import logging
from pathlib import Path

import numpy as np
import lightgbm as lgb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder

from app.services.categorize import suggest_category, get_all_categories, KEYWORD_MAP

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "saved_models"
MODEL_PATH = MODEL_DIR / "categorizer_model.json"
VECTORIZER_PATH = MODEL_DIR / "vectorizer.json"
LABEL_ENCODER_PATH = MODEL_DIR / "label_encoder.json"
META_PATH = MODEL_DIR / "model_meta.json"

MIN_TRAINING_SAMPLES = 30
CONFIDENCE_THRESHOLD = 0.55


class TransactionCategorizer:
    """LightGBM-based transaction categorizer with rule-based fallback."""

    def __init__(self):
        self.model: lgb.Booster | None = None
        self.vectorizer: TfidfVectorizer | None = None
        self.label_encoder: LabelEncoder | None = None
        self.is_trained = False
        self.training_samples = 0
        self._load_model()

    def _build_text(self, description: str, merchant: str | None = None) -> str:
        """Combine description and merchant into a single text field."""
        parts = [description.strip()]
        if merchant and merchant.strip():
            parts.append(merchant.strip())
        return " ".join(parts)

    def _load_model(self):
        """Load saved model from disk if available."""
        if not all(p.exists() for p in [MODEL_PATH, VECTORIZER_PATH, LABEL_ENCODER_PATH, META_PATH]):
            return

        try:
            self.model = lgb.Booster(model_file=str(MODEL_PATH))

            with open(VECTORIZER_PATH, "r") as f:
                vec_data = json.load(f)
            self.vectorizer = TfidfVectorizer(
                vocabulary=vec_data["vocabulary"],
                ngram_range=tuple(vec_data["ngram_range"]),
                max_features=vec_data["max_features"],
                sublinear_tf=True,
            )
            # Fit vectorizer on dummy data to restore state
            self.vectorizer.fit(["dummy"])

            with open(LABEL_ENCODER_PATH, "r") as f:
                le_data = json.load(f)
            self.label_encoder = LabelEncoder()
            self.label_encoder.classes_ = np.array(le_data["classes"])

            with open(META_PATH, "r") as f:
                meta = json.load(f)
            self.training_samples = meta.get("training_samples", 0)
            self.is_trained = True

            logger.info(
                "Loaded categorizer model (%d training samples)",
                self.training_samples,
            )
        except Exception as e:
            logger.warning("Failed to load categorizer model: %s", e)
            self.is_trained = False

    def _save_model(self):
        """Persist model to disk."""
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        self.model.save_model(str(MODEL_PATH))

        with open(VECTORIZER_PATH, "w") as f:
            json.dump({
                "vocabulary": {k: int(v) for k, v in self.vectorizer.vocabulary_.items()},
                "ngram_range": list(self.vectorizer.ngram_range),
                "max_features": self.vectorizer.max_features,
            }, f)

        with open(LABEL_ENCODER_PATH, "w") as f:
            json.dump({"classes": self.label_encoder.classes_.tolist()}, f)

        with open(META_PATH, "w") as f:
            json.dump({"training_samples": self.training_samples}, f)

        logger.info("Saved categorizer model (%d samples)", self.training_samples)

    def train(self, texts: list[str], labels: list[str]) -> dict:
        """Train the LightGBM model on correction data.

        Returns training stats.
        """
        if len(texts) < MIN_TRAINING_SAMPLES:
            return {
                "status": "insufficient_data",
                "samples": len(texts),
                "required": MIN_TRAINING_SAMPLES,
            }

        # Build features
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=2000,
            sublinear_tf=True,
            analyzer="word",
        )
        X = self.vectorizer.fit_transform(texts).toarray()

        # Encode labels
        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(labels)

        # Train LightGBM
        train_data = lgb.Dataset(X, label=y)
        params = {
            "objective": "multiclass",
            "num_class": len(self.label_encoder.classes_),
            "metric": "multi_logloss",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "min_child_samples": 5,
        }
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=200,
            valid_sets=[train_data],
            callbacks=[lgb.log_evaluation(0)],
        )

        self.training_samples = len(texts)
        self.is_trained = True
        self._save_model()

        # Compute training accuracy
        preds = self.model.predict(X)
        pred_labels = np.argmax(preds, axis=1)
        accuracy = float(np.mean(pred_labels == y))

        return {
            "status": "trained",
            "samples": len(texts),
            "accuracy": round(accuracy, 4),
            "num_classes": len(self.label_encoder.classes_),
        }

    def predict(self, description: str, merchant: str | None = None) -> tuple[str | None, str, float]:
        """Predict category for a transaction.

        Returns (category, confidence_level, probability).
        Falls back to rule-based if model is unavailable or confidence is low.
        """
        text = self._build_text(description, merchant)

        # Try ML model first
        if self.is_trained and self.model and self.vectorizer and self.label_encoder:
            try:
                X = self.vectorizer.transform([text]).toarray()
                probs = self.model.predict(X)[0]
                pred_idx = int(np.argmax(probs))
                prob = float(probs[pred_idx])
                category = self.label_encoder.inverse_transform([pred_idx])[0]

                if prob >= CONFIDENCE_THRESHOLD:
                    if prob >= 0.8:
                        confidence = "high"
                    elif prob >= 0.65:
                        confidence = "medium"
                    else:
                        confidence = "low"
                    return category, confidence, prob

                # Low confidence — fall through to rule-based
            except Exception as e:
                logger.warning("ML prediction failed: %s", e)

        # Fallback: rule-based keyword matching
        rule_category = suggest_category(description, merchant)
        if rule_category:
            # Determine rule-based confidence
            text_lower = text.lower()
            keywords = KEYWORD_MAP.get(rule_category, [])
            max_match_len = max((len(kw) for kw in keywords if kw in text_lower), default=0)
            if max_match_len >= 8:
                confidence = "high"
            elif max_match_len >= 4:
                confidence = "medium"
            else:
                confidence = "low"
            return rule_category, confidence, 0.0

        return None, "none", 0.0


# Singleton instance — load model once at module level
_categorizer: TransactionCategorizer | None = None


def get_categorizer() -> TransactionCategorizer:
    global _categorizer
    if _categorizer is None:
        _categorizer = TransactionCategorizer()
    return _categorizer
