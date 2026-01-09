import argparse
import cv2
import glob
import os
from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.download_util import load_file_from_url

from realesrgan import RealESRGANer
from realesrgan.archs.srvgg_arch import SRVGGNetCompact

# Import configuration system
try:
    from upscaler_config import upscaler_config
    USE_CONFIG = True
except ImportError:
    USE_CONFIG = False
    print("DEBUG: Warning: upscaler_config not found, using default paths")


def main():
    """Inference demo for Real-ESRGAN.
    """
    print("\n--- DEBUG START: Script Execution ---")
    # Get default paths from config if available
    if USE_CONFIG:
        defaults = upscaler_config.get_inference_defaults()
        upscaler_config.ensure_directories_exist()
        default_input = defaults['input']
        default_output = defaults['output']
    else:
        default_input = './inputs'
        default_output = './results'
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, default=default_input, help='Input image or folder')
    parser.add_argument(
        '-n',
        '--model_name',
        type=str,
        default='RealESRGAN_x4plus',
        help=('Model names: RealESRGAN_x4plus | RealESRNet_x4plus | RealESRGAN_x4plus_anime_6B | RealESRGAN_x2plus | '
              'realesr-animevideov3 | realesr-general-x4v3'))
    parser.add_argument('-o', '--output', type=str, default=default_output, help='Output folder')
    parser.add_argument(
        '-dn',
        '--denoise_strength',
        type=float,
        default=0.5,
        help=('Denoise strength. 0 for weak denoise (keep noise), 1 for strong denoise ability. '
              'Only used for the realesr-general-x4v3 model'))
    parser.add_argument('-s', '--outscale', type=float, default=4, help='The final upsampling scale of the image')
    parser.add_argument(
        '--model_path', type=str, default=None, help='[Option] Model path. Usually, you do not need to specify it')
    parser.add_argument('--suffix', type=str, default='out', help='Suffix of the restored image')
    parser.add_argument('-t', '--tile', type=int, default=0, help='Tile size, 0 for no tile during testing')
    parser.add_argument('--tile_pad', type=int, default=10, help='Tile padding')
    parser.add_argument('--pre_pad', type=int, default=0, help='Pre padding size at each border')
    parser.add_argument('--face_enhance', action='store_true', help='Use GFPGAN to enhance face')
    parser.add_argument(
        '--fp32', action='store_true', help='Use fp32 precision during inference. Default: fp16 (half precision).')
    parser.add_argument(
        '--alpha_upsampler',
        type=str,
        default='realesrgan',
        help='The upsampler for the alpha channels. Options: realesrgan | bicubic')
    parser.add_argument(
        '--ext',
        type=str,
        default='auto',
        help='Image extension. Options: auto | jpg | png, auto means using the same extension as inputs')
    parser.add_argument(
        '-g', '--gpu-id', type=int, default=None, help='gpu device to use (default=None) can be 0,1,2 for multi-gpu')

    args = parser.parse_args()
    print(f"DEBUG: Parsed Arguments: input={args.input}, model={args.model_name}, fp32={args.fp32}")


    # determine models according to model names
    args.model_name = args.model_name.split('.')[0]
    # ... (Model determination code remains the same) ...
    if args.model_name == 'RealESRGAN_x4plus':  # x4 RRDBNet model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        netscale = 4
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth']
    elif args.model_name == 'RealESRNet_x4plus':  # x4 RRDBNet model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        netscale = 4
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRNet_x4plus.pth']
    elif args.model_name == 'RealESRGAN_x4plus_anime_6B':  # x4 RRDBNet model with 6 blocks
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
        netscale = 4
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth']
    elif args.model_name == 'RealESRGAN_x2plus':  # x2 RRDBNet model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
        netscale = 2
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth']
    elif args.model_name == 'realesr-animevideov3':  # x4 VGG-style model (XS size)
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4, act_type='prelu')
        netscale = 4
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth']
    elif args.model_name == 'realesr-general-x4v3':  # x4 VGG-style model (S size)
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type='prelu')
        netscale = 4
        file_url = [
            'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth',
            'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth'
        ]


    # determine model paths
    if args.model_path is not None:
        model_path = args.model_path
    else:
        if USE_CONFIG:
            model_path = str(upscaler_config.get_model_path(args.model_name))
            weights_dir = str(upscaler_config.weights_dir)
        else:
            model_path = os.path.join('./weights', args.model_name + '.pth')
            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
            weights_dir = os.path.join(ROOT_DIR, 'weights')
            
        print(f"DEBUG: Expected model path check: {model_path}")
        if not os.path.isfile(model_path):
            print(f"DEBUG: Model path NOT found: {model_path}. Attempting download...")
            for url in file_url:
                # model_path will be updated
                model_path = load_file_from_url(
                    url=url, model_dir=weights_dir, progress=True, file_name=None)
            print(f"DEBUG: Model path after download/check: {model_path}")
        else:
            print(f"DEBUG: Model path found: {model_path}")

    # use dni to control the denoise strength
    dni_weight = None
    if args.model_name == 'realesr-general-x4v3' and args.denoise_strength != 1:
        wdn_model_path = model_path.replace('realesr-general-x4v3', 'realesr-general-wdn-x4v3')
        model_path = [model_path, wdn_model_path]
        dni_weight = [args.denoise_strength, 1 - args.denoise_strength]

    # restorer
    print("DEBUG: Initializing RealESRGANer (This is where VRAM/Model load issues often happen)...")
    upsampler = RealESRGANer(
        scale=netscale,
        model_path=model_path,
        dni_weight=dni_weight,
        model=model,
        tile=args.tile,
        tile_pad=args.tile_pad,
        pre_pad=args.pre_pad,
        half=not args.fp32,
        gpu_id=args.gpu_id)
    print("DEBUG: RealESRGANer initialized successfully.")

    if args.face_enhance:  # Use GFPGAN for face enhancement
        print("DEBUG: Initializing GFPGANer...")
        from gfpgan import GFPGANer
        face_enhancer = GFPGANer(
            model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth',
            upscale=args.outscale,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=upsampler)
        print("DEBUG: GFPGANer initialized successfully.")
        
    os.makedirs(args.output, exist_ok=True)
    print(f"DEBUG: Output directory check/creation: {args.output}")

    if os.path.isfile(args.input):
        paths = [args.input]
        print(f"DEBUG: Input is a single file. Path: {args.input}")
    else:
        paths = sorted(glob.glob(os.path.join(args.input, '*')))
        print(f"DEBUG: Input is a folder. Glob pattern: {os.path.join(args.input, '*')}")
        
    print(f"DEBUG: Found {len(paths)} file(s) to process.")
    
    if not paths:
        print("\n!!! ERROR: ZERO files found. Script terminating. Check input path/directory. !!!")
        return # Exit gracefully if no files found
    
    # --- Start of the main processing loop ---
    for idx, path in enumerate(paths):
        imgname, extension = os.path.splitext(os.path.basename(path))
        print(f'\n--- Processing Start: File {idx+1} of {len(paths)}: "{imgname}" ---')
        print('Testing', idx, imgname) # Original print statement

        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"!!! ERROR: cv2.imread failed to load image: {path} !!!")
            continue
            
        print(f"DEBUG: Image loaded. Shape: {img.shape}")
        if len(img.shape) == 3 and img.shape[2] == 4:
            img_mode = 'RGBA'
        else:
            img_mode = None

        try:
            print("DEBUG: Starting enhancement...")
            if args.face_enhance:
                # ... (face enhancement code) ...
                _, _, output = face_enhancer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
            else:
                output, _ = upsampler.enhance(img, outscale=args.outscale)
            print("DEBUG: Enhancement complete.")
        except RuntimeError as error:
            print('\n!!! CRITICAL ERROR: RuntimeError during enhancement !!!')
            print('Error', error)
            print('If you encounter CUDA out of memory, try to set --tile with a smaller number.')
            print('!!! CRITICAL ERROR: End !!!\n')
        else:
            if args.ext == 'auto':
                extension = extension[1:]
            else:
                extension = args.ext
            if img_mode == 'RGBA':  # RGBA images should be saved in png format
                extension = 'png'
            if args.suffix == '':
                save_path = os.path.join(args.output, f'{imgname}.{extension}')
            else:
                save_path = os.path.join(args.output, f'{imgname}_{args.suffix}.{extension}')
            
            print(f"DEBUG: Saving output to: {save_path}")
            cv2.imwrite(save_path, output)
            print(f"--- Processing Complete: File {idx+1} Saved ---")


if __name__ == '__main__':
    main()