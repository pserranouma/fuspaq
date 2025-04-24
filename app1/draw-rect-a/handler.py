import base64
import json
import cv2
import numpy as np

def handle(event, context):
    try:
        # Parse input JSON
        data = json.loads(event.body)
        image_b64 = data.get("image")
        rectangles = data.get("faces", [])

        if not image_b64 or not rectangles:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing image_base64 or rectangles in request"})
            }

        # Decode base64 image to OpenCV format
        image_bytes = base64.b64decode(image_b64)
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
            "body": json.dumps({"image_base64": result_b64})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

