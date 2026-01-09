# app.py - Python Flask Backend for Mathematical Face Generator

import os
import base64
import json
import io
import random
import math
import numpy as np
from flask import Flask, request, render_template, jsonify
from PIL import Image, ImageDraw, ImageFont

# Initialize the Flask application
# The template_folder='.' tells Flask to look for HTML files in the same directory.
app = Flask(__name__, template_folder='.')

# --- Python Logic for Mathematical Face Generation (Ported from Mathface.txt) ---
# This section contains the core logic for processing the image and generating the math face.
# It is a self-contained function that can be called by the Flask route.

def safe_gamma(brightness_val, gamma_val):
    """
    Applies gamma correction safely.
    :param brightness_val: Normalized brightness (0-1).
    :param gamma_val: Gamma value.
    :return: Gamma-corrected brightness (0-1).
    """
    if brightness_val <= 0.0:
        return 0.0
    return brightness_val ** gamma_val

# Hardcoded region maps based on your Python script
REGION_SYMBOLS_MAP = {
    1: ['∂', '∑', '√', '≈', '∇', '∞'],       # Face
    2: ['—', '−', '≡', '―', '∼'],           # Eyebrow L
    3: ['—', '−', '≡', '―', '∼'],           # Eyebrow R
    4: ['●', '◉', '◎', '○', '◍'],           # Eye L
    5: ['●', '◉', '◎', '○', '◍'],           # Eye R
    7: ['∫', '∮', 'Ω', 'σ', 'θ'],           # Ear L
    8: ['∫', '∮', 'Ω', 'σ', 'θ'],           # Ear R
    10: ['|', '‖', '∣', '∥', '+'],          # Nose
    12: ['⌒', '∩', '∪', '⌓', '∿'],         # Lower lip
    13: ['⌒', '∩', '∪', '⌓', '∿'],         # Upper lip
    14: ['∏', 'Π', 'µ', 'ω', 'φ'],          # Neck
    16: ['Σ', 'π', '∑', 'λ', 'Ψ', 'Ω'],     # Hair
    17: ['Σ', 'π', '∑', 'λ', 'Ψ', 'Ω']      # Hair
}

REGION_OPACITY_MAP = {
    4: 170, 5: 170,
    12: 170, 13: 170,
    2: int(255 * 0.85), 3: int(255 * 0.85),
    10: int(255 * 0.90),
    1: int(255 * 0.60),
    7: int(255 * 0.75), 8: int(255 * 0.75),
    14: int(255 * 0.70),
    16: int(255 * 0.80), 17: int(255 * 0.80),
}

REGION_IMPORTANCE_MAP = {
    1: 1.0, 2: 1.1, 3: 1.1,
    4: 1.3, 5: 1.3,
    7: 1.0, 8: 1.0,
    10: 1.0,
    12: 1.2, 13: 1.2,
    14: 1.0,
    16: 0.9, 17: 0.9
}

REGION_STYLE_MAP = {
    1: [12, 10], 2: [9, 6], 3: [9, 6], 4: [9, 5], 5: [9, 5],
    7: [9, 7], 8: [9, 7], 10: [10, 8], 12: [8, 5],
    13: [8, 5], 14: [10, 8], 16: [8, 7], 17: [8, 7]
}

def get_region_id(region_key):
    """Maps string key from frontend to region ID used in Python maps."""
    mapping = {
        'skin': 1, 'l_brow': 2, 'r_brow': 3, 'l_eye': 4, 'r_eye': 5,
        'l_ear': 7, 'r_ear': 8, 'nose': 10, 'u_lip': 12, 'l_lip': 13,
        'neck': 14, 'cloth': 16, 'hair': 17
    }
    return mapping.get(region_key, 0)

