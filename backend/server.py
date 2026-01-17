from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import os
import sys
from pathlib import Path
import glob
import subprocess
import shutil

app = FastAPI()

# Allow all origins for Hugging Face deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Path Resolution for Cloud (Relative Paths) ---
BACKEND_DIR = Path(__file__).resolve().parent

# Key directories (all relative to backend folder)
TEST_IMG_DIR = BACKEND_DIR / "test_img"
ESRGAN_ROOT = BACKEND_DIR / "ImageUpscaler" / "Real-ESRGAN"
ESRGAN_SCRIPT = BACKEND_DIR / "Real-ESRGAN" / "inference_realesrgan.py"
ESRGAN_INPUT_DIR = ESRGAN_ROOT / "inputs"
ESRGAN_OUTPUT_DIR = ESRGAN_ROOT / "results"
FACE_PARSING_DIR = BACKEND_DIR / "face-parsing.PyTorch"
FACE_PARSING_SCRIPT = FACE_PARSING_DIR / "test.py"
DIVIDED_REGIONS_DIR = BACKEND_DIR / "Divided Regions"

# Ensure directories exist on startup
TEST_IMG_DIR.mkdir(parents=True, exist_ok=True)
ESRGAN_INPUT_DIR.mkdir(parents=True, exist_ok=True)
ESRGAN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DIVIDED_REGIONS_DIR.mkdir(parents=True, exist_ok=True)


