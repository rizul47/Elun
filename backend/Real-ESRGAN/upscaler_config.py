"""
Configuration module for Real-ESRGAN ImageUpscaler.
Handles environment variables and deployment settings for the upscaler component.
"""
import os
from pathlib import Path
from typing import Optional

class UpscalerConfig:
    """Configuration class for Real-ESRGAN upscaler settings."""
    
    def __init__(self):
        # Get the directory where this config file is located (Real-ESRGAN directory)
        self.realesrgan_dir = Path(__file__).resolve().parent
        
        # ImageUpscaler root (parent of Real-ESRGAN)
        self.imageupscaler_root = self.realesrgan_dir.parent
        
        # Picture-Equation project root (parent of ImageUpscaler)
        self.project_root = self._get_project_root()
        
    def _get_project_root(self) -> Path:
        """
        Determine the project root directory.
        Can be overridden with PICTURE_EQUATION_ROOT environment variable.
        """
        env_root = os.getenv('PICTURE_EQUATION_ROOT')
        if env_root:
            return Path(env_root).resolve()
        
        # Default: assume Real-ESRGAN is in Picture-Equation/ImageUpscaler/Real-ESRGAN/
        return self.imageupscaler_root.parent
    
    @property
    def inputs_dir(self) -> Path:
        """Directory for input images."""
        custom_path = os.getenv('REALESRGAN_INPUTS_DIR')
        if custom_path:
            return Path(custom_path)
        return self.realesrgan_dir / "inputs"
    
    @property
    def results_dir(self) -> Path:
        """Directory for output results."""
        custom_path = os.getenv('REALESRGAN_RESULTS_DIR')
        if custom_path:
            return Path(custom_path)
        return self.realesrgan_dir / "results"
    
    @property
    def weights_dir(self) -> Path:
        """Directory for model weights."""
        custom_path = os.getenv('REALESRGAN_WEIGHTS_DIR')
        if custom_path:
            return Path(custom_path)
        return self.realesrgan_dir / "weights"
    
    @property
    def datasets_dir(self) -> Path:
        """Directory for training datasets."""
        custom_path = os.getenv('REALESRGAN_DATASETS_DIR')
        if custom_path:
            return Path(custom_path)
        return self.realesrgan_dir / "datasets"
    
    @property
    def experiments_dir(self) -> Path:
        """Directory for experiments and pretrained models."""
        custom_path = os.getenv('REALESRGAN_EXPERIMENTS_DIR')
        if custom_path:
            return Path(custom_path)
        return self.realesrgan_dir / "experiments"
    
    def ensure_directories_exist(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.inputs_dir,
            self.results_dir,
            self.weights_dir,
            self.datasets_dir / "DF2K" / "meta_info",
            self.experiments_dir / "pretrained_models",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_model_path(self, model_name: str, custom_path: Optional[str] = None) -> Path:
        """
        Get the path for a specific model.
        
        Args:
            model_name: Name of the model (e.g., 'RealESRGAN_x4plus')
            custom_path: Optional custom path override
            
        Returns:
            Path to the model file
        """
        if custom_path:
            return Path(custom_path)
        
        return self.weights_dir / f"{model_name}.pth"
    
    def get_dataset_config_paths(self) -> dict:
        """
        Get dataset configuration paths for training.
        
        Returns:
            Dictionary with dataset configuration paths
        """
        return {
            'dataroot_gt': str(self.datasets_dir / "DF2K"),
            'meta_info': str(self.datasets_dir / "DF2K" / "meta_info" / "meta_info_DF2Kmultiscale+OST_sub.txt"),
            'pretrain_network_g': str(self.experiments_dir / "pretrained_models" / "RealESRNet_x4plus.pth")
        }
    
    def validate_setup(self) -> bool:
        """
        Validate that the required directories exist for basic operation.
        Returns True if setup is valid, False otherwise.
        """
        required_paths = [
            (self.realesrgan_dir / "inference_realesrgan.py", "Inference script"),
            (self.realesrgan_dir / "realesrgan", "RealESRGAN package directory"),
        ]
        
        missing_paths = []
        for path, description in required_paths:
            if not path.exists():
                missing_paths.append(f"{description}: {path}")
        
        if missing_paths:
            print("❌ Missing required files/directories for Real-ESRGAN:")
            for missing in missing_paths:
                print(f"   - {missing}")
            return False
        
        return True
    
    def get_inference_defaults(self) -> dict:
        """
        Get default paths for inference script.
        
        Returns:
            Dictionary with default inference paths
        """
        return {
            'input': str(self.inputs_dir),
            'output': str(self.results_dir),
            'weights': str(self.weights_dir)
        }

# Global configuration instance
upscaler_config = UpscalerConfig()
