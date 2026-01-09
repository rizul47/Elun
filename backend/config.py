"""
Configuration module for Picture-Equation backend.
Handles environment variables and deployment settings.
"""
import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuration class that handles both development and production settings."""
    
    def __init__(self):
        # Get the directory where this config file is located
        self.backend_dir = Path(__file__).resolve().parent
        
        # Default project structure: Picture-Equation/Website/backend/
        self.project_root = self._get_project_root()
        
    def _get_project_root(self) -> Path:
        """
        Determine the project root directory.
        Can be overridden with PICTURE_EQUATION_ROOT environment variable.
        """
        env_root = os.getenv('PICTURE_EQUATION_ROOT')
        if env_root:
            return Path(env_root).resolve()
        
        # Default: assume backend is in Picture-Equation/Website/backend/
        return self.backend_dir.parent.parent
    
    @property
    def test_img_dir(self) -> Path:
        """Directory for test images."""
        custom_path = os.getenv('TEST_IMG_DIR')
        if custom_path:
            return Path(custom_path)
        return self.backend_dir / "test_img"
    
    @property
    def face_parsing_dir(self) -> Path:
        """Directory for face parsing scripts."""
        custom_path = os.getenv('FACE_PARSING_DIR')
        if custom_path:
            return Path(custom_path)
        return self.backend_dir / "face-parsing.PyTorch"
    
    @property
    def divided_regions_dir(self) -> Path:
        """Directory for divided regions output."""
        custom_path = os.getenv('DIVIDED_REGIONS_DIR')
        if custom_path:
            return Path(custom_path)
        return self.backend_dir / "Divided Regions"
    
    @property
    def final_output_file(self) -> Path:
        """Path to the final mathematical face output."""
        return self.divided_regions_dir / "gift_worthy_mathematical_face.png"
    
    @property
    def realesrgan_dir(self) -> Path:
        """Directory for Real-ESRGAN upscaler."""
        custom_path = os.getenv('REALESRGAN_DIR')
        if custom_path:
            return Path(custom_path)
        return self.backend_dir / "Real-ESRGAN"
    
    @property
    def realesrgan_inputs(self) -> Path:
        """Real-ESRGAN inputs directory."""
        return self.realesrgan_dir / "inputs"
    
    @property
    def realesrgan_results(self) -> Path:
        """Real-ESRGAN results directory."""
        return self.realesrgan_dir / "results"
    
    def ensure_directories_exist(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.test_img_dir,
            self.divided_regions_dir,
            self.realesrgan_inputs,
            self.realesrgan_results,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_setup(self) -> bool:
        """
        Validate that the required directories and files exist.
        Returns True if setup is valid, False otherwise.
        """
        required_paths = [
            (self.face_parsing_dir / "test.py", "Face parsing script"),
            (self.face_parsing_dir / "model.py", "BiSeNet model file"),
        ]
        
        missing_paths = []
        for path, description in required_paths:
            if not path.exists():
                missing_paths.append(f"{description}: {path}")
        
        if missing_paths:
            print("❌ Missing required files/directories:")
            for missing in missing_paths:
                print(f"   - {missing}")
            return False
        
        return True

# Global configuration instance
config = Config()
