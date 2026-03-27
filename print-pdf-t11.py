import sys
import subprocess
import os
import argparse
import time

USB_DEVICE = '/dev/usb/lp0'
WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8
LINES_PER_BLOCK = 8 # Even smaller blocks for maximum safety

def print_pdf_page(pdf_path, page_num=0, threshold=128):
    print(f"Converting PDF {pdf_path} [Page {page_num}]...")
    raw_gray = "page.gray"
    
    # 1. Standard Render
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
    print(f"Packing {WIDTH_PX}x{height} pixels into bits...")
    
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
            print(f"Printing {height} lines in safe-mode (Blocks of {LINES_PER_BLOCK}, 0.2s delay)...")
            
            for y_start in range(0, height, LINES_PER_BLOCK):
                y_end = min(y_start + LINES_PER_BLOCK, height)
                num_lines = y_end - y_start
                
                start_idx = y_start * BYTES_PER_LINE
                end_idx = y_end * BYTES_PER_LINE
                block_data = bit_data[start_idx:end_idx]
                
                header = bytes([0x1d, 0x76, 0x30, 0, BYTES_PER_LINE % 256, BYTES_PER_LINE // 256, num_lines % 256, num_lines // 256])
                
                f.write(header + block_data)
                f.flush()
                
                # 0.2s delay - extremely conservative to prevent hardware hang
                time.sleep(0.2) 
                
                if y_start % 240 == 0:
                    print(f"Progress: {y_start}/{height} lines...")
            
            f.write(b'\x1bd\x05')
            f.flush()
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(raw_gray):
            os.remove(raw_gray)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PDF to T11 (Max Stability)')
    parser.add_argument('pdf')
    parser.add_argument('--page', type=int, default=0)
    parser.add_argument('--threshold', type=int, default=128)
    args = parser.parse_args()
    print_pdf_page(args.pdf, args.page, args.threshold)
