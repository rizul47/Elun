# Real-ESRGAN ImageUpscaler Deployment Guide

## 🚀 Deployment Configuration

The Real-ESRGAN ImageUpscaler has been updated with a flexible configuration system to support deployment across different environments.

### 1. **Configuration System**

The `upscaler_config.py` provides:
- **Automatic path detection**: Works with relative paths by default
- **Environment variable overrides**: For custom deployments
- **Cross-platform compatibility**: Works on Windows, Linux, and macOS
- **Directory validation**: Ensures required directories exist

### 2. **Environment Variables**

Override default paths using environment variables:

```bash
# Linux/Mac
export REALESRGAN_INPUTS_DIR="/opt/realesrgan/inputs"
export REALESRGAN_RESULTS_DIR="/opt/realesrgan/results"
export REALESRGAN_WEIGHTS_DIR="/opt/realesrgan/weights"
export REALESRGAN_DATASETS_DIR="/opt/realesrgan/datasets"

# Windows
set REALESRGAN_INPUTS_DIR=C:\apps\realesrgan\inputs
set REALESRGAN_RESULTS_DIR=C:\apps\realesrgan\results
set REALESRGAN_WEIGHTS_DIR=C:\apps\realesrgan\weights
```

### 3. **Directory Structure**

Recommended deployment structure:

```
/opt/picture-equation/ImageUpscaler/Real-ESRGAN/
├── inference_realesrgan.py          # Main inference script
├── upscaler_config.py               # Configuration system
├── realesrgan/                      # Package directory
├── inputs/                          # Input images (auto-created)
├── results/                         # Output images (auto-created)
├── weights/                         # Model weights (auto-created)
│   ├── RealESRGAN_x4plus.pth
│   └── RealESRNet_x4plus.pth
├── datasets/                        # Training datasets (optional)
│   └── DF2K/
└── experiments/                     # Pretrained models (optional)
    └── pretrained_models/
```

### 4. **Usage Examples**

#### Basic Usage (with config system):
```bash
python inference_realesrgan.py -i ./inputs/image.jpg -o ./results
```

#### Custom paths:
```bash
python inference_realesrgan.py -i /custom/input/path -o /custom/output/path
```

#### Environment variable override:
```bash
export REALESRGAN_INPUTS_DIR="/data/images"
export REALESRGAN_RESULTS_DIR="/data/upscaled"
python inference_realesrgan.py
```

### 5. **Integration with Picture-Equation Backend**

The backend configuration system automatically handles Real-ESRGAN paths:

```python
# In backend/config.py
@property
def realesrgan_dir(self) -> Path:
    custom_path = os.getenv('REALESRGAN_DIR')
    if custom_path:
        return Path(custom_path)
    return self.project_root / "ImageUpscaler" / "Real-ESRGAN"
```

### 6. **Docker Deployment**

Example Dockerfile for Real-ESRGAN:

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/ImageUpscaler/Real-ESRGAN

# Copy Real-ESRGAN files
COPY ImageUpscaler/Real-ESRGAN/ .

# Install Python dependencies
RUN pip install -r requirements.txt

# Set environment variables
ENV REALESRGAN_INPUTS_DIR=/app/inputs
ENV REALESRGAN_RESULTS_DIR=/app/results
ENV REALESRGAN_WEIGHTS_DIR=/app/weights

# Create directories
RUN mkdir -p /app/inputs /app/results /app/weights

# Download default model (optional)
# RUN python -c "from inference_realesrgan import main; main()" --help

EXPOSE 8000

CMD ["python", "inference_realesrgan.py", "--help"]
```

### 7. **Troubleshooting**

#### Common Issues:

1. **Missing model weights**: The script will automatically download them
2. **Permission errors**: Ensure write access to results directory
3. **CUDA errors**: Set `--fp32` flag for CPU inference
4. **Path not found**: Check environment variables and directory structure

#### Debug Commands:

```python
# Test configuration
python -c "from upscaler_config import upscaler_config; print(upscaler_config.validate_setup())"

# Check paths
python -c "from upscaler_config import upscaler_config; print(upscaler_config.get_inference_defaults())"
```

### 8. **Environment Variables Reference**

| Variable | Description | Default |
|----------|-------------|---------|
| `REALESRGAN_INPUTS_DIR` | Input images directory | `./inputs` |
| `REALESRGAN_RESULTS_DIR` | Output images directory | `./results` |
| `REALESRGAN_WEIGHTS_DIR` | Model weights directory | `./weights` |
| `REALESRGAN_DATASETS_DIR` | Training datasets directory | `./datasets` |
| `REALESRGAN_EXPERIMENTS_DIR` | Experiments directory | `./experiments` |
| `PICTURE_EQUATION_ROOT` | Project root override | Auto-detected |

### 9. **Performance Optimization**

For production deployments:

- Use GPU inference when available
- Set appropriate tile size for memory management
- Use FP16 precision for faster inference
- Batch process multiple images

```bash
# GPU inference with optimizations
python inference_realesrgan.py -i ./inputs -o ./results --gpu-id 0 --tile 512
```

This configuration system ensures your Real-ESRGAN upscaler works seamlessly across different deployment environments!
