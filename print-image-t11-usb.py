import sys
import subprocess
import os
import argparse
import time

# USB Device
USB_DEVICE = '/dev/usb/lp0'

# US Letter Thermal Printer Specs (8.5 inches)
WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8
LINES_PER_BLOCK = 8

def convert_and_print(image_path, threshold=50, mirror=False):
    print(f"Processing image for 8.5x11 USB: {image_path}")
    mono_output = "image.mono"
    
    cmd = [
        "magick", 
        "-background", "white", 
        image_path, 
        "-alpha", "remove", 
        "-flatten", 
        "-resize", f"{WIDTH_PX}x", 
        "-colorspace", "gray", "-threshold", f"{threshold}%", 
        "-depth", "1", 
        f"MONO:{mono_output}"
    ]
    
    if mirror:
        cmd.insert(-1, "-flop")
        
    print("Rendering...")
    start_time = time.time()
    subprocess.run(cmd, check=True)
    
    with open(mono_output, "rb") as f:
        bit_data = f.read()
    
    height = len(bit_data) // BYTES_PER_LINE
    print(f"Rendered in {time.time() - start_time:.2f}s. Image: {WIDTH_PX}x{height}")

    try:
        with open(USB_DEVICE, 'wb') as f:
            f.write(b'\x1b@') # Init
            print(f"Printing {height} lines in safe-mode...")
            
            for y_start in range(0, height, LINES_PER_BLOCK):
                y_end = min(y_start + LINES_PER_BLOCK, height)
                num_lines = y_end - y_start
                start_idx = y_start * BYTES_PER_LINE
                end_idx = y_end * BYTES_PER_LINE
                block_data = bit_data[start_idx:end_idx]
                
                header = bytes([0x1d, 0x76, 0x30, 0, BYTES_PER_LINE % 256, BYTES_PER_LINE // 256, num_lines % 256, num_lines // 256])
                
                f.write(header + block_data)
                f.flush()
                time.sleep(0.2) 
                
                if y_start % 480 == 0:
                    print(f"Progress: {y_start}/{height} lines...")
            
            f.write(b'\x1bd\x05') 
            f.flush()
        print("\nSuccess! Image printed successfully via USB.")
    except Exception as e:
        print(f"\nUSB Error: {e}")
    finally:
        if os.path.exists(mono_output):
            os.remove(mono_output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Print 8.5x11 image to T11 (Optimized Startup)')
    parser.add_argument('image', help='Path to image')
    parser.add_argument('--threshold', type=int, default=50, help='Darkness threshold (1-99, default 50)')
    parser.add_argument('--mirror', action='store_true', help='Mirror image')
    args = parser.parse_args()
    convert_and_print(args.image, args.threshold, args.mirror)
