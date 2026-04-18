import base64
import os
import torch
import cv2
import numpy as np
import requests
from collections import deque, Counter
from flask import Flask, request, jsonify, render_template
from torchvision import models, transforms
from PIL import Image

# Fix for PyTorch 2.6+ weights_only=True security restriction
try:
    if hasattr(torch.serialization, 'add_safe_globals'):
        # We don't strictly need this for standard resnet weights but good practice
        pass
except ImportError:
    pass

app = Flask(__name__)

# --- Places365 Model Setup ---
CATEGORIES_URL = "https://raw.githubusercontent.com/csailvision/places365/master/categories_places365.txt"
WEIGHTS_URL = "https://download.pytorch.org/models/resnet18-f37072fd.pth" # Placeholder for architecture, we need specialized places weights
# For reliable Places365, we use the MIT CSAIL pre-trained model
PLACES_MODEL_URL = "http://places2.csail.mit.edu/models_places365/resnet18_places365.pth.tar"

model_file = 'resnet18_places365.pth.tar'
if not os.path.exists(model_file):
    print("Downloading Places365 weights (approx 45MB)...")
    r = requests.get(PLACES_MODEL_URL, stream=True)
    with open(model_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: f.write(chunk)

# Load the model architecture
model = models.resnet18(num_classes=365)
checkpoint = torch.load(model_file, map_location=lambda storage, loc: storage)
state_dict = {str.replace(k, 'module.', ''): v for k, v in checkpoint['state_dict'].items()}
model.load_state_dict(state_dict)
model.eval()

# Download categories
categories_file = 'categories_places365.txt'
if not os.path.exists(categories_file):
    r = requests.get(CATEGORIES_URL)
    with open(categories_file, 'wb') as f:
        f.write(r.content)

with open(categories_file) as f:
    classes = [line.strip().split(' ')[0][3:] for line in f]

# Image transformation for ResNet
preprocess = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# Define room mapping for the user's focus categories
MAPPING = {
    # Classrooms
    'classroom': 'Classroom',
    'lecture_hall': 'Classroom',
    'library/indoor': 'Library',
    'computer_room': 'Office/Classroom',
    
    # Dorms/Bedrooms
    'bedroom': 'Bedroom',
    'dorm_room': 'Dorm Room',
    'hotel_room': 'Dorm Room',
    
    # Living Spaces
    'living_room': 'Living Room',
    'lobby': 'Lobby',
    'waiting_room': 'Lobby',
    
    # Cafes/Dining
    'coffee_shop': 'Cafe',
    'cafeteria': 'Cafe',
    'dining_room': 'Dining Room',
    'restaurant': 'Restaurant',
    'bar': 'Cafe',
    'pizzeria': 'Cafe',
    
    # Others
    'gymnasium/indoor': 'Gym',
    'kitchen': 'Kitchen',
    'office': 'Office',
    'corridor': 'Hallway',
    'staircase': 'Staircase'
}

recent_detections = deque(maxlen=25)
current_stable_room = "Scanning..."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global current_stable_room
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        img_str = data['image']
        if ',' in img_str: img_str = img_str.split(',')[1]
        img_data = base64.b64decode(img_str)
        
        # Convert to PIL Image for torchvision
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None: return jsonify({'error': 'Decode failed'}), 400
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        # Predict
        input_tensor = preprocess(pil_img).unsqueeze(0)
        with torch.no_grad():
            output = model(input_tensor)
        
        probs = torch.nn.functional.softmax(output[0], dim=0)
        conf, idx = torch.max(probs, 0)
        
        scene_name = classes[idx.item()]
        
        # Map to user category
        display_name = MAPPING.get(scene_name, scene_name.replace('_', ' ').title())
        
        recent_detections.append(display_name)
        
        # --- Stability Logic (Hysteresis) ---
        counts = Counter(recent_detections)
        most_common, vote_count = counts.most_common(1)[0]
        
        # Required confidence: At least 60% of current window must agree to switch labels
        # This prevents flickering when moving camera or through blurry frames
        if vote_count / len(recent_detections) > 0.6:
            current_stable_room = most_common
        
        # Even if we don't switch the label, we return the high-confidence individual result
        # but the UI will show the 'stable' one.
        
        return jsonify({
            'room': current_stable_room,
            'confidence': round(float(conf), 2),
            'raw': scene_name
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False, ssl_context='adhoc')
