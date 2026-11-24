# AI Background Remover — Backend

A Python-based AI backend for removing image backgrounds and generating transparent PNG images using deep-learning segmentation models.

Built with **FastAPI, PyTorch, Pillow, and Transformers**, the backend provides an HTTP API for image processing and a modular architecture for integrating multiple background-removal models.

---

## Features

- AI-powered image background removal.
- Transparent PNG output with alpha-channel preservation.
- Multiple model adapters through a shared model interface.
- Centralized model registration and management.
- CPU inference support.
- Asynchronous FastAPI endpoints with inference delegated to a thread pool.
- Image validation and upload-size restrictions.
- Automated tests for API, model services, adapters, and model management.

## Models

The backend currently integrates the following models:

| Model | Integration | Purpose |
|---|---|---|
| BiRefNet-DIS5K | Integrated into API | High-quality salient object segmentation |
| InSPyReNet | Registered through model manager | High-resolution salient object segmentation |
| BiRefNet-HR | Local experimental checkpoint | High-resolution model evaluation |

**Current API behavior:** The background-removal endpoint uses BiRefNet. InSPyReNet is available through the model manager, but automatic model selection and API-level model routing are not implemented yet.

Model weights are stored locally and are not included in this repository.

---

## Architecture

The backend uses a modular architecture that separates HTTP handling, model management, model adapters, and inference services.

```text
Client Application
       |
       v
    FastAPI
       |
       v
Background Removal API
       |
       v
   ModelManager
       |
       v
   ModelInterface
       |
       +-------------------+
       |                   |
       v                   v
 BiRefNetAdapter     InSPyReNetAdapter
       |                   |
       v                   v
 BiRefNetService     InSPyReNetService
       |                   |
       v                   v
 BiRefNet Model       InSPyReNet Model
```

### Main Components

**API Layer**
- Handles image uploads.
- Validates file types and sizes.
- Returns transparent PNG images.
- Provides health-check endpoints.

**Model Interface**
- Defines a common interface for model implementations.
- Provides shared background-removal functionality.
- Ensures consistent RGBA output.

**Model Adapters**
- Connect individual model services to the shared interface.
- Allow different segmentation models to be accessed consistently.

**Model Manager**
- Registers model adapters.
- Retrieves models using their identifiers.
- Separates model registration from model loading.

**Model Services**
- Handle model initialization and inference.
- Keep model-specific implementation details separate.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Backend language |
| FastAPI | REST API framework |
| PyTorch | Deep-learning inference |
| Transformers | BiRefNet model loading |
| InSPyReNet | Background segmentation |
| Pillow | Image processing |
| Uvicorn | ASGI server |
| Pytest | Automated testing |

---

## Project Structure

```text
bg_remover_backend/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── remove_background.py
│   │
│   ├── services/
│   │   ├── adapters/
│   │   │   ├── birefnet_adapter.py
│   │   │   └── inspyrenet_adapter.py
│   │   │
│   │   ├── birefnet_service.py
│   │   ├── inspyrenet_service.py
│   │   ├── model_interface.py
│   │   ├── model_manager.py
│   │   └── model_registry.py
│   │
│   └── main.py
│
├── models/                  # Local model weights (not tracked)
│
├── tests/
│   ├── test_api.py
│   ├── test_birefnet_adapter.py
│   ├── test_birefnet_hr_smoke.py
│   ├── test_birefnet_quality.py
│   ├── test_birefnet_service.py
│   ├── test_inspire_net_smoke.py
│   ├── test_inspyrenet_adapter.py
│   ├── test_inspyrenet_integration.py
│   ├── test_inspyrenet_service.py
│   ├── test_model_interface.py
│   ├── test_model_manager.py
│   └── test_model_registry.py
│
├── test_input.png
├── test_birefnet.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/YOUR_USERNAME/removeBG-backend.git
cd removeBG-backend
```

Replace `YOUR_USERNAME` with the GitHub account hosting the repository.

### 2. Create a virtual environment

Python 3.12 is recommended.

```powershell
py -3.12 -m venv .venv-ai
```

### 3. Activate the environment

```powershell
.\.venv-ai\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The requirements file pins the project's Python dependencies, including PyTorch and torchvision.

---

## Model Setup

Model weights are not distributed through Git because of their large file sizes.

Download or obtain the required checkpoints separately and place them in the expected local directories.

Expected layout:

```text
models/
│
├── BiRefNet-DIS5K/
│   └── model.safetensors
│
├── BiRefNet-HR/
│   └── model.safetensors
│
└── InSPyReNet/
    └── ckpt_base.pth
```

The BiRefNet-DIS5K and InSPyReNet models are used by the current model integrations.

BiRefNet-HR is retained for local experimentation and evaluation.

**Important:** The model files must be placed in their expected directories before loading the corresponding services. They are intentionally excluded from Git.

---

## Running the Backend

Start the FastAPI development server from the repository root:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

The current application loads BiRefNet during startup. Initial startup can take some time because the model must be initialized.

### API Documentation

FastAPI automatically generates interactive API documentation.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## API Reference

### 1. Root Endpoint

**GET /**

Checks whether the backend is running.

Example response:

```json
{
  "message": "AI Background Remover backend is running!"
}
```

### 2. Health Check

**GET /health**

Returns the application's current health status.

Example response:

```json
{
  "status": "healthy"
}
```

### 3. Remove Background

**POST /api/v1/remove-background**

Accepts an image and returns a PNG with a transparent background.

**Request format:** `multipart/form-data`

| Parameter | Type | Required |
|---|---|---|
| file | Image file | Yes |

**Supported formats**
- JPEG
- PNG
- WebP

**Maximum upload size:** 15 MB

**Example using cURL**

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/remove-background" \
  -F "file=@input.jpg" \
  --output background_removed.png
```

**Response**
- Content-Type: `image/png`
- Output: Transparent RGBA PNG image.

**Possible error responses**

| HTTP Status | Description |
|---|---|
| 400 | Empty, invalid, or corrupted image |
| 413 | Upload exceeds 15 MB |
| 415 | Unsupported image format |
| 500 | Background-removal processing failed |

---

## Running Tests

The project uses Pytest.

Run the complete test suite:

```powershell
pytest -v
```

Run an individual test module:

```powershell
pytest tests/test_model_manager.py -v
```

Run the API tests:

```powershell
pytest tests/test_api.py -v
```

Some tests perform actual model inference and therefore require local model checkpoints. CPU inference may take considerably longer than GPU inference.

---

## Current Limitations

- The current HTTP endpoint uses BiRefNet.
- Automatic model selection is not implemented.
- InSPyReNet is registered but not yet exposed through the background-removal API.
- Model weights must be downloaded separately.
- Model inference can be slow on CPU.
- Authentication, user management, and persistent job storage are not implemented.

---

## Roadmap

- [ ] Implement intelligent model routing.
- [ ] Expose multiple models through the API.
- [ ] Add lazy model loading and lifecycle management.
- [ ] Add model-specific inference configuration.
- [ ] Improve inference performance and memory management.
- [ ] Add structured logging and better error reporting.
- [ ] Add background-processing job management.
- [ ] Add deployment configuration.
- [ ] Expand integration and performance testing.

---

## License

Choose and add an appropriate open-source license before distributing this project publicly.

---

**AI Background Remover Backend**  
Built with Python, FastAPI, and PyTorch.