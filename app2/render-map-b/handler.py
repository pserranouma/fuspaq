import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests

def handle(event, context):
    if not event.body:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing request body"})}

    try:
        data = json.loads(event.body)
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

    try:
        lat = data.get("latitude")
        lon = data.get("longitude")
        predicted_temp = data.get("predicted_temperature_in_3h")

        # Validate inputs
        if lat is None or lon is None or predicted_temp is None:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing 'latitude', 'longitude', or 'predicted_temperature_in_3h' parameter"})}

        # Get a static map image from OpenStreetMap via the Static Map API (with language set to English)
        static_map_url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&size=650,450&z=13&l=map&lang=en_US"
        
        # Download the map image from OpenStreetMap
        response = requests.get(static_map_url)
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve map image. Status code: {response.status_code}")
        
        # Open the image and add temperature label
        img = Image.open(BytesIO(response.content))
        img_with_text = img.copy()
        draw = ImageDraw.Draw(img_with_text)
        
        # Define the font and color
        font = ImageFont.load_default()
        text = f"Temp: {predicted_temp}°C"
        text_color = (255, 0, 0)  # red text
        outline_color = (255, 0, 0)  # red outline
        
        # Add text with outline for better visibility
        # Position the text
        x, y = 50, 50
        draw.text((x-1, y-1), text, font=font, fill=outline_color)  # Top-left outline
        draw.text((x+1, y-1), text, font=font, fill=outline_color)  # Top-right outline
        draw.text((x-1, y+1), text, font=font, fill=outline_color)  # Bottom-left outline
        draw.text((x+1, y+1), text, font=font, fill=outline_color)  # Bottom-right outline
        draw.text((x, y), text, font=font, fill=text_color)  # Center text

        # Convert image to JPEG
        buffer = BytesIO()
        img_with_text.convert("RGB").save(buffer, format="JPEG")
        encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Prepare the response data with the base64 encoded image
        response = {
            "statusCode": 200,
            "data": {
                "map_image_base64": encoded_image  # Base64 encoded JPEG image
            }
        }

    except Exception as e:
        # Handle unexpected errors
        return {"statusCode": 200, "body": json.dumps({"error": f"An error occurred: {str(e)}"})}

    # Return the response in the required format
    return json.dumps(response)

