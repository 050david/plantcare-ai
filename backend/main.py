from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
import numpy as np
from PIL import Image
import json
import io

app = FastAPI(title="PlantCare AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NUM_CLASSES = 15

def build_model():
    base_model = MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights=None
    )
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(512, activation='relu')(x)
    x = Dropout(0.4)(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.3)(x)
    output = Dense(NUM_CLASSES, activation='softmax')(x)
    return Model(inputs=base_model.input, outputs=output)

def parse_class_name(class_name):
    if '___' in class_name:
        parts = class_name.split('___')
        plant = parts[0].replace('_', ' ').strip()
        disease = parts[1].replace('_', ' ').strip() if len(parts) > 1 else 'Healthy'
    elif '__' in class_name:
        parts = class_name.split('__')
        plant = parts[0].replace('_', ' ').strip()
        disease = parts[1].replace('_', ' ').strip() if len(parts) > 1 else 'Healthy'
    else:
        parts = class_name.split('_')
        plant = parts[0].strip()
        disease = ' '.join(parts[1:]).strip() if len(parts) > 1 else 'Healthy'
    is_healthy = 'healthy' in disease.lower()
    return plant, disease, is_healthy

print("Building model...")
model = build_model()
model.load_weights("plantcare_weights.weights.h5")
print("Weights loaded!")

with open("class_info.json") as f:
    class_info = json.load(f)

print(f"Ready! {len(class_info)} classes loaded.")


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((224, 224))
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)


@app.get("/")
def root():
    return {"status": "PlantCare AI is running"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()
    img_array = preprocess_image(image_bytes)

    predictions = model.predict(img_array)
    predicted_idx = int(np.argmax(predictions[0]))
    confidence = float(np.max(predictions[0]))

    info = class_info[str(predicted_idx)]
    plant, disease, is_healthy = parse_class_name(info['class_name'])

    return {
        "plant": plant,
        "disease": disease,
        "is_healthy": is_healthy,
        "confidence": round(confidence * 100, 2),
        "class_name": info['class_name']
    }


@app.get("/classes")
def get_classes():
    return class_info