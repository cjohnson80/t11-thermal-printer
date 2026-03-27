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
LINES_PER_BLOCK = 8 # Ultra-safe small blocks

def convert_and_print(image_path, threshold=128, mirror=False):
    print(f"Processing image for 8.5x11 USB: {image_path}")
    raw_gray = "image.gray"
    
    cmd = [
        "magick", 
        "-background", "white", 
        image_path, 
        "-alpha", "remove", 
        "-flatten", 
        "-resize", f"{WIDTH_PX}x", 
        "-colorspace", "gray", 
        "-depth", "8", 
        f"GRAY:{raw_gray}"
    ]
    
    if mirror:
        cmd.insert(-1, "-flop")
        
    subprocess.run(cmd, check=True)
    
    with open(raw_gray, "rb") as f:
        gray_data = f.read()
    
    height = len(gray_data) // WIDTH_PX
    print(f"Image Ready: {WIDTH_PX}x{height} pixels. Packing bits...")

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
                time.sleep(0.2) # High delay for stability
                
                if y_start % 480 == 0:
                    print(f"Progress: {y_start}/{height} lines...")
            
            f.write(b'\x1bd\x05') 
            f.flush()
        print("\nSuccess! Image printed successfully via USB.")
    except Exception as e:
        print(f"\nUSB Error: {e}")
    finally:
        if os.path.exists(raw_gray):
            os.remove(raw_gray)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Print 8.5x11 image to T11 (Safe Mode)')
    parser.add_argument('image', help='Path to image')
    parser.add_argument('--threshold', type=int, default=128, help='B/W threshold (0-255)')
    parser.add_argument('--mirror', action='store_true', help='Mirror image')
    args = parser.parse_args()
    convert_and_print(args.image, args.threshold, args.mirror)
