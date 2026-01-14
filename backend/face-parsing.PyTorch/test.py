#!/usr/bin/python
# -*- encoding: utf-8 -*-

from logger import setup_logger
from model import BiSeNet
import torch
import os
import os.path as osp
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torchvision.transforms as transforms
import cv2
import random
import json
import io
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None 
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def vis_parsing_maps(im, parsing_anno, stride, save_im=False, save_path='vis_results/parsing_map_on_im.jpg'):
    # Colors for all 20 parts
    part_colors = [[255, 0, 0], [255, 85, 0], [255, 170, 0],
                   [255, 0, 85], [255, 0, 170],
                   [0, 255, 0], [85, 255, 0], [170, 255, 0],
                   [0, 255, 85], [0, 255, 170],
                   [0, 0, 255], [85, 0, 255], [170, 0, 255],
                   [0, 85, 255], [0, 170, 255],
                   [255, 255, 0], [255, 255, 85], [255, 255, 170],
                   [255, 0, 255], [255, 85, 255], [255, 170, 255],
                   [0, 255, 255], [85, 255, 255], [170, 255, 255]]

    im = np.array(im)
    vis_im = im.copy().astype(np.uint8)
    vis_parsing_anno = parsing_anno.copy().astype(np.uint8)
    vis_parsing_anno = cv2.resize(vis_parsing_anno, None, fx=stride, fy=stride, interpolation=cv2.INTER_NEAREST)
    vis_parsing_anno_color = np.zeros((vis_parsing_anno.shape[0], vis_parsing_anno.shape[1], 3), dtype=np.uint8) + 255

    num_of_class = np.max(vis_parsing_anno)

    for pi in range(1, num_of_class + 1):
        if pi < len(part_colors):  # Safety
            index = np.where(vis_parsing_anno == pi)
            vis_parsing_anno_color[index[0], index[1], :] = part_colors[pi]

    vis_parsing_anno_color = vis_parsing_anno_color.astype(np.uint8)
    vis_im = cv2.addWeighted(cv2.cvtColor(vis_im, cv2.COLOR_RGB2BGR), 0.4, vis_parsing_anno_color, 0.6, 0)

    # Save result (only visualizations!)
    if save_im:
        # Visualization overlay
        cv2.imwrite(save_path, vis_im, [int(cv2.IMWRITE_JPEG_QUALITY), 100])  # Only saves *visualization* overlay

def evaluate(respth='./res/test_res', dspth='./data', cp='model_final_diss.pth'):
    if not os.path.exists(respth):
        os.makedirs(respth)

    n_classes = 19
    net = BiSeNet(n_classes=n_classes)

    # Check if CUDA is available, otherwise use CPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    net.to(device)

    save_pth = osp.join('res/cp', cp)
    net.load_state_dict(torch.load(save_pth, map_location=device))
    net.eval()

    to_tensor = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    ])

    with torch.no_grad():
        # Handle both file path and directory path
        if os.path.isfile(dspth):
            # Single file passed
            image_paths = [os.path.basename(dspth)]
            dspth = os.path.dirname(dspth)
        else:
            # Directory passed
            image_paths = os.listdir(dspth)
        
        for image_path in image_paths:
            img = Image.open(osp.join(dspth, image_path)).convert('RGB')
            image = img.resize((512, 512), Image.BILINEAR)
            img_tensor = to_tensor(image)
            img_tensor = torch.unsqueeze(img_tensor, 0)
            img_tensor = img_tensor.to(device)
            out = net(img_tensor)[0]
            parsing = out.squeeze(0).cpu().numpy().argmax(0)  # 2D array: class indices

            # --- The KEY: Save the raw label map as PNG using PIL only ---
            label_save_path = osp.join(respth, image_path[:-4] + '_label.png')
            Image.fromarray(parsing.astype(np.uint8)).save(label_save_path)
            print(f"Saved raw label map: {label_save_path}")

            # Save colored visualization overlay (optional)
            vis_save_path = osp.join(respth, image_path[:-4] + '_overlay.jpg')
            vis_parsing_maps(image, parsing, stride=1, save_im=True, save_path=vis_save_path)

