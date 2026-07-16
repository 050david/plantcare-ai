# PlantCare AI 🌿

An AI-powered plant disease detection and health advisory web application.

## What it does
- Upload a photo of a plant leaf
- AI identifies the plant species and detects diseases
- Shows confidence score, disease info, and treatment recommendations
- Saves scan history per user
- Admin dashboard for managing users and scans

## Project Structure
- backend/ — FastAPI backend + ML model
- frontend/ — HTML/CSS/JS frontend

## Setup Instructions

### Prerequisites
- Python 3.9+
- The model weights file (ask David or re-train using the Colab notebook)

### 1. Get the model weights
Place `plantcare_weights.weights.h5` in the `backend/` folder.

### 2. Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn tensorflow pillow python-multipart "python-jose[cryptography]" "passlib[bcrypt]==4.0.1" sqlalchemy "pydantic[email]"
./venv/bin/uvicorn main:app --reload

Backend runs on http://127.0.0.1:8000

### 3. Frontend setup
cd frontend
python3 -m http.server 3001

Open http://localhost:3001 in your browser.

## Model Info
- Architecture: MobileNetV2 (transfer learning)
- Dataset: PlantVillage (20,639 images, 15 classes)
- Validation accuracy: 95.34%
- Classes: Tomato (9 diseases), Potato (3), Pepper (2)

## Team
- David Oppong Bawuah
- Drusilla Osei Takyiaw
- Lemuel Ofosu-Adjei
- Kennedy Okom
