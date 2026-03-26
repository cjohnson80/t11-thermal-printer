import sys
import subprocess
import os
import argparse
import time

USB_DEVICE = '/dev/usb/lp0'
# ESC * 33 (24-dot double density) expects 3 bytes (24 bits) per vertical line
# This means we send image in horizontal strips of 24 pixels high
WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8

def print_pdf_page(pdf_path, page_num=0, threshold=128):
    print(f"Converting PDF {pdf_path} (ESC * mode)...")
    raw_gray = "page.gray"
    
    cmd = [
        "magick", "-density", "300", 
        "-background", "white", f"{pdf_path}[{page_num}]", 
        "-alpha", "remove", "-flatten", 
        "-resize", f"{WIDTH_PX}x", 
        "-colorspace", "gray", "-depth", "8", f"GRAY:{raw_gray}"
    ]
    subprocess.run(cmd, check=True)
    
    with open(raw_gray, "rb") as f:
        gray_data = f.read()
    
    height = len(gray_data) // WIDTH_PX
    print(f"Packing {WIDTH_PX}x{height} pixels for ESC *...")

    try:
        with open(USB_DEVICE, 'wb') as f:
            f.write(b'\x1b@') # Init
            
            # ESC * m nL nH d1...dk
            # m=33 (24-dot double density)
            # nL, nH = WIDTH_PX
            nL = WIDTH_PX % 256
            nH = WIDTH_PX // 256
            
            # Loop through 24-pixel high strips
            for y_strip in range(0, height, 24):
                # Header for a 24-dot high strip
                f.write(bytes([0x1b, 0x2a, 33, nL, nH]))
                
                # Each 'column' in the strip is 3 bytes (24 vertical pixels)
                for x in range(WIDTH_PX):
                    col_data = 0
                    for bit in range(24):
                        y = y_strip + bit
                        if y < height:
                            pixel_idx = (y * WIDTH_PX) + x
                            if gray_data[pixel_idx] < threshold:
                                # Pack into 3 bytes (MSB of first byte is top pixel)
                                col_data |= (1 << (23 - bit))
                    
                    # Write the 3 bytes for this column
                    f.write(bytes([(col_data >> 16) & 0xFF, (col_data >> 8) & 0xFF, col_data & 0xFF]))
                
                f.write(b'\x0a') # Line feed after strip
                f.flush()
                time.sleep(0.2) # Long delay between strips for safety
                
                if y_strip % 240 == 0:
                    print(f"Progress: {y_strip}/{height} lines...")
            
            f.write(b'\x1bd\x0a')
            f.flush()
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(raw_gray):
            os.remove(raw_gray)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PDF to T11 (ESC * Mode)')
    parser.add_argument('pdf')
    parser.add_argument('--page', type=int, default=0)
    parser.add_argument('--threshold', type=int, default=128)
    args = parser.parse_args()
    print_pdf_page(args.pdf, args.page, args.threshold)
