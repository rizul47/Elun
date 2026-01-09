from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import subprocess
from pathlib import Path
import os
import uvicorn
from config import config

app = FastAPI()

# Allow your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://192.168.1.10:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate setup and ensure directories exist
if not config.validate_setup():
    print("⚠️  Warning: Some required files are missing. The application may not work correctly.")

config.ensure_directories_exist()
print(f"✅ Configuration loaded. Project root: {config.project_root}")

realesrgan_model_name = "RealESRGAN_x4plus"

def clean_folder(folder: Path):
    for f in folder.glob("*"):
        if f.is_file():
            try:
                f.unlink()
            except Exception:
                pass

def run_realesrgan(input_path: Path, output_dir: Path):
    script_path = config.realesrgan_dir / "inference_realesrgan.py"
    cmd = [
        "python", str(script_path),
        "-n", realesrgan_model_name,
        "-i", str(input_path),
        "-o", str(output_dir),
        "-t", "400"
    ]
    result = subprocess.run(cmd, cwd=str(config.realesrgan_dir), capture_output=True, text=True)
    if result.returncode != 0:
        print("Real-ESRGAN failed:")
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Real-ESRGAN processing failed")
    
    output_files = list(output_dir.glob("*"))
    if not output_files:
         raise RuntimeError(f"Real-ESRGAN did not produce expected output at {output_dir}")
    
    return max(output_files, key=os.path.getctime)

@app.post("/process")
async def process_image(
    file: UploadFile = File(...),
    quality: str = Form("low"),  # Expected: low, medium, high
    palette: str = Form("math")  # Currently unused
):
    print("--- Starting image processing pipeline ---")
    print(f"Requested quality: {quality}")

    # Clean input/output folders
    clean_folder(config.realesrgan_inputs)
    clean_folder(config.realesrgan_results)
    print("-> Cleaned Real-ESRGAN input/output folders.")

    # Save uploaded file to Real-ESRGAN input folder
    upload_path = config.realesrgan_inputs / "test.jpg"
    try:
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")
    finally:
        file.file.close()
    print(f"-> Uploaded file saved to {upload_path}")

    # Decide how many upscales based on quality
    upscale_times = 0
    if quality.lower() == "medium":
        upscale_times = 1
    elif quality.lower() == "high":
        upscale_times = 2

    # Run Real-ESRGAN if needed
    current_input = upload_path
    for i in range(upscale_times):
        print(f"-> Running Real-ESRGAN upscale {i+1}/{upscale_times}...")
        output_file = run_realesrgan(current_input, config.realesrgan_results)
        # Next upscale input is output of previous
        current_input = output_file
        print(f"-> Upscale {i+1} complete. Output: {output_file}")

    # After upscaling (or directly if low quality), copy input to test_img for face parsing
    target_test_img = config.test_img_dir / "test.jpg"
    shutil.copy(current_input, target_test_img)
    print(f"-> File copied to face parsing input: {target_test_img}")

    # Run face parsing
    try:
        print("-> Running face-parsing script...")
        proc = subprocess.run(
            ["python", "test.py"],
            cwd=str(config.face_parsing_dir),
            capture_output=True,
            text=True
        )
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr)
            raise RuntimeError("Face-parsing script failed.")
        print("-> Face-parsing script completed successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face parsing failed: {e}")

    # Return final output
    if not config.final_output_file.exists():
        raise HTTPException(status_code=500, detail=f"Final output not found: {config.final_output_file}")

    print("-> Pipeline completed successfully!")
    return FileResponse(path=str(config.final_output_file), media_type="image/png", filename=config.final_output_file.name)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
