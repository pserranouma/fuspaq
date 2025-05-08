import base64
import json
import cv2
import numpy as np
import requests

def handle(event, context):
    try:
        # Parse the input JSON
        data = json.loads(event.body)

        image_b64 = data.get("image")
        image_url = data.get("image_url")

        if not image_b64 and not image_url:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'image' (base64) or 'image_url'"})
            }

        if image_b64:
            # Decode base64 image to OpenCV format
            image_bytes = base64.b64decode(image_b64)
        else:
            # Download image from URL
            response = requests.get(image_url)
            if response.status_code != 200:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Unable to download image from URL"})
                }
            image_bytes = response.content

        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Could not decode image"})
            }

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

