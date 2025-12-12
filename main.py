import os
os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'
import uvicorn
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import resnet34
import io
import pandas as pd
from datetime import datetime
import random
from ultralytics import YOLO
import joblib
import threading
import os

# -------------------------------------------------------
# 1️⃣ Load Models & Configuration
# -------------------------------------------------------
weed_detector = YOLO("models/weed.pt")
num_classes = 4
resnet_model = resnet34(weights=None)
resnet_model.fc = nn.Linear(resnet_model.fc.in_features, num_classes)
resnet_model.load_state_dict(torch.load("models/leaf_resnet.pth", map_location="cpu", weights_only=True))
resnet_model.eval()

# Load Logistic Regression model and scaler for soil fertility
fertility_model = None
fertility_scaler = None
fertility_class_names = ["Low Fertility", "Medium Fertility", "High Fertility"]

try:
    fertility_model = joblib.load("models/best_model.pkl")
    fertility_scaler = joblib.load("models/scaler.pkl")
    print("✓ Soil fertility model and scaler loaded successfully")
except FileNotFoundError as e:
    print(f"⚠ Fertility model files not found: {e}")
except Exception as e:
    print(f"⚠ Error loading soil fertility model: {e}")

resnet_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
class_names = ["Blast", "Blight", "Brown_Spot", "Healthy"]
RESULT_CSV = "results/result.csv"
os.makedirs("results", exist_ok=True)

# -------------------------------------------------------
# 2️⃣ Utilities
# -------------------------------------------------------
def get_mock_gps():
    lat = round(random.uniform(12.8, 13.2), 6)
    lon = round(random.uniform(80.0, 80.3), 6)
    return lat, lon

def log_result(event, details=""):
    lat, lon = get_mock_gps()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "Timestamp": current_time,
        "Type": event,
        "Result": details,
        "Latitude": lat,
        "Longitude": lon
    }
    with threading.Lock():
        if os.path.exists(RESULT_CSV):
            df = pd.read_csv(RESULT_CSV)
            df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
        else:
            df = pd.DataFrame([entry])
        df.to_csv(RESULT_CSV, index=False)

# -------------------------------------------------------
# 3️⃣ FastAPI Application
# -------------------------------------------------------
app = FastAPI(title="Agricultural Monitoring API")

class SoilData(BaseModel):
    n: float
    p: float
    k: float
    ph: float
    ec: float

@app.post("/predict_fertility/")
def predict_fertility(data: SoilData):
    if not fertility_model or not fertility_scaler:
        return {
            "status": "error", 
            "fertility": "Model Not Available",
            "details": "Fertility model or scaler file is missing."
        }
    try:
        # Prepare input data: Raw Input → Scaler → Model → Prediction
        input_data = np.array([[data.n, data.p, data.k, data.ph, data.ec]])
        
        # Step 1: Scale the input data
        scaled_data = fertility_scaler.transform(input_data)
        
        # Step 2: Make prediction
        prediction = fertility_model.predict(scaled_data)[0]
        
        # Map prediction to class name (0=Low, 1=Medium, 2=High)
        predicted_class_name = fertility_class_names[prediction]
        
        log_result("Soil_Fertility", predicted_class_name)
        return {"status": "success", "fertility": predicted_class_name}
        
    except Exception as e:
        print(f"Error in /predict_fertility/: {e}")
        return {"status": "error", "fertility": "Error", "details": str(e)}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Agricultural Monitoring API"}

@app.post("/classify_leaf/")
async def classify_leaf_disease(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    
    # Check if it's a leaf using weed detector model (it can detect leaves)
    results = weed_detector.predict(image, verbose=False)
    if not any(len(r.boxes) > 0 for r in results):
        return {"filename": file.filename, "disease": "N/A", "leaf_detected": False}
    
    # If leaf detected, proceed with disease classification
    input_tensor = resnet_transform(image).unsqueeze(0)
    with torch.no_grad():
        preds = resnet_model(input_tensor)
        pred_class_idx = torch.argmax(preds, dim=1).item()
        disease_name = class_names[pred_class_idx]
    if disease_name != "Healthy":
        log_result("Leaf_Disease", disease_name)
    return {"filename": file.filename, "disease": disease_name, "leaf_detected": True}

@app.post("/detect_weed/")
async def detect_weed(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    results = weed_detector.predict(image, verbose=False)
    weed_detected = any(len(r.boxes) > 0 for r in results)
    if weed_detected:
        log_result("Weed", "WEED_DETECTED")
    return {"filename": file.filename, "weed_detected": weed_detected}

# -------------------------------------------------------
# 4️⃣ Run Application
# -------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)