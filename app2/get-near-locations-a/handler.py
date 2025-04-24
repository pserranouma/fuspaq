import mysql.connector
import json
import os
import math

# Function to get distances using Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distance in kilometers

def handle(event, context):
    connection = None
    response = {}

    if not event.body:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing request body"})}

    try:
        event_data = json.loads(event.body)
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

    # Extract input parameters
    latitude = event_data.get("latitude")
    longitude = event_data.get("longitude")
    address = event_data.get("address")
    distance = event_data.get("distance")

    if latitude is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing latitude parameter"})}
    if longitude is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing longitude parameter"})}
    if not address:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing address parameter"})}
    if distance is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing distance parameter"})}

    # Get DB connection details from environment
    db_host = os.getenv('DB_HOST', '192.168.1.43')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '1234')
    db_name = os.getenv('DB_NAME', 'prueba')

    try:
        # Connect to MySQL
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = connection.cursor(dictionary=True)

        # Extract location components
        country = address.get("country")
        state = address.get("state")
        province = address.get("province")
        town = address.get("town")
        municipality = address.get("municipality")
        location_coords = (float(latitude), float(longitude))

        # Construct query to get locations within the same administrative area
        base_query = "SELECT * FROM locations WHERE country=%s AND state=%s AND province=%s"
        query_values = [country, state, province]

        if municipality and municipality.strip():
            base_query += " AND municipality=%s"
            query_values.append(municipality)
            
        if town and town.strip():
            base_query += " AND town=%s"
            query_values.append(town)

        cursor.execute(base_query, tuple(query_values))
        locations = cursor.fetchall()

        if not locations:
            return {"statusCode": 404, "body": json.dumps({"error": "No locations found"})}

        # Filter nearby locations
        nearby_locations = []
        for loc in locations:
            loc_coords = (float(loc["latitude"]), float(loc["longitude"]))
            dist = haversine(location_coords[0], location_coords[1], loc_coords[0], loc_coords[1])
            if dist < distance:
                nearby_locations.append(loc)

        if nearby_locations:
            response = {
                "statusCode": 200,
                "body": json.dumps({"locations": nearby_locations})
            }
        else:
            response = {
                "statusCode": 404,
                "body": json.dumps({"error": f"No images within {distance} km of the location"})
            }

    except mysql.connector.Error as err:
        response = {
            "statusCode": 500,
            "body": json.dumps({"error": str(err)})
        }

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

    return response

