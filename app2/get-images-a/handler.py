import mysql.connector
import json
import os
import math

def handle(event, context):
    connection = None
    response = {}
    
    if not event.body:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing request body"})}

    try:
        event_data = json.loads(event.body)
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

    locations = event_data.get("locations")
    if not locations or not isinstance(locations, list):
        return {"statusCode": 400, "body": json.dumps({"error": "Missing or invalid 'data' parameter"})}

    # Extract IDs from locations
    location_ids = [location['id'] for location in locations if 'id' in location]

    if not location_ids:
        return {"statusCode": 404, "body": json.dumps({"error": "No valid location ids found"})}
    
    # Get connection data from environment variables
    db_host = os.getenv('DB_HOST', '192.168.1.43')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '1234')
    db_name = os.getenv('DB_NAME', 'prueba')

    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )

        cursor = connection.cursor(dictionary=True)
        
        # Get all images for each id_location
        format_strings = ','.join(['%s'] * len(location_ids))  # Crear el formato para la consulta
        query = f"SELECT id, name, url FROM images WHERE id_location IN ({format_strings})"
        cursor.execute(query, tuple(location_ids))

        images = cursor.fetchall()

        if not images:
            return {"statusCode": 404, "body": json.dumps({"error": "No images found for the given locations"})}

        # Return found images
        response = {
            "statusCode": 200,
            "body": json.dumps({"images": images})
        }

    except mysql.connector.Error as err:
        # Returns connection errors
        response = {
            "statusCode": 500,
            "body": json.dumps({"error": str(err)})
        }

    finally:
        # Close connection if established
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

    # Make sure that a valid JSON is returned
    return response

