import json
import random
import requests
from PIL import Image
from io import BytesIO
import base64

def handle(event, context):
    if not event.body:
        return {"statusCode": 200, "body": json.dumps({"error": "Missing request body"})}

    try:
        body = json.loads(event.body)
    except json.JSONDecodeError:
        return {"statusCode": 200, "body": json.dumps({"error": "Invalid JSON"})}
        
    try:
        images_data = body.get("images", [])
    except:
        images_data = []
    
    try:
        num_images = body.get("n", 2)
    except:
        num_images = 2
        
    try:
        target_width = body.get("width", 480)
    except:
        target_width = 480

    if num_images > len(images_data):
        num_images = len(images_data)

    selected = random.sample(images_data, num_images)

    resized_images = []

    for img_info in selected:
        url = img_info.get("url")
        if not url:
            continue

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
        except Exception as e:
            return {"statusCode": 200, "body": json.dumps({"error": f"Error downloading image from {url}: {str(e)}"})}

        # Redimensionar manteniendo proporción
        w_percent = (target_width / float(img.size[0]))
        target_height = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        resized_images.append(img)

    if not resized_images:
        return {"statusCode": 200, "body": json.dumps({"error": "No images could be processed"})}

    # Combinar imágenes horizontalmente
    total_width = sum(img.width for img in resized_images)
    max_height = max(img.height for img in resized_images)

    final_image = Image.new('RGB', (total_width, max_height), color=(255, 255, 255))

    current_x = 0
    for img in resized_images:
        final_image.paste(img, (current_x, 0))
        current_x += img.width

    # Convertir a base64
    buffer = BytesIO()
    final_image.save(buffer, format="JPEG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return {
        "status": 200,
        "body": json.dumps(encoded_image)
    }

