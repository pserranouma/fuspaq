import json
import requests
import mysql.connector
import os
import joblib
import io
from datetime import datetime
import pandas as pd

def load_model_from_db(model_name):
    """Load the trained model from the MySQL database."""
    try:
        # Connect to MySQL database
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "192.168.1.43"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "1234"),
            database=os.getenv("DB_DATABASE", "models")
        )
        cursor = conn.cursor()

        # Retrieve the model from the database
        cursor.execute("SELECT model_data FROM models WHERE model_name = %s", (model_name,))
        result = cursor.fetchone()

        if result:
            model_blob = result[0]
            
            # Load the model from the BLOB
            model = joblib.load(io.BytesIO(model_blob))  # Load from BLOB using BytesIO

            cursor.close()
            conn.close()

            return model
        else:
            cursor.close()
            conn.close()
            raise Exception(f"Model with name {model_name} not found in the database.")
    
    except mysql.connector.Error as err:
        raise Exception(f"Error loading model from database: {err}")

def handle(event, context):
    """Handle the prediction request."""
    if not event.body:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing request body"})}

    try:
        request_data = json.loads(event.body)
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

    if "hourly" not in request_data:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid data format. 'hourly' key not found."})}

    lat = request_data.get("latitude")
    lon = request_data.get("longitude")
    hourly = request_data["hourly"]
    model_name = "model_rf"

    if lat is None or lon is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing 'latitude' or 'longitude' in request."})}

    try:
        # Prepare data for prediction
        hourly = request_data["hourly"]
        df = pd.DataFrame(hourly)
        df["time"] = pd.to_datetime(df["time"])

        X_new = df[["temperature_2m", "precipitation", "windspeed_10m"]]
        
        # Drop rows with any NaN values
        X_new = X_new.dropna().tail(1)

        # Load the model from the database
        model = load_model_from_db(model_name)

        # Make prediction
        prediction = model.predict(X_new)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "prediction_time": str(df.iloc[-1]["time"]),
                "predicted_temperature_in_3h": float(round(prediction[0], 2))
            })
        }

    except Exception as e:
        return {"statusCode": 200, "body": json.dumps({"error": f"An error occurred: {str(e)}"})}

