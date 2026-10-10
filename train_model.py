"""Create a DEMO study-need classifier for VERVAIN.

Important: this model is trained on illustrative synthetic examples, not real student outcomes.
It is a wiring/prototype check only and must not be presented as a validated predictor.
Run: python train_model.py
"""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# Each row is [quiz score percentage, BKT mastery probability].
# Synthetic labels follow a transparent rule to create a working prototype:
# flag extra practice when score < 60% OR mastery < 0.50.
rows = []
labels = []
for score in range(0, 101, 5):
    for mastery_pct in range(0, 101, 5):
        mastery = mastery_pct / 100
        rows.append([score, mastery])
        labels.append(int(score < 60 or mastery < 0.50))

X = pd.DataFrame(rows, columns=["quiz_score", "mastery"])
y = labels
model = make_pipeline(StandardScaler(), LogisticRegression(random_state=42, max_iter=1000))
model.fit(X, y)

out = Path(__file__).with_name("study_recommender.pkl")
joblib.dump(model, out)
print(f"Created {out}")
print("DEMO ONLY: trained on synthetic rule-generated labels; not validated on real student outcomes.")
