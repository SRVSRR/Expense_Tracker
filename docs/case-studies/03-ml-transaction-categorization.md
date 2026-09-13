# Transaction Categorization That Survives Cold Starts

**Reading time:** 7 minutes  
**Audience:** Data science, machine learning engineering, and hiring managers  
**Repository evidence:** `backend/app/ml/categorizer.py`, `backend/app/services/categorize.py`, `backend/app/routes/categorize.py`

## Problem

Manual finance tracking breaks down when users must categorize every transaction by hand. Free-text descriptions such as “Starbucks,” “Uber trip,” or “monthly electricity bill” are noisy, inconsistent, and often ambiguous. Merchant text may be abbreviated, misspelled, or missing entirely.

A purely ML-based solution has its own failure mode: cold starts. A newly deployed model has no training data. Even a trained model can encounter unfamiliar merchants and produce low-confidence guesses. For personal-finance data, a confident wrong answer is worse than an explicit fallback.

The goal was therefore not only accuracy, but graceful degradation.

## Approach

I built a hybrid categorization system with three cooperating layers.

### 1. Rule-based baseline

Keyword matching provides an immediate, explainable fallback. It maps merchant and description substrings to categories and assigns confidence based on match strength.

This ensures the product works on day one, before any training data exists. It also provides a transparent baseline against which ML behavior can be compared.

The baseline also preserves auditability. A suggested category can be traced to an input substring rather than an opaque model weight. That property is especially useful for finance workflows, where users reasonably ask why a transaction received a particular label.

Relevant code:

- `../../backend/app/services/categorize.py`

### 2. LightGBM classifier with TF-IDF features

When enough correction data exists, the system trains a LightGBM multiclass classifier on:

- Transaction descriptions
- Merchant names
- TF-IDF word features with one- to three-word n-grams
- Up to 2,000 features with sublinear term frequency scaling
- Label-encoded category targets

Training requires at least 30 samples. The implementation uses 200 boosting rounds and reports training accuracy, sample count, and class count. The model, vectorizer, label encoder, and training metadata are persisted together so training remains reproducible and reloadable. Reloading reconstructs the same vocabulary, label mapping, and sample-count metadata; a missing or corrupt artifact returns the system to the rule-based fallback instead of serving an inconsistent model.

Relevant code:

- `../../backend/app/ml/categorizer.py`

### 3. Confidence-gated fallback

The prediction path follows a deliberate hierarchy:

1. Use the ML model when it is trained and confident.
2. Fall back to keyword rules when:
   - No trained model exists.
   - There are too few training samples.
   - The model’s confidence is below the threshold.
3. Return no suggestion when neither layer has a credible answer.

The confidence threshold is currently `0.55`. High-confidence behavior above that boundary is further distinguished by probability ranges. Low-confidence ML output falls through to rules instead of being presented as authoritative.

### 6. Keep model operations boring

The categorizer avoids exotic deployment machinery. Artifacts live in backend-controlled files, training is triggered explicitly through an authenticated endpoint, and inspection exposes training state without exposing model internals. That operational simplicity makes the model easier to retrain, redeploy, audit, and eventually replace.

## Stack

- LightGBM multiclass gradient-boosted trees
- scikit-learn TF-IDF and label encoding
- NumPy and pandas
- FastAPI endpoints for suggestion, correction logging, training, and model inspection
- File-backed model, vectorizer, encoder, and metadata artifacts

## Results

- `/api/categorize/suggest` returns a category, confidence level, available categories, and prediction source.
- `/api/categorize/corrections` captures user overrides for future training.
- `/api/categorize/train` requires at least 30 samples before training.
- `/api/categorize/model-info` exposes whether the model exists, whether it is trained, and how many samples it used.
- User corrections from all users improve the shared model intentionally.
- When confidence is low, the system transparently falls back to rules instead of pretending to know the answer. This study does not claim held-out production accuracy; its verifiable claims are the training gate, confidence gate, correction lifecycle, persisted artifacts, and fallback behavior.

Example suggest response:

```json
{
  "suggested_category": "Food & Dining",
  "confidence": "high",
  "all_categories": ["Food & Dining", "Transportation", "Shopping"],
  "source": "ml"
}
```

### 4. Make training and inspection operational

Training is not a notebook-only step. The API exposes the complete correction-to-model lifecycle:

- Corrections are stored with the original description, merchant, suggested category, and corrected category.
- Training reads every stored correction and returns sample count, status, accuracy, class count, and minimum-data requirements.
- Model inspection reports whether artifacts exist, whether the model is trained, and how many samples were used.
- Saved artifacts remain on backend-controlled storage rather than being accepted from client uploads.

Relevant code:

- `../../backend/app/routes/categorize.py`

Example training response:

```json
{
  "status": "trained",
  "samples": 150,
  "accuracy": 0.92,
  "num_classes": 14,
  "required": 30
}
```

The reported training accuracy should be read carefully: it measures fit on the supplied correction set, not held-out production performance. The more important production property is that low-confidence predictions do not reach users as authoritative ML answers.

### 5. Keep the evaluation honest

This system does not claim a universal accuracy number. Its measurable guarantees are narrower and more useful:

- A minimum training-data gate prevents training on noise.
- A confidence gate prevents low-confidence output from masquerading as knowledge.
- Correction logging preserves the exact inputs needed to retrain or audit the model.
- Model metadata preserves the sample count used for the current artifacts.

Future work could add held-out evaluation, per-category precision and recall, calibration curves, and drift monitoring for merchant vocabulary. Those would be natural extensions, not missing prerequisites for the current fallback architecture.

## Lessons

1. **Design the fallback first.** A production ML feature needs a credible answer for “what happens before training?”
2. **Calibrate confidence, not just accuracy.** A threshold turns model uncertainty into product behavior.
3. **Keep training artifacts together.** Model, vectorizer, labels, and metadata must be versioned and reloadable as a unit.
4. **Use corrections as training data.** Logging overrides creates a natural feedback loop for model improvement.
5. **Shared training data is a product decision.** Corrections from all users improve a shared model here; that tradeoff should be reviewed explicitly before handling more sensitive data.
6. **Report minimum-data behavior.** Training endpoints should distinguish “trained,” “insufficient data,” and “no data” instead of failing opaquely. That distinction also makes future monitoring straightforward: data volume, training outcomes, and fallback frequency can be tracked as operational signals.