def generate_mathematical_face(image_data, settings):
    """
    Generates the mathematical face image using the original Python logic.
    :param image_data: Binary image data from the frontend.
    :param settings: JSON object with user settings.
    :return: Base64-encoded image string.
    """
    try:
        # Load the image from binary data
        original_im = Image.open(io.BytesIO(image_data)).convert("RGB")
        width, height = original_im.size
        
        # Create a blank image to draw on
        canvas = Image.new('RGB', (width, height), 'black')
        d_canvas = ImageDraw.Draw(canvas)
        
        # --- PLACEHOLDER FOR FACE PARSING ---
        # The original Python script uses a BiSeNet model for this step.
        # This is a simplified placeholder that creates a single 'skin' region.
        # To get the perfect segmented result, you must replace this with
        # the BiSeNet model and its parsing logic.
        # Your original code would go here:
        # e.g., parsing_anno = BiSeNet(im_tensor)
        
        # This is a simple dummy mask that marks the whole face as 'skin' (ID 1)
        parsing_anno_np = np.full((height, width), 1, dtype=np.uint8)
        # --- END PLACEHOLDER ---

        # Gamma correction value
        gamma = 0.75
        jitter_cap_px = 2

        for region_key, region_settings in settings.items():
            region_id = get_region_id(region_key)
            if region_id == 0:
                continue

            symbols = REGION_SYMBOLS_MAP.get(region_id, region_settings['symbols'])
            if not symbols:
                continue

            # Get base font size and step from Python's style map
            base_font, step_base = REGION_STYLE_MAP.get(region_id, [9, 6])
            region_importance = REGION_IMPORTANCE_MAP.get(region_id, 1.0)
            
            # Adjust step based on the density setting
            density_val = region_settings['density'] / 100.0
            step = max(1, math.floor(step_base * (1.0 - density_val) + 1))
            
            rotation_range = region_settings['rotation']
            brightness_factor = region_settings['brightness'] / 100.0
            opacity_factor = region_settings['opacity'] / 100.0

            im_pixels = original_im.load()

            for y in range(0, height, step):
                for x in range(0, width, step):
                    if parsing_anno_np[y, x] == region_id:
                        # Get pixel brightness from the original image
                        r, g, b = im_pixels[x, y]
                        raw_brightness = (r + g + b) / 3
                        
                        # Apply gamma correction and UI brightness
                        brightness_norm = raw_brightness / 255.0
                        adjusted_brightness = safe_gamma(brightness_norm, gamma) * brightness_factor
                        
                        # Calculate symbol color based on adjusted brightness
                        symbol_color_val = int(adjusted_brightness * 255)
                        symbol_color = (symbol_color_val, symbol_color_val, symbol_color_val)
                        
                        # Apply UI opacity
                        alpha = int(opacity_factor * 255)
                        symbol_color_with_alpha = symbol_color + (alpha,)

                        # Symbol sizing logic ported from Mathface.txt
                        size_factor = 0.9 + 0.5 * (1 - brightness_norm)
                        size_factor *= region_importance
                        min_size = max(9, int(base_font * 0.85))
                        final_size = max(min_size, int(base_font * size_factor))
                        
                        # Load font with calculated size
                        # Using a generic font that should be available on most systems
                        font = ImageFont.truetype("arial.ttf", final_size)
                        
                        # Get a random symbol
                        sym = random.choice(symbols)
                        
                        # Create a transparent symbol image
                        text_im = Image.new('RGBA', (final_size * 2, final_size * 2))
                        d_text = ImageDraw.Draw(text_im)
                        d_text.text((final_size, final_size), sym, fill=symbol_color_with_alpha, font=font)
                        
                        # Rotate the symbol
                        rot_angle = random.randint(-rotation_range, rotation_range)
                        text_im_rotated = text_im.rotate(rot_angle, expand=1)

                        # Apply jitter
                        jitter_x = random.randint(-jitter_cap_px, jitter_cap_px)
                        jitter_y = random.randint(-jitter_cap_px, jitter_cap_px)
                        
                        # Paste the symbol onto the main canvas
                        canvas.paste(text_im_rotated, (x + jitter_x, y + jitter_y), text_im_rotated)

        # Save the final image to a buffer
        img_buffer = io.BytesIO()
        canvas.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Convert to base64 for sending to frontend
        base64_img = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        return base64_img
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# --- Flask Routes ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_image_route():
    """
    Handles the image generation request from the frontend.
    Receives image data and settings, calls the generator, and returns the result.
    """
    data = request.json
    image_b64 = data.get('imageData').split(',')[1]
    settings = data.get('settings')

    # Decode base64 image data
    image_data = base64.b64decode(image_b64)

    # Generate the new image
    generated_image_b64 = generate_mathematical_face(image_data, settings)

    if generated_image_b64:
        return jsonify({'image': generated_image_b64})
    else:
        return jsonify({'error': 'Image generation failed'}), 500

if __name__ == '__main__':
    # You can change the port and debug settings as needed
    app.run(debug=True, port=5000)
