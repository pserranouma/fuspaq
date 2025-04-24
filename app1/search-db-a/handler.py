import json
import mysql.connector
import os

def handle(event, context):
    try:
        # Parse input JSON
        data = json.loads(event.body)
        client_id = data.get("client_id")

        if not client_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing client_id"})
            }

        # Database connection parameters (use environment variables or secrets)
        db_config = {
            "host": os.environ.get("DB_HOST", "192.168.1.43"),
            "user": os.environ.get("DB_USER", "root"),
            "password": os.environ.get("DB_PASS", "1234"),
            "database": os.environ.get("DB_NAME", "prueba"),
        }

        # Connect to MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Query known faces for given client
        query = """
            SELECT name, encoding
            FROM known_faces
            WHERE client_id = %s
        """
        cursor.execute(query, (client_id,))
        rows = cursor.fetchall()

        known_faces = []
        for row in rows:
            try:
                encoding = json.loads(row["encoding"])
                known_faces.append({
                    "name": row["name"],
                    "encoding": encoding
                })
            except json.JSONDecodeError:
                continue  # Skip malformed encoding

        cursor.close()
        conn.close()

        return {
            "statusCode": 200,
            "body": json.dumps({"known_faces": known_faces})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

