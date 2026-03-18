## RecycleScan
A waste disposal assistant that helps you figure out how to correctly dispose of any item. Point your camera at something, and RecycleScan identifies it, explains how to dispose of it responsibly, and surfaces nearby disposal facilities when needed.

### What it does:
- Classifies waste items from photos using a HuggingFace image classifier (ViT, ~95% accuracy)
- Explains disposal reasoning via Gemini API
- Surfaces nearby disposal facilities using Google Places API
- Logs all requests to Cloud SQL Postgres
- Safety layer catches hazardous materials before they reach the model

### Stack
Python, FastAPI, Docker, Google Cloud Run, PostgreSQL, HuggingFace, Gemini API, Google Places API

### Status
Active development. Backend in progress, hardware extension planned: an ESP32-CAM mounted near a bin that automatically captures an item when held up and signals which bin it belongs in with an LED.

### Structure
- `backend/database.py` — database models and connection
- `backend/models.py` — Pydantic schemas
- `backend/safety.py` — hazardous material detection layer