def run_esrgan_upscale(script_dir: Path, input_output_dir: Path, input_file_name: str, step: int):
    """
    Runs the Real-ESRGAN inference script with memory-optimized arguments.
    script_dir: Directory where inference_realesrgan.py is located
    input_output_dir: Directory containing inputs/ and results/ folders
    """
    input_path = input_output_dir / "inputs" / input_file_name
    output_path = input_output_dir / "results/"
    
    # Verify input file exists
    if not input_path.exists():
        raise HTTPException(status_code=500, detail=f"ESRGAN input file not found: {input_path}")
    
    sys.stderr.write(f"DEBUG: ESRGAN Step {step} - Input: {input_path}\n")
    sys.stderr.write(f"DEBUG: ESRGAN Step {step} - Output dir: {output_path}\n")
    
    command = [
        "python", 
        "inference_realesrgan.py", 
        "-n", "RealESRGAN_x4plus", 
        "-i", str(input_path), 
        "-o", str(output_path),
        "-t", "64",
        "--tile_pad", "8"
    ]
    
    sys.stderr.write(f"DEBUG: Running ESRGAN Step {step} with command: {' '.join(command)}\n")

    completed = None
    try:
        completed = subprocess.run(
            command,
            cwd=str(script_dir),
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
    except subprocess.CalledProcessError as e:
        error_detail = e.stderr or e.stdout or str(e)
        sys.stderr.write(f"\n--- ESRGAN Step {step} FAILED ---\n{error_detail}\n")
        raise HTTPException(status_code=500, detail=f"ESRGAN upscale Step {step} failed: {error_detail}")

    if completed:
        sys.stderr.write(f"ESRGAN Step {step} stdout:\n{completed.stdout}\n")
        sys.stderr.write(f"ESRGAN Step {step} stderr:\n{completed.stderr}\n")
        sys.stderr.write(f"--- ESRGAN Step {step} SUCCESS ---\n")

    return completed


@app.post("/process")
async def process_image(
    file: UploadFile = File(...),
    quality: str = Form("high"),
    density: int = Form(50),
    palette: str = Form("math"),
):
    """
    Save upload, run optional ESRGAN upscaling, run face parsing script, return image.
    """
    quality = (quality or "high").strip().lower()
    if quality not in {"low", "medium", "high"}:
        raise HTTPException(status_code=400, detail="Invalid quality value. Use 'low', 'medium', or 'high'.")

    uploaded_file_name = "test.jpg"
    final_input_for_face_parsing = TEST_IMG_DIR / uploaded_file_name

    # --- Directory Setup and Cleanup ---
    try:
        TEST_IMG_DIR.mkdir(parents=True, exist_ok=True)
        ESRGAN_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        ESRGAN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        for f in ESRGAN_INPUT_DIR.glob("*.*"):
            os.remove(f)
        for f in ESRGAN_OUTPUT_DIR.glob("*.*"):
            os.remove(f)
        if final_input_for_face_parsing.exists():
            os.remove(final_input_for_face_parsing)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to set up directories: {exc}")

    # --- Save Uploaded File ---
    esrgan_initial_input_path = ESRGAN_INPUT_DIR / uploaded_file_name
    try:
        data = await file.read()
        with open(esrgan_initial_input_path, "wb") as out:
            out.write(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {exc}")

    # --- Handle ESRGAN Quality Options ---
    if quality == "low":
        shutil.copy(esrgan_initial_input_path, final_input_for_face_parsing)

    elif quality in {"medium", "high"}:
        input_file_name = uploaded_file_name
        
        # ESRGAN Step 1
        run_esrgan_upscale(ESRGAN_SCRIPT.parent, ESRGAN_ROOT, input_file_name, 1)
        
        # Search for output files - try multiple patterns
        output_files_step1 = list(ESRGAN_OUTPUT_DIR.glob("*.png"))  # Direct children
        if not output_files_step1:
            output_files_step1 = list(ESRGAN_OUTPUT_DIR.glob("*/*.png"))  # One level deep
        if not output_files_step1:
            output_files_step1 = list(ESRGAN_OUTPUT_DIR.glob("**/*.png"))  # Recursive
        
        if not output_files_step1:
            output_contents = list(ESRGAN_OUTPUT_DIR.rglob("*"))
            content_names = [str(p.relative_to(ESRGAN_OUTPUT_DIR)) for p in output_contents[:20]]
            raise HTTPException(status_code=500, 
                detail=f"ESRGAN Step 1 output not found. Directory: {ESRGAN_OUTPUT_DIR}. Contents: {content_names}")
        
        
        first_output_image = max(output_files_step1, key=lambda p: p.stat().st_mtime)

        if quality == "high":
            # ESRGAN Step 2
            for f in ESRGAN_INPUT_DIR.glob("*.*"):
                os.remove(f)
            
            shutil.copy(first_output_image, ESRGAN_INPUT_DIR / input_file_name)
            run_esrgan_upscale(ESRGAN_SCRIPT.parent, ESRGAN_ROOT, input_file_name, 2)

            # Search for output files from Step 2
            output_files_step2 = list(ESRGAN_OUTPUT_DIR.glob("*.png"))
            if not output_files_step2:
                output_files_step2 = list(ESRGAN_OUTPUT_DIR.glob("*/*.png"))
            if not output_files_step2:
                output_files_step2 = list(ESRGAN_OUTPUT_DIR.glob("**/*.png"))
            
            if not output_files_step2:
                raise HTTPException(status_code=500, detail="ESRGAN Step 2 output not found.")
            
            final_output_image = max(output_files_step2, key=lambda p: p.stat().st_mtime)
        else:
            final_output_image = first_output_image

        sys.stderr.write(f"DEBUG: Copying output to parser: {final_output_image} -> {final_input_for_face_parsing}\n")
        shutil.copy(final_output_image, final_input_for_face_parsing)

    # --- Run Face Parsing Script ---
    if not FACE_PARSING_SCRIPT.exists():
        raise HTTPException(status_code=500, detail=f"Processing script not found at {FACE_PARSING_SCRIPT}")

    try:
        completed = subprocess.run(
            ["python", str(FACE_PARSING_SCRIPT), str(final_input_for_face_parsing)],
            cwd=str(FACE_PARSING_DIR),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to execute processing script: {exc}")

    if completed.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Script failed: {completed.stderr or completed.stdout}")

    # --- Locate and Return Output ---
    candidates = []
    for search_dir in [DIVIDED_REGIONS_DIR, FACE_PARSING_DIR, BACKEND_DIR]:
        for pattern in ["gift_worthy_mathematical_face*", "gift-worthy*"]:
            for ext in ("png", "jpg", "jpeg", "webp"):
                candidates.extend(
                    glob.glob(str(search_dir / f"**/{pattern}.{ext}"), recursive=True)
                )

    if not candidates:
        raise HTTPException(status_code=500, detail="Processed output not found.")

    output_path = max((Path(p) for p in candidates), key=lambda p: p.stat().st_mtime)

    # Cleanup input file
    try:
        if final_input_for_face_parsing.exists():
            os.remove(final_input_for_face_parsing)
    except Exception:
        pass

    return FileResponse(path=str(output_path), media_type="image/png")


# --- Health check endpoint for Hugging Face ---
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# --- Serve React Frontend (Static Files) ---
# Serve index.html for root and SPA routing
@app.get("/", response_class=FileResponse)
async def serve_index():
    dist_path = BACKEND_DIR / "dist" / "index.html"
    if dist_path.exists():
        return dist_path
    return {"error": "Frontend not built"}

# Mount other static assets
dist_path = BACKEND_DIR / "dist"
if dist_path.exists() and (dist_path / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="assets")
