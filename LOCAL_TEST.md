# Local Testing Guide

Follow these steps to test the Symbol Art application on your laptop before deploying to Hugging Face.

## Prerequisites

Make sure you have:
- **Node.js 18+** (for React frontend)
- **Python 3.10+** (for backend)
- **Git** (already set up)

## Step 1: Setup the Backend

Open a **PowerShell/CMD terminal** and navigate to the backend folder:

```powershell
cd "c:\Users\Rizul garg\Documents\Projects\Picture-Equation\Website\backend"

# Create a Python virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

⏱️ **This may take 5-10 minutes** (PyTorch + models are large)

## Step 2: Run the Backend

```powershell
# Make sure you're in the backend folder and venv is activated
uvicorn server:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

✅ **Leave this terminal open and running**

## Step 3: Setup the Frontend

Open a **new terminal** (keep backend running):

```powershell
cd "c:\Users\Rizul garg\Documents\Projects\Picture-Equation\Website"

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```

You should see:
```
  VITE v5.4.2  ready in 500 ms

  ➜  Local:   http://127.0.0.1:5173/
  ➜  Press q to quit
```

## Step 4: Open the App

Go to **http://localhost:5173** in your browser

You should see the Symbol Art homepage with the upload section.

## Step 5: Test It

1. Click **"Upload"** and select a face image
2. Choose quality (Low/Medium/High)
3. Click the button to process
4. Wait for the result (should show the mathematical symbols version)
5. Click **Download** to save the output

---

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'torch'"
**Fix**: Make sure your venv is activated (`.\venv\Scripts\Activate.ps1`)

### Issue: "Connection refused" when uploading
**Fix**: Make sure backend is running on port 8000. Check the backend terminal for errors.

### Issue: "CUDA out of memory" or "OOM"
**Fix**: This is normal on laptop GPUs. The code automatically uses CPU fallback. Just wait longer.

### Issue: ESRGAN takes forever
**Fix**: This is expected! Real-ESRGAN upscaling is slow. Use "Low" quality first to test without upscaling.

### Issue: Port 5173 or 8000 already in use
**Fix**: Kill the process or change the port:
```powershell
# Frontend (change to port 3000)
npm run dev -- --port 3000

# Backend (change to port 9000)
uvicorn server:app --reload --port 9000
```

Then update vite.config.ts to proxy port 9000 instead of 8000.

---

## ✅ Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] Browser shows the Symbol Art app
- [ ] Can upload an image
- [ ] Image processes and displays result
- [ ] Can download the output

Once all ✅, you're ready to deploy to Hugging Face!
