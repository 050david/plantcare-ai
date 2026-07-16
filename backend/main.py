from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
import numpy as np
from PIL import Image
import json
import io
from datetime import datetime

from database import get_db, User, Scan, create_tables
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_current_admin
)
from pydantic import BaseModel, EmailStr

app = FastAPI(title="PlantCare AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables on startup
create_tables()

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


# --- Pydantic Schemas ---
class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Auth Routes ---
@app.get("/")
def root():
    return {"status": "PlantCare AI is running"}


@app.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user": {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "is_admin": user.is_admin
    }}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user": {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "is_admin": user.is_admin
    }}


@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }


# --- Predict Route ---
@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()
    img_array = preprocess_image(image_bytes)

    predictions = model.predict(img_array)
    predicted_idx = int(np.argmax(predictions[0]))
    confidence = float(np.max(predictions[0]))

    info = class_info[str(predicted_idx)]
    plant, disease, is_healthy = parse_class_name(info['class_name'])

    # Save scan to history
    scan = Scan(
        user_id=current_user.id,
        plant=plant,
        disease=disease,
        is_healthy=is_healthy,
        confidence=str(round(confidence * 100, 2)),
        class_name=info['class_name']
    )
    db.add(scan)
    db.commit()

    return {
        "plant": plant,
        "disease": disease,
        "is_healthy": is_healthy,
        "confidence": round(confidence * 100, 2),
        "class_name": info['class_name']
    }


# --- Scan History ---
@app.get("/history")
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scans = db.query(Scan).filter(Scan.user_id == current_user.id).order_by(Scan.created_at.desc()).all()
    return [{
        "id": s.id,
        "plant": s.plant,
        "disease": s.disease,
        "is_healthy": s.is_healthy,
        "confidence": s.confidence,
        "class_name": s.class_name,
        "created_at": s.created_at
    } for s in scans]


# --- Admin Routes ---
@app.get("/admin/users")
def get_all_users(current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "is_admin": u.is_admin,
        "created_at": u.created_at,
        "scan_count": len(u.scans)
    } for u in users]


@app.get("/admin/scans")
def get_all_scans(current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    scans = db.query(Scan).order_by(Scan.created_at.desc()).all()
    return [{
        "id": s.id,
        "user_id": s.user_id,
        "plant": s.plant,
        "disease": s.disease,
        "is_healthy": s.is_healthy,
        "confidence": s.confidence,
        "created_at": s.created_at
    } for s in scans]


@app.get("/classes")
def get_classes():
    return class_info