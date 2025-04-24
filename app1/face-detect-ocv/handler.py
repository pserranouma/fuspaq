import base64
import json
import cv2
import numpy as np
import os

def handle(event, context):
    try:
        # Parse the input JSON
        data = json.loads(event.body)
        image_b64 = data.get("image")

        if not image_b64:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing image_base64 in request"})
            }

        # Decode base64 image to OpenCV format
        image_bytes = base64.b64decode(image_b64)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Detect faces in the image
        rectangles = detect_faces(img)

        return {
            "statusCode": 200,
            "body": json.dumps({"faces": rectangles})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def detect_faces(img):
    # Convert image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Load Haar cascade classifier for face detection
    haar_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(haar_path)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    rectangles = []
    for (x, y, w, h) in faces:
        rectangles.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})

    return rectangles

