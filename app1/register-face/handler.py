import json
import base64
import requests
import torch
import torchvision.transforms as transforms
import numpy as np
import cv2
import mysql.connector
import os

# Descargar modelo MobileFaceNet
MODEL_URL = "https://github.com/deepinsight/insightface/releases/download/models/mobilenet_glint360k_backbone.pth"

device = torch.device('cpu')

# Definición de MobileFaceNet
class MobileFaceNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.model = torch.hub.load('pytorch/vision:v0.10.0', 'mobilenet_v2', pretrained=True)
        self.model.classifier = torch.nn.Identity()

    def forward(self, x):
        return self.model(x)

# Cargar el modelo
model = MobileFaceNet().to(device)
model.eval()

# Definir las transformaciones
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((112, 112)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Función para obtener la codificación facial
def get_embedding(image):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = model(img)
    emb = emb.cpu().numpy().flatten()
    return emb / np.linalg.norm(emb)

def handle(event, context):
    try:
        data = json.loads(event.body)
        image_b64 = data.get("image")
        image_url = data.get("image_url")
        name = data.get("name")
        client_id = data.get("client_id")

        if (not image_b64 and not image_url) or not name or not client_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'image' (base64) or 'image_url', or 'name' or 'client_id'"})
            }

        if image_b64:
            # Decode base64 image to OpenCV format
            image_bytes = base64.b64decode(image_b64)
        else:
            # Download image from URL
            response = requests.get(image_url)
            if response.status_code != 200:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Unable to download image from URL"})
                }
            image_bytes = response.content

        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Obtener la codificación facial utilizando MobileFaceNet
        encoding = get_embedding(img)

        # Insertar en MySQL
        db_config = {
            "host": os.environ.get("DB_HOST", "192.168.1.43"),
            "user": os.environ.get("DB_USER", "root"),
            "password": os.environ.get("DB_PASS", "1234"),
            "database": os.environ.get("DB_NAME", "prueba")
        }

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO known_faces (client_id, name, encoding) VALUES (%s, %s, %s)"
        cursor.execute(query, (client_id, name, json.dumps(encoding.tolist())))
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "statusCode": 200,
            "body": json.dumps({"result": "face_registered", "name": name})
        }

    except Exception as e:
        return {
            "statusCode": 200,
            "body": json.dumps({"error": str(e)})
        }