# Script 2 code
def extract_regions():
    # Paths - Using relative paths from the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level from face-parsing.PyTorch
    
    orig_path = os.path.join(project_root, "test_img", "test.jpg")
    parsing_path = os.path.join(script_dir, "res", "test_res", "test_label.png")
    output_dir = os.path.join(project_root, "Divided Regions")

    # Clear the output directory to avoid conflicts with old region files
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
        print(f"🧹 Cleared old region files from: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)

    # Load images
    orig = np.array(Image.open(orig_path).convert('RGB'))
    parsing = np.array(Image.open(parsing_path))

    # Optionally, print present region indices
    unique_indices = np.unique(parsing)
    print('Present region indices:', unique_indices)

    for idx in unique_indices:
        # Skip background if you wish
        if idx == 0:
            continue

        mask = (parsing == idx).astype(np.uint8)

        # Resize mask to match original image if needed:
        if mask.shape[:2] != orig.shape[:2]:
            mask = np.array(Image.fromarray(mask * 255).resize(
                (orig.shape[1], orig.shape[0]), resample=Image.NEAREST)) // 255

        # Multiply to get only that region in color
        part_image = orig * mask[:, :, None]

        # Save with clear index
        filename = f"region_{idx}.png"
        Image.fromarray(part_image).save(os.path.join(output_dir, filename))
        print(f"Saved {filename}")

    print("Done! All segmented region images saved in:", output_dir)

# Script 3 code - INTEGRATED WITH YOUR PROVIDED LOGIC
def create_math_face():
    # ---------------- Config ----------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level from face-parsing.PyTorch
    base_path = os.path.join(project_root, "Divided Regions")
    region_indices = [i for i in range(1, 18)]

    # Region-specific math symbol sets
    region_symbols_map = {
    1:  ['∂', '∑', '√', '≈', '∇', '∞'],        # Face (skin)
    2:  ['—', '−', '≡', '―', '∼'],             # Eyebrow L  n
    3:  ['—', '−', '≡', '―', '∼'],             # Eyebrow R  n
    4:  ['●', '◉', '◎', '○', '◍'],             # Eye L     y
    5:  ['●', '◉', '◎', '○', '◍'],             # Eye R     y
    6:  ['▭', '▬', '═', '≡', '≣'],             # Eyeglasses n
    7:  ['∫', '∮', 'Ω', 'σ', 'θ'],             # Ear L       y
    8:  ['∫', '∮', 'Ω', 'σ', 'θ'],             # Ear R       y
    9:  ['⇔', '⇒', '⟹', '→', '↠'],             # Nose Glasses Bridge n
    10: ['|', '‖', '∣', '∥', '+'],             # Nose     y
    11: ['⧉', '◧', '◨', '▣', '⊞'],             # Mouth Interior / Teeth y
    12: ['⌒', '∩', '∪', '⌓', '∿'],            # Lower lip n
    13: ['⌒', '∩', '∪', '⌓', '∿'],            # Upper lip n
    14: ['∏', 'Π', 'µ', 'ω', 'φ'],             # Neck y
    15: ['☼', '✶', '✷', '✸', '✹'],            # Hat / Head accessory n
    16: ['Σ', 'π', '∑', 'λ', 'Ψ', 'Ω'],        # Hair n
    17: ['Σ', 'π', '∑', 'λ', 'Ψ', 'Ω']         # Hair (alt / background overlap) n
}

    region_opacity_map = {
        4: 170, 5: 170,                   # Eyes - full opacity (100%)
        12: 170, 13: 170,                  # Lips - full opacity (100%)
        2: int(255 * 0.85), 3: int(255 * 0.85),  # Eyebrows - 85% opacity
        10: int(255 * 0.90),                  # Nose - 90% opacity
        1: int(255 * 0.60),                   # Face - 60% opacity (background texture)
        7: int(255 * 0.75), 8: int(255 * 0.75),  # Ears - 75% opacity
        14: int(255 * 0.70),                  # Neck - 70% opacity
        16: int(255 * 0.80), 17: int(255 * 0.80), # Hair - 80% opacity
    }

    # Region importance factor (kept for sizing)
    region_importance_map = {
        1: 1.0,  2: 1.1, 3: 1.1,
        4: 1.3, 5: 1.3,
        7: 1.0, 8: 1.0,
        10: 1.0,
        12: 1.2, 13: 1.2,
        14: 1.0,
        16: 0.9, 17: 0.9
    }

    # Base font size and step
    region_style_map = {
        1: (12, 10), 2: (9, 6), 3: (9, 6), 4: (9, 5), 5: (9, 5),
        7: (9, 7), 8: (9, 7), 10: (10, 8), 12: (8, 5),
        13: (8, 5), 14: (10, 8), 16: (8, 7), 17: (8, 7)
    }

    # Style params
    jitter_cap_px = 2
    rot_range_deg = 8
    gamma = 0.75

    def safe_gamma(bright):
        b = np.clip(bright / 255.0, 0, 1)
        g = b ** gamma
        return int(np.clip(g * 255, 0, 255))

    def size_mapping(base, brightness, region_importance=1.0):
        brightness_norm = brightness / 255.0
        size_factor = 0.9 + 0.5 * (1 - brightness_norm)
        min_size = max(9, int(base * 0.85))
        size_factor *= region_importance
        return max(min_size, int(base * size_factor))

    def load_font(size):
        # Prioritize fonts with math symbol support
        fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuMathTeXGyre.ttf",  # Math symbols
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",     # Fallback
            "cour.ttf", 
            "arial.ttf"
        ]
        for font_name in fonts:
            try:
                return ImageFont.truetype(font_name, size)
            except (IOError, OSError):
                continue
        return ImageFont.load_default()

    # ---------------- Pre-scan regions to set canvas ----------------
    sizes = []
    available_regions = []

    for region_id in region_indices:
        p = os.path.join(base_path, f"region_{region_id}.png")
        if os.path.exists(p):
            try:
                with Image.open(p) as im:
                    sizes.append(im.size)  # (w, h)
                    available_regions.append(region_id)
            except Exception:
                pass

    if not sizes:
        print("❌ Region images not found in base_path:", base_path)
        return

    # Determine the maximum width and height for the canvas
    max_w = max(w for (w, h) in sizes)
    max_h = max(h for (w, h) in sizes)

    # Global canvas dimensions
    global_width, global_height = max_w, max_h 
    canvas = Image.new('RGBA', (global_width, global_height), (0, 0, 0, 255))

    print(f" Canvas initialized: {global_width}x{global_height}")
    print(" Creating gift-worthy mathematical face...")

    # INITIALIZE SYMBOL LOG
    symbol_log = []
    total_symbols = 0

    # ---------------- Render ----------------
    for region_id in available_regions: # Iterate over regions that actually exist
        region_path = os.path.join(base_path, f"region_{region_id}.png")
        print(f"Processing region {region_id}...")

        img_pil = Image.open(region_path).convert("RGB")
        
        # Get the specific dimensions for the current region's image
        region_width, region_height = img_pil.size 

        img = np.array(img_pil)
        gray = img.mean(axis=2).astype(np.uint8)
        mask = (gray > 10).astype(np.uint8) # Mask will have region_height, region_width

        base_font, step = region_style_map.get(region_id, (9, 6))
        region_importance = region_importance_map.get(region_id, 1.0)
        symbols = region_symbols_map.get(region_id, ['·']) # Added a fallback symbol

        symbols_placed_in_region = 0 

        # Iterate using the current region's dimensions (region_height, region_width)
        for y in range(0, region_height, step):
            for x in range(0, region_width, step):
                # Ensure x and y are within the mask's bounds before accessing.
                if not (0 <= y < region_height and 0 <= x < region_width):
                    continue
                
                if mask[y, x] != 1:
                    continue

                raw_b = int(img[y, x].mean())
                b = safe_gamma(raw_b)
                
                sym = random.choice(symbols)
                final_size = size_mapping(base_font, b, region_importance)
                font = load_font(final_size)
                
                angle = random.randint(-rot_range_deg, rot_range_deg)
                bbox = font.getbbox(sym)
                wtxt, htxt = bbox[2] - bbox[0], bbox[3] - bbox[1]

                if wtxt <= 0 or htxt <= 0:
                    continue

                txt = Image.new("RGBA", (wtxt, htxt), (0, 0, 0, 0))
                d = ImageDraw.Draw(txt)
                
                alpha_val = region_opacity_map.get(region_id, 255)
                color = (b, b, b, alpha_val)
                
                d.text((-bbox[0], -bbox[1]), sym, font=font, fill=color)
                txt = txt.rotate(angle, expand=1)
                wx, hy = txt.size # Size of rotated text image

                jitter_x = random.randint(-jitter_cap_px, jitter_cap_px)
                jitter_y = random.randint(-jitter_cap_px, jitter_cap_px)
                
                # Proposed center for the symbol
                ox, oy = x + jitter_x, y + jitter_y

                placed = False
                final_draw_x, final_draw_y = 0, 0 # Coords where symbol is actually drawn

                # YOUR PROVIDED LOGIC FOR PLACEMENT:
                # Attempt to place with jitter, checking against global canvas bounds AND region mask
                if (ox - wx//2 >= 0 and oy - hy//2 >= 0 and
                    ox + wx//2 < global_width and oy + hy//2 < global_height):
                    
                    # Ensure the central point (ox,oy) for mask check is within the *current region's* bounds
                    if (0 <= oy < region_height and 0 <= ox < region_width and mask[oy, ox] == 1):
                        canvas.alpha_composite(txt, (ox - wx//2, oy - hy//2))
                        symbols_placed_in_region += 1
                        placed = True
                        final_draw_x, final_draw_y = ox - wx//2, oy - hy//2
                
                # Fallback: try center of cell (x,y) if jittered pos failed, checking against global canvas bounds AND region mask
                if not placed and (0 <= y < region_height and 0 <= x < region_width and mask[y, x] == 1):
                    # Check if the symbol's full bounding box fits within the GLOBAL canvas
                    if (x - wx//2 >= 0 and y - hy//2 >= 0 and
                        x + wx//2 < global_width and y + hy//2 < global_height):
                        
                        canvas.alpha_composite(txt, (x - wx//2, y - hy//2))
                        symbols_placed_in_region += 1
                        placed = True
                        final_draw_x, final_draw_y = x - wx//2, y - hy//2

                # CRITICAL: LOG EVERY SYMBOL PLACEMENT DETAIL IF IT WAS PLACED
                if placed:
                    total_symbols += 1
                    symbol_info = {
                        "symbol": sym,
                        "font_size": final_size,
                        "position_center_of_text": [final_draw_x + wx//2, final_draw_y + hy//2], 
                        "position_top_left_of_text": [final_draw_x, final_draw_y], 
                        "rotation": angle,
                        "color": color,
                        "region_id": region_id,
                        "order": total_symbols,
                        "text_drawn_size": [wx, hy],  
                        "brightness": b,
                        "alpha": alpha_val,
                        "timestamp": total_symbols 
                    }
                    symbol_log.append(symbol_info)

        print(f"Region {region_id}: {symbols_placed_in_region} symbols placed")

    # Save the final image
    output_path = os.path.join(base_path, "gift_worthy_mathematical_face.png")
    canvas.save(output_path)

    # SAVE THE SYMBOL PLACEMENT LOG - ANIMATION GOLD!
    log_path = os.path.join(base_path, "symbol_placements.json")
    with open(log_path, "w") as f:
        json.dump(symbol_log, f, indent=2)

    print(f"\n🎁 Gift-worthy mathematical face completed!")
    print(f"📁 Saved to: {output_path}")
    print(f"📁 Symbol placement details saved to: {log_path}")
    print(f"🎯 Total symbols logged for animation: {len(symbol_log)}")

if __name__ == "__main__":
    # Ensure the logger is set up if needed by the BiSeNet model
    # setup_logger takes an argument for log directory, adjust if needed
    # For a quick run, you might comment this out if it's causing issues
    # setup_logger('./res/log') 

    # Run script 1 - Use relative path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Accept image path from command line, default to test_img if not provided
    if len(sys.argv) > 1:
        test_img_path = sys.argv[1]
    else:
        test_img_path = os.path.join(project_root, "test_img")
    
    evaluate(
        dspth=test_img_path,
        cp='79999_iter.pth'
    )

    # Run script 2
    extract_regions()

    # Run script 3
    create_math_face()