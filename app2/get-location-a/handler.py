import json
import requests

def handle(event, context):
    try:
        body = event.body

        if not body:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing request body"})
            }

        data = json.loads(body)
        address_input = data.get("address")

        if not address_input or not isinstance(address_input, dict):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing or invalid 'address' object"})
            }

        # Build a query string like "city, state, country"
        query_parts = [address_input.get(key) for key in [
            "road", "postcode", "city", "town", "village", "county", "state", "country", "municipality", "province", "neighbourhood"
        ] if address_input.get(key)]
        if not query_parts:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No valid address fields provided"})
            }

        query_string = ", ".join(query_parts)

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query_string,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "openfaas-geolocator"
        }

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        results = response.json()
        if not results:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Address not found"})
            }

        location = results[0]
        full_address = location.get("address", {})

        return {
            "statusCode": 200,
            "body": json.dumps({
                "query": query_string,
                "latitude": location["lat"],
                "longitude": location["lon"],
                "display_name": location.get("display_name"),
                "address": full_address
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

