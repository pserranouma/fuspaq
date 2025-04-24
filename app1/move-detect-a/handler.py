import json
import base64
import numpy as np
import cv2

def detect_motion(img1, img2, threshold=25):
    # Convert images to grayscale
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Compute absolute difference and threshold
    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

    # Compute percentage of changed pixels
    motion_percent = (np.sum(thresh > 0) / thresh.size) * 100
    return motion_percent, motion_percent > 2  # e.g. movement over 2% is considered significant

def handle(event, context):
    if not event.body:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing request body"})}

    try:
        data = json.loads(event.body)
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}
        
    img1_b64 = data.get("image1")
    img2_b64 = data.get("image2")

    if not img1_b64 or not img2_b64:
        return {"statusCode": 400,
            "body": json.dumps({"error": "Both 'image1' and 'image2' (base64-encoded) are required."})
        }

    try:
        # Decode images from base64 to OpenCV format
        img1_bytes = base64.b64decode(img1_b64)
        img2_bytes = base64.b64decode(img2_b64)

        img1 = cv2.imdecode(np.frombuffer(img1_bytes, np.uint8), cv2.IMREAD_COLOR)
        img2 = cv2.imdecode(np.frombuffer(img2_bytes, np.uint8), cv2.IMREAD_COLOR)

        if img1 is None or img2 is None:
            raise ValueError("One or both images could not be decoded.")

        motion_percent, motion_detected = detect_motion(img1, img2)

        response = {
            "statusCode": 200,
            "body": json.dumps({
                "motion_detected": motion_detected,
                "motion_percent": round(motion_percent, 2)
                })
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"An error occurred: {str(e)}"})}

    # Make sure that a valid JSON is returned
    return response

