import json
import base64
import cv2
import numpy as np
from deepface import DeepFace
import mysql.connector
import os

def handle(event, context):
    try:
        data = json.loads(event.body)
        image_b64 = data.get("image")
        name = data.get("name")
        client_id = data.get("client_id")

        if not image_b64 or not name or not client_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields"})
            }

        # Decode base64 image
        image_bytes = base64.b64decode(image_b64)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Get embedding with DeepFace
        embedding_obj = DeepFace.represent(img_path=img, model_name="Facenet", enforce_detection=False)
        if not embedding_obj:
            return {
                "statusCode": 200,
                "body": json.dumps({"result": "embedding_failed"})
            }

        embedding = embedding_obj[0]["embedding"]  # list of 128 floats

        # Insert into MySQL
        db_config = {
            "host": os.environ.get("DB_HOST", "192.168.1.43"),
            "user": os.environ.get("DB_USER", "root"),
            "password": os.environ.get("DB_PASS", "1234"),
            "database": os.environ.get("DB_NAME", "prueba")
        }

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO known_faces (id_cliente, name, encoding) VALUES (%s, %s, %s)"
        cursor.execute(query, (client_id, name, json.dumps(embedding)))
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "statusCode": 200,
            "body": json.dumps({"result": "face_registered", "name": name})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

