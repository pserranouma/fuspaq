import base64
import json
import cv2
import numpy as np
import requests

def handle(event, context):
    try:
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
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                image_bytes = response.content
            except requests.exceptions.RequestException as e:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": f"Unable to download image: {str(e)}"})
                }

        result_b64 = base64.b64encode(image_bytes).decode()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "image": result_b64
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Server error: {str(e)}"})
        }

