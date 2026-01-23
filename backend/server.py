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
from PIL import Image

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
ESRGAN_ROOT = BACKEND_DIR / "Real-ESRGAN"
ESRGAN_SCRIPT = ESRGAN_ROOT / "inference_realesrgan.py"
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
    
    # Optimization: Adaptive tile size based on image dimensions
    # Tile sizes MUST be even to avoid assertion errors
    try:
        img = Image.open(input_path)
        img_area = img.size[0] * img.size[1]
        
        if img_area > 200000:  # Large image
            tile_size = "128"  # Even tile size
            tile_pad = "2"
        elif img_area > 100000:  # Medium image
            tile_size = "256"  # Even tile size
            tile_pad = "2"
        else:  # Small image
            tile_size = "512"  # Even tile size
            tile_pad = "2"
        
        sys.stderr.write(f"DEBUG: ESRGAN adaptive settings - Image: {img.size}, Area: {img_area}, Tile: {tile_size}\n")
    except Exception as e:
        tile_size = "256"
        tile_pad = "2"
        sys.stderr.write(f"DEBUG: Using default tile settings: {e}\n")
    
    sys.stderr.write(f"DEBUG: ESRGAN Step {step} - Input: {input_path}\n")
    sys.stderr.write(f"DEBUG: ESRGAN Step {step} - Output dir: {output_path}\n")
    
    command = [
        "python", 
        "inference_realesrgan.py", 
        "-n", "RealESRGAN_x2plus",  # Faster 2x upscaling instead of 4x
        "-i", str(input_path), 
        "-o", str(output_path),
        "-t", tile_size,  # Adaptive tile size
        "--tile_pad", tile_pad,  # Minimal padding
        "--fp32"  # Force full precision on CPU
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
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        with open(esrgan_initial_input_path, "wb") as out:
            out.write(data)
        
        # Verify file was saved
        if not esrgan_initial_input_path.exists():
            raise HTTPException(status_code=500, detail=f"File save failed: {esrgan_initial_input_path}")
        
        sys.stderr.write(f"DEBUG: Uploaded file saved: {esrgan_initial_input_path} ({len(data)} bytes)\n")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {exc}")

    # --- Optimization: Pre-process input image for faster upscaling ---
    try:
        img = Image.open(esrgan_initial_input_path)
        sys.stderr.write(f"DEBUG: Image opened successfully: {img.size}, mode: {img.mode}\n")
        
        # Convert to RGB first if needed
        if img.mode != "RGB":
            sys.stderr.write(f"DEBUG: Converting {img.mode} to RGB\n")
            if img.mode == "RGBA":
                img_rgb = Image.new("RGB", img.size, (255, 255, 255))
                img_rgb.paste(img, mask=img.split()[3])
                img = img_rgb
            else:
                img = img.convert("RGB")
        
        # Resize if too large (max 512 for better performance)
        max_size = 512
        if img.size[0] > max_size or img.size[1] > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            sys.stderr.write(f"DEBUG: Resized to {img.size}\n")
        
        # CRITICAL: Ensure dimensions are EVEN (divisible by 2) for ESRGAN
        width, height = img.size
        new_width = width - (width % 2)  # Make even
        new_height = height - (height % 2)  # Make even
        
        if new_width != width or new_height != height:
            img = img.crop((0, 0, new_width, new_height))
            sys.stderr.write(f"DEBUG: Cropped to even dimensions: {img.size}\n")
        
        # Verify dimensions are even
        assert img.size[0] % 2 == 0 and img.size[1] % 2 == 0, f"Dimensions still odd: {img.size}"
        
        # Save as JPEG
        img.save(esrgan_initial_input_path, format="JPEG", quality=85)
        sys.stderr.write(f"DEBUG: Preprocessed image saved with dimensions {img.size}\n")
    except Exception as e:
        sys.stderr.write(f"ERROR: Pre-processing failed: {e}\n")
        raise HTTPException(status_code=500, detail=f"Image preprocessing failed: {e}")

    # --- Handle ESRGAN Quality Options ---
    if quality == "low":
        shutil.copy(esrgan_initial_input_path, final_input_for_face_parsing)

    elif quality in {"medium", "high"}:
        input_file_name = uploaded_file_name
        
        # Clean outputs before ESRGAN step 1
        for f in ESRGAN_OUTPUT_DIR.glob("*.*"):
            try:
                os.remove(f)
            except Exception:
                pass
        
        # ESRGAN Step 1
        try:
            run_esrgan_upscale(ESRGAN_SCRIPT.parent, ESRGAN_ROOT, input_file_name, 1)
        except Exception as e:
            sys.stderr.write(f"ESRGAN Step 1 failed: {str(e)}\n")
            raise
        
        # Search for output files - try multiple patterns
        output_files_step1 = []
        for ext in ["*.png", "*.jpg", "*.jpeg"]:
            output_files_step1.extend(list(ESRGAN_OUTPUT_DIR.glob(ext)))
        if not output_files_step1:
            for ext in ["*.png", "*.jpg", "*.jpeg"]:
                output_files_step1.extend(list(ESRGAN_OUTPUT_DIR.glob(f"*/{ext}")))
        if not output_files_step1:
            for ext in ["*.png", "*.jpg", "*.jpeg"]:
                output_files_step1.extend(list(ESRGAN_OUTPUT_DIR.glob(f"**/{ext}")))
        
        if not output_files_step1:
            output_contents = list(ESRGAN_OUTPUT_DIR.rglob("*"))
            content_names = [str(p.relative_to(ESRGAN_OUTPUT_DIR)) for p in output_contents[:20]]
            sys.stderr.write(f"ESRGAN Step 1 output files not found. Directory: {ESRGAN_OUTPUT_DIR}\n")
            sys.stderr.write(f"Contents: {content_names}\n")
            raise HTTPException(status_code=500, 
                detail=f"ESRGAN Step 1 output not found. Directory: {ESRGAN_OUTPUT_DIR}. Contents: {content_names}")
        
        
        first_output_image = max(output_files_step1, key=lambda p: p.stat().st_mtime)
        sys.stderr.write(f"DEBUG: ESRGAN Step 1 output found: {first_output_image}\n")

        if quality == "high":
            # ESRGAN Step 2 - Load and fix dimensions FIRST
            step1_img = Image.open(first_output_image)
            width, height = step1_img.size
            sys.stderr.write(f"DEBUG: Step 1 output size: {step1_img.size}\n")
            
            # Ensure EVEN dimensions (divisible by 2)
            new_width = width - (width % 2)
            new_height = height - (height % 2)
            
            if new_width != width or new_height != height:
                step1_img = step1_img.crop((0, 0, new_width, new_height))
                sys.stderr.write(f"DEBUG: Step 2 input cropped to even dimensions: {step1_img.size}\n")
            
            # Verify dimensions are even
            assert step1_img.size[0] % 2 == 0 and step1_img.size[1] % 2 == 0, f"Step 2 input dimensions not even: {step1_img.size}"
            
            # Now clean up directories
            for f in ESRGAN_INPUT_DIR.glob("*.*"):
                try:
                    os.remove(f)
                except Exception:
                    pass
            
            for f in ESRGAN_OUTPUT_DIR.glob("*.*"):
                try:
                    os.remove(f)
                except Exception:
                    pass
            
            # Save the processed image for Step 2 as PNG to preserve exact dimensions
            step1_img.save(ESRGAN_INPUT_DIR / input_file_name, format="JPEG", quality=95)
            
            # Verify saved file has even dimensions
            verify_img = Image.open(ESRGAN_INPUT_DIR / input_file_name)
            if verify_img.size[0] % 2 != 0 or verify_img.size[1] % 2 != 0:
                sys.stderr.write(f"ERROR: Saved image has odd dimensions: {verify_img.size}\n")
                raise HTTPException(status_code=500, detail=f"Step 2 input has odd dimensions after save: {verify_img.size}")
            sys.stderr.write(f"DEBUG: Step 2 input saved and verified with size {verify_img.size}\n")
            
            try:
                run_esrgan_upscale(ESRGAN_SCRIPT.parent, ESRGAN_ROOT, input_file_name, 2)
            except Exception as e:
                sys.stderr.write(f"ESRGAN Step 2 failed: {str(e)}\n")
                raise

            # Search for output files from Step 2
            output_files_step2 = []
            for ext in ["*.png", "*.jpg", "*.jpeg"]:
                output_files_step2.extend(list(ESRGAN_OUTPUT_DIR.glob(ext)))
            if not output_files_step2:
                for ext in ["*.png", "*.jpg", "*.jpeg"]:
                    output_files_step2.extend(list(ESRGAN_OUTPUT_DIR.glob(f"*/{ext}")))
            if not output_files_step2:
                for ext in ["*.png", "*.jpg", "*.jpeg"]:
                    output_files_step2.extend(list(ESRGAN_OUTPUT_DIR.glob(f"**/{ext}")))
            
            if not output_files_step2:
                output_contents = list(ESRGAN_OUTPUT_DIR.rglob("*"))
                content_names = [str(p.relative_to(ESRGAN_OUTPUT_DIR)) for p in output_contents[:20]]
                sys.stderr.write(f"ESRGAN Step 2 output files not found. Contents: {content_names}\n")
                raise HTTPException(status_code=500, detail=f"ESRGAN Step 2 output not found. Contents: {content_names}")
            
            final_output_image = max(output_files_step2, key=lambda p: p.stat().st_mtime)
            sys.stderr.write(f"DEBUG: ESRGAN Step 2 output found: {final_output_image}\n")
        else:
            final_output_image = first_output_image

        sys.stderr.write(f"DEBUG: Copying output to parser: {final_output_image} -> {final_input_for_face_parsing}\n")
        shutil.copy(final_output_image, final_input_for_face_parsing)

    # --- Run Face Parsing Script ---
    if not FACE_PARSING_SCRIPT.exists():
        raise HTTPException(status_code=500, detail=f"Processing script not found at {FACE_PARSING_SCRIPT}")

    try:
        completed = subprocess.run(
            ["python", str(FACE_PARSING_SCRIPT), str(final_input_for_face_parsing), quality, palette],
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
