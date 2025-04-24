import json
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

def handle(event, context):
    if not event.body:
        return {"statusCode": 404, "body": json.dumps({"error": "Missing request body"})}

    try:
        data = json.loads(event.body)
    except json.JSONDecodeError:
        return {"statusCode": 404, "body": json.dumps({"error": "Invalid JSON"})}

    try:
        if "hourly" not in data:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid data format. 'hourly' key not found."})}

        hourly = data["hourly"]
        df = pd.DataFrame(hourly)
        df["time"] = pd.to_datetime(df["time"])

        # Objective: temperature after 3h
        df["target"] = df["temperature_2m"].shift(-3)
        df = df.dropna()

        # Training
        feature_cols = ["temperature_2m", "precipitation", "windspeed_10m"]
        X = df[feature_cols]
        y = df["target"]

        # Scale data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        # Neuronal network
        model = MLPRegressor(hidden_layer_sizes=(64, 32), activation='relu', max_iter=500, random_state=42)
        
        model.fit(X_scaled, y)

        # Predict using last scaled row
        last_row = df.iloc[[-1]][feature_cols]
        last_row_scaled = scaler.transform(last_row)
        prediction = model.predict(last_row_scaled)[0]

        response = {
            "statusCode": 200,
            "body": json.dumps({
                "prediction_time": str(df.iloc[-1]["time"]),
                "predicted_temperature_in_3h": round(prediction, 2)
            })
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"An error occurred: {str(e)}"})}

    return response

