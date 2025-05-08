import json
import base64
import requests
import torch
import torchvision.transforms as transforms
import numpy as np
import cv2
from numpy.linalg import norm

# Descargar modelo MobileFaceNet
MODEL_URL = "https://github.com/deepinsight/insightface/releases/download/models/mobilenet_glint360k_backbone.pth"

device = torch.device('cpu')

# Definición simple de MobileFaceNet (puedes hacer una clase pequeña)
class MobileFaceNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.model = torch.hub.load('pytorch/vision:v0.10.0', 'mobilenet_v2', pretrained=True)
        self.model.classifier = torch.nn.Identity()

    def forward(self, x):
        return self.model(x)

model = MobileFaceNet().to(device)
model.eval()

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((112, 112)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (norm(a) * norm(b))

def get_embedding(image):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = model(img)
    emb = emb.cpu().numpy().flatten()
    return emb / norm(emb)

def handle(event, context):
    try:
        data = json.loads(event.body)
        image_b64 = data.get("image")
        image_url = data.get("image_url")
        known_faces = data.get("known_faces")

        if (not image_b64 and not image_url) or not known_faces:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'image' (base64) or 'image_url', or 'known_faces'"})
            }

        if image_b64:
            image_bytes = base64.b64decode(image_b64)
        else:
            response = requests.get(image_url)
            if response.status_code != 200:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Unable to download image from URL"})
                }
            image_bytes = response.content

        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        target_embedding = get_embedding(img)

        best_match = None
        best_score = -1
        threshold = 0.6

        for face in known_faces:
            name = face.get("name")
            encoding = face.get("encoding")
            if not name or not encoding:
                continue

            known_encoding = np.array(encoding)
            score = cosine_similarity(target_embedding, known_encoding)

            if score > best_score:
                best_score = score
                best_match = name

        if best_score >= threshold:
            return {
                "statusCode": 200,
                "body": json.dumps({"result": "match", "name": best_match, "similarity": best_score})
            }
        else:
            return {
                "statusCode": 200,
                "body": json.dumps({"result": "unknown", "similarity": best_score})
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

