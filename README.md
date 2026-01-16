---
title: Elun
emoji: 🎨
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# Elun - Image Processing Pipeline

A full-stack application that processes images through face parsing and upscaling using Real-ESRGAN and face-parsing.PyTorch models.

## Project Structure

```
Elun/
├── backend/              # Python FastAPI server
│   ├── server.py        # Main FastAPI application
│   ├── config.py        # Configuration management
│   ├── main.py          # Alternative entry point
│   ├── requirements.txt  # Python dependencies
│   ├── face-parsing.PyTorch/  # Face parsing model
│   └── Real-ESRGAN/     # Image upscaler model
├── src/                 # React frontend
│   ├── App.tsx
│   └── components/
├── public/              # Static assets
├── vite.config.ts       # Vite configuration
├── package.json         # Node dependencies
└── tsconfig.json        # TypeScript config
```

## Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **pip** (Python package manager)
- **npm** or **yarn** (Node package manager)

## Installation

### 1. Clone/Setup

Navigate to the project directory:
```bash
cd Elun
```

### 2. Backend Setup

**Install Python dependencies:**

```bash
cd backend
pip install -r requirements.txt
```

**Note:** The Real-ESRGAN and face-parsing models are large and may take time to download on first run.

### 3. Frontend Setup

Navigate back to root and install Node dependencies:

```bash
cd ..
npm install
```

Or with yarn:
```bash
yarn install
```

## Running the Project

### Option A: Using Batch Scripts (Windows)

From the project root, double-click:
- `start-backend.bat` - Starts the FastAPI server
- `start-frontend.bat` - Starts the Vite dev server

### Option B: Manual Terminal Commands

**Terminal 1 - Start Backend:**
```bash
cd backend
uvicorn server:app --reload --port 5000
```

**Terminal 2 - Start Frontend:**
```bash
npm run dev
```

The frontend will be available at: `http://localhost:5173`

## Configuration

Edit `backend/config.py` to adjust:
- Project paths
- Model settings
- Processing parameters

## Project Features

- **Image Upload**: Upload images for processing
- **Quality Options**: Low, Medium, High (with Real-ESRGAN upscaling)
- **Face Parsing**: Automatically detects and processes facial regions
- **Background Processing**: Images process asynchronously in the background
- **Real-time Updates**: Frontend polls for processing status

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/process` | POST | Upload image for processing |
| `/health` | GET | Health check |

## Next Steps

- Configure Supabase for image storage (optional)
- Add authentication
- Deploy to production
- Add more processing models

## Troubleshooting

### Backend won't start
- Check Python 3.8+ is installed: `python --version`
- Verify all dependencies: `pip install -r requirements.txt`
- Try running from the `backend/` directory

### Frontend won't start
- Clear node_modules: `rm -r node_modules && npm install`
- Check Node version: `node --version`

### Models not downloading
- Ensure internet connection is stable
- Models download to `backend/Real-ESRGAN/weights/` and `backend/face-parsing.PyTorch/res/cp/`
- First run may take 5-10 minutes

## Development

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python subprocess for ML models
- **ML Models**: Real-ESRGAN (upscaling), face-parsing.PyTorch (segmentation)

## License

See individual model repositories for licensing information.
