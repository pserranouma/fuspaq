import base64
import json
import cv2
import numpy as np
import requests

def handle(event, context):
    try:
        # Parse input JSON
        data = json.loads(event.body)
        image_b64 = data.get("image")
        image_url = data.get("image_url")
        rectangles = data.get("faces", [])

        if (not image_b64 and not image_url) or not rectangles:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'image' (base64) or 'image_url', or rectangles"})
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

        # Draw rectangles
        for rect in rectangles:
            x, y, w, h = rect.get("x"), rect.get("y"), rect.get("w"), rect.get("h")
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Encode modified image to base64
        _, buffer = cv2.imencode('.png', img)
        result_b64 = base64.b64encode(buffer).decode()

        return {
            "statusCode": 200,
            "body": json.dumps({"image": result_b64})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

