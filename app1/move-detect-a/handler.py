import json
import base64
import numpy as np
import cv2
import requests

def detect_motion(img1, img2, threshold=25):
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    motion_percent = (np.sum(thresh > 0) / thresh.size) * 100
    return motion_percent, motion_percent > 2

def handle(event, context):
    try:
        data = json.loads(event.body)

        image1_bytes = None
        if "image1" in data:
            image1_bytes = base64.b64decode(data["image1"])
        elif "image1_url" in data:
            r = requests.get(data["image1_url"])
            if r.status_code == 200:
                image1_bytes = r.content

        image2_bytes = None
        if "image2" in data:
            image2_bytes = base64.b64decode(data["image2"])
        elif "image2_url" in data:
            r = requests.get(data["image2_url"])
            if r.status_code == 200:
                image2_bytes = r.content

        if image1_bytes is None or image2_bytes is None:
            return {
                "statusCode": 200,
                "body": json.dumps({"error": "Missing images or invalid URLs"})
            }

        img1 = cv2.imdecode(np.frombuffer(image1_bytes, np.uint8), cv2.IMREAD_COLOR)
        img2 = cv2.imdecode(np.frombuffer(image2_bytes, np.uint8), cv2.IMREAD_COLOR)

        if img1 is None or img2 is None:
            raise ValueError("One or both images could not be decoded.")

        motion_percent, motion_detected = detect_motion(img1, img2)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "motion_detected": bool(motion_detected),
                "motion_percent": float(round(motion_percent, 2))
            })
        }

    except Exception as e:
        return {
            "statusCode": 200,
            "body": json.dumps({"error": f"An error occurred: {str(e)}"})
        }

