import folium
import json
import base64
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import mplleaflet

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

        # Create a folium map centered at the given coordinates
        m = folium.Map(location=[lat, lon], zoom_start=13)
        
        # Add a marker for the location
        folium.Marker([lat, lon], tooltip="Location").add_to(m)

        # Add the predicted temperature as a label centered on the map
        folium.Marker([lat, lon], 
                      popup=f"Predicted Temperature in 3h: {predicted_temp}°C", 
                      icon=folium.Icon(color='blue')).add_to(m)

        # Convert folium map to a matplotlib figure
        fig = plt.figure(figsize=(10, 10))  # Optional: Set figure size
        m.save("/tmp/map.html")

        # Use mplleaflet to convert the map to a static image
        mplleaflet.show(fig)
        plt.savefig('/tmp/map.png')

        # Open the saved image and convert it to JPEG
        img = Image.open('/tmp/map.png')
        buffer = BytesIO()
        img.convert("RGB").save(buffer, format="JPEG")
        encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Prepare response data with the base64 encoded image
        response = {
            "statusCode": 200,
            "data": {
                "map_image_base64": encoded_image  # Base64 encoded JPEG image
            }
        }

    except Exception as e:
        # Handle unexpected errors
        return {"statusCode": 500, "body": json.dumps({"error": f"An error occurred: {str(e)}"})}

    # Return the response in the required format
    return json.dumps(response)

