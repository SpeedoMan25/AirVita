import base64
import os
import torch
import cv2
import numpy as np
import requests
from collections import deque, Counter
from torchvision import models, transforms
from PIL import Image
from pathlib import Path

# MIT CSAIL Places365 Model
PLACES_MODEL_URL = "http://places2.csail.mit.edu/models_places365/resnet18_places365.pth.tar"
CATEGORIES_URL = "https://raw.githubusercontent.com/csailvision/places365/master/categories_places365.txt"

class RoomClassifier:
    def __init__(self):
        self.model = None
        self.classes = []
        self.history = deque(maxlen=25)
        self.stable_room = "Scanning..."
        self.preprocess = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        # User focus mapping
        self.room_mapping = {
            'classroom': 'Classroom',
            'lecture_hall': 'Classroom',
            'library/indoor': 'Library',
            'computer_room': 'Office',
            'bedroom': 'Bedroom',
            'dorm_room': 'Dorm Room',
            'hotel_room': 'Dorm Room',
            'living_room': 'Living Room',
            'lobby': 'Lobby',
            'coffee_shop': 'Cafe',
            'cafeteria': 'Cafe',
            'dining_room': 'Dining Room',
            'restaurant': 'Restaurant',
            'gymnasium/indoor': 'Gym',
            'kitchen': 'Kitchen',
            'office': 'Office',
            'corridor': 'Hallway'
        }

    def load_model(self):
        # Local paths - ensure we are in /app/data/models in Docker or backend/data/models locally
        base_path = Path(__file__).parent.parent
        cache_dir = base_path / "data" / "models"
        
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️ Could not create directory {cache_dir}: {e}")
            # Fallback to current directory if permission denied at root
            cache_dir = Path(".") / "models"
            cache_dir.mkdir(exist_ok=True)
        
        model_path = cache_dir / "resnet18_places365.pth.tar"
        cats_path = cache_dir / "categories_places365.txt"

        # Download if missing
        if not model_path.exists():
            print(f"📥 Downloading Places365 weights to {model_path} (45MB)...")
            try:
                r = requests.get(PLACES_MODEL_URL, stream=True, timeout=30)
                with open(model_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk: f.write(chunk)
                print("✅ Download complete.")
            except Exception as e:
                print(f"❌ Failed to download weights: {e}")
                return

        if not cats_path.exists():
            try:
                r = requests.get(CATEGORIES_URL, timeout=10)
                with open(cats_path, 'wb') as f:
                    f.write(r.content)
            except Exception as e:
                print(f"❌ Failed to download categories: {e}")
                return

        # Initialize model
        self.model = models.resnet18(num_classes=365)
        checkpoint = torch.load(model_path, map_location=lambda storage, loc: storage)
        state_dict = {str.replace(k, 'module.', ''): v for k, v in checkpoint['state_dict'].items()}
        self.model.load_state_dict(state_dict)
        self.model.eval()

        with open(cats_path) as f:
            self.classes = [line.strip().split(' ')[0][3:] for line in f]
        
        print("✅ Room Classifier model loaded.")

    def predict(self, base64_image: str):
        if self.model is None:
            return {"error": "Model not loaded"}

        try:
            if ',' in base64_image:
                base64_image = base64_image.split(',')[1]
            img_data = base64.b64decode(base64_image)
            
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None: return {"error": "Invalid image"}
            
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            input_tensor = self.preprocess(pil_img).unsqueeze(0)
            with torch.no_grad():
                output = self.model(input_tensor)
            
            probs = torch.nn.functional.softmax(output[0], dim=0)
            conf, idx = torch.max(probs, 0)
            
            scene_name = self.classes[idx.item()]
            display_name = self.room_mapping.get(scene_name, scene_name.replace('_', ' ').title())
            
            self.history.append(display_name)
            counts = Counter(self.history)
            most_common, vote_count = counts.most_common(1)[0]
            
            # Hysteresis: Require 60% majority to switch stable labels
            if (vote_count / len(self.history)) > 0.6:
                self.stable_room = most_common
                
            return {
                "room": self.stable_room,
                "confidence": round(float(conf), 2),
                "scene": scene_name
            }
        except Exception as e:
            return {"error": str(e)}

# Singleton instance
classifier = RoomClassifier()
