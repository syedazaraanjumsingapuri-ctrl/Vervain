


from pathlib import Path
import joblib
import pandas as pd

# Load the saved model
model_path = Path(__file__).parent / "study_recommender.pkl"
model = joblib.load(model_path)

# Test with a student's learning performance
quiz_score = 35
mastery = 35

# Prepare the input in the same format used during training
student_data = pd.DataFrame(
    [[quiz_score, mastery]],
    columns=["quiz_score", "mastery"]
)

# Predict whether a resource should be recommended
prediction = model.predict(student_data)[0]

print("Quiz Score:", quiz_score)
print("Mastery:", mastery)

if prediction == 1:
    print("Result: Recommend additional learning resources.")
else:
    print("Result: Additional resources may not be necessary.")
