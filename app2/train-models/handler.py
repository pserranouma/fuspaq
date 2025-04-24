import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
import pickle
import os
import io
import mysql.connector

def save_model_to_db(model, model_name):
    """Save the trained model to the MySQL database."""
    try:
        # Serialize the model using pickle and store it in a BytesIO object
        model_blob = io.BytesIO()
        pickle.dump(model, model_blob)
        model_blob.seek(0)  # Rewind to the beginning of the file-like object

        # Read the BytesIO object as bytes
        model_data = model_blob.read()

        # Connect to MySQL database
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "192.168.1.43"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "1234"),
            database=os.getenv("DB_DATABASE", "models")
        )
        cursor = conn.cursor()

        # Check if model already exists, if so, update it, else insert it
        cursor.execute("SELECT model_name FROM models WHERE model_name = %s", (model_name,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE models SET model_data = %s WHERE model_name = %s
            """, (model_data, model_name))
        else:
            cursor.execute("""
                INSERT INTO models (model_name, model_data) VALUES (%s, %s)
            """, (model_name, model_data))

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Model '{model_name}' saved successfully to the database.")
    
    except mysql.connector.Error as err:
        raise Exception(f"Error saving model to database: {err}")

def handle(event, context):
    """Train and save multiple models to the database."""
    if not event.body:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing request body"})}

    try:
        request_data = json.loads(event.body)
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

    lat = request_data.get("latitude")
    lon = request_data.get("longitude")

    if lat is None or lon is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing 'latitude' or 'longitude' in request."})}

    try:
        # Get meteorological data
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=70)

        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "hourly": "temperature_2m,precipitation,windspeed_10m",
            "timezone": "Europe/Madrid"
        }

        response = requests.get(url, params=params)
        weather_data = response.json()

        if "hourly" not in weather_data:
            return {"statusCode": 404, "body": json.dumps({"error": "No 'hourly' data returned from API."})}

        # Prepare data
        hourly = weather_data["hourly"]
        df = pd.DataFrame(hourly)
        df["time"] = pd.to_datetime(df["time"])
        df["target"] = df["temperature_2m"].shift(-3)
        df = df.dropna()

        X = df[["temperature_2m", "precipitation", "windspeed_10m"]]
        y = df["target"]

        # Train models
        rf_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        rf_model.fit(X, y)
        
        lr_model = LinearRegression()
        lr_model.fit(X, y)
        
        nn_model = MLPRegressor(hidden_layer_sizes=(50,), max_iter=1000, random_state=42)
        nn_model.fit(X, y)

        # Save models to database
        save_model_to_db(rf_model, "model_rf")
        save_model_to_db(lr_model, "model_lr")
        save_model_to_db(nn_model, "model_nn")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Models trained and saved successfully.",
                "models_saved": ["model_rf", "model_lr", "model_nn"]
            })
        }

    except Exception as e:
        return {"statusCode": 200, "body": json.dumps({"error": f"An error occurred: {str(e)}"})}

