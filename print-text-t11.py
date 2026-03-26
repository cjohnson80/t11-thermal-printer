import sys
import subprocess
import os
import argparse
import time

USB_DEVICE = '/dev/usb/lp0'
WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8
LINES_PER_BLOCK = 24

def print_text_file(text_path, threshold=128):
    print(f"Rendering text file {text_path} for 8.5x11...")
    raw_gray = "text.gray"
    
    # Use magick to:
    # 1. Read text file with specific font and sizing
    # 2. Use 'caption:' or 'label:' for automatic wrapping
    # 3. Format as 8.5x11 equivalent (approx 2550x3300 at 300dpi)
    # Actually, let's just render the text normally and resize to width.
    cmd = [
        "magick", 
        "-background", "white", 
        "-fill", "black", 
        "-font", "Adwaita-Mono", 
        "-pointsize", "12", 
        "-size", f"{WIDTH_PX}x", # Constrain width
        f"caption:@{text_path}", 
        "-colorspace", "gray", 
        "-depth", "8", 
        f"GRAY:{raw_gray}"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    with open(raw_gray, "rb") as f:
        gray_data = f.read()
    
    height = len(gray_data) // WIDTH_PX
    print(f"Text Rendered: {WIDTH_PX}x{height} pixels. Packing bits...")

    bit_data = bytearray()
    for y in range(height):
        for x_byte in range(BYTES_PER_LINE):
            byte_val = 0
            for bit in range(8):
                pixel_idx = (y * WIDTH_PX) + (x_byte * 8) + bit
                if pixel_idx < len(gray_data) and gray_data[pixel_idx] < threshold:
                    byte_val |= (1 << (7 - bit))
            bit_data.append(byte_val)

    try:
        with open(USB_DEVICE, 'wb') as f:
            f.write(b'\x1b@') # Init
            
            # 1. Top padding (50 lines of white)
            f.write(b'\x1bd\x32')
            
            print(f"Printing {height} lines...")
            for y_start in range(0, height, LINES_PER_BLOCK):
                y_end = min(y_start + LINES_PER_BLOCK, height)
                num_lines = y_end - y_start
                start_idx = y_start * BYTES_PER_LINE
                end_idx = y_end * BYTES_PER_LINE
                block_data = bit_data[start_idx:end_idx]
                header = bytes([0x1d, 0x76, 0x30, 0, BYTES_PER_LINE % 256, BYTES_PER_LINE // 256, num_lines % 256, num_lines // 256])
                f.write(header + block_data)
                f.flush()
                time.sleep(0.1)
                if y_start % 480 == 0:
                    print(f"Progress: {y_start}/{height} lines...")
            
            # 2. Bottom padding (100 lines of white / ~0.5 inch)
            f.write(b'\x1bd\x64') 
            f.flush()
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(raw_gray):
            os.remove(raw_gray)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Text to T11')
    parser.add_argument('text_file')
    parser.add_argument('--threshold', type=int, default=128)
    args = parser.parse_args()
    print_text_file(args.text_file, args.threshold)
