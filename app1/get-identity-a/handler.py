import json
import base64
import numpy as np
import cv2
from deepface import DeepFace
from numpy.linalg import norm

# Compute cosine similarity between two vectors
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (norm(a) * norm(b))

def handle(event, context):
    try:
        data = json.loads(event.body)
        image_b64 = data.get("image")
        known_faces = data.get("known_faces")

        if not image_b64 or not known_faces:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing image or known_faces"})
            }

        # Decode image
        image_bytes = base64.b64decode(image_b64)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Get embedding of input face
        target_embedding_obj = DeepFace.represent(img_path=img, model_name="Facenet", enforce_detection=False)
        if not target_embedding_obj:
            return {
                "statusCode": 200,
                "body": json.dumps({"result": "embedding_failed"})
            }

        target_embedding = target_embedding_obj[0]["embedding"]

        # Compare with known faces
        best_match = None
        best_score = -1
        threshold = 0.6  # Adjust as needed

        for face in known_faces:
            name = face.get("name")
            encoding = face.get("encoding")
            if not name or not encoding:
                continue

            score = cosine_similarity(target_embedding, encoding)
            if score > best_score:
                best_score = score
                best_match = name

        if best_score >= threshold:
            return {
                "statusCode": 200,
                "body": json.dumps({"result": "match", "name": best_match, "similarity": best_score})
            }
        else:
            return {
                "statusCode": 200,
                "body": json.dumps({"result": "unknown", "similarity": best_score})
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

