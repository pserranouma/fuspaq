import json
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

def handle(event, context):
    if not event.body:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing request body"})}

    try:
        data = json.loads(event.body)
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

    if "hourly" not in data:
        return {"statusCode": 404, "body": json.dumps({"error": "Invalid data format. 'hourly' key not found."})}

    try:
        hourly = data["hourly"]
        df = pd.DataFrame(hourly)
        df["time"] = pd.to_datetime(df["time"])

        # Objective variable: temperature after 3 hours
        df["target"] = df["temperature_2m"].shift(-3)
        df = df.dropna()

        X = df[["temperature_2m", "precipitation", "windspeed_10m"]]
        y = df["target"]

        # Random Forest
        model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        model.fit(X, y)

        # Predict using last row
        last_features = X.iloc[-1].values.reshape(1, -1)
        prediction = model.predict(last_features)[0]

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

