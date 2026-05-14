import joblib
import pandas as pd

model = joblib.load("performance_model.pkl")

def predict_performance(data):
    df = pd.DataFrame([data])
    return float(model.predict(df)[0])