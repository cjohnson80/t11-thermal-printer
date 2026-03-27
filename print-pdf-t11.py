import sys
import subprocess
import os
import argparse
import time

USB_DEVICE = '/dev/usb/lp0'
WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8
LINES_PER_BLOCK = 8

def print_pdf_page(pdf_path, page_num=0, threshold=50):
    print(f"Converting PDF {pdf_path} [Page {page_num}]...")
    mono_output = "page.mono"
    
    # Let Magick do the heavy lifting (much faster than Python loops)
    # -threshold X% handles the darkness
    # -depth 1 MONO: outputs exactly the bitmask the printer wants
    cmd = [
        "magick", "-density", "300", 
        "-background", "white", f"{pdf_path}[{page_num}]", 
        "-alpha", "remove", "-flatten", 
        "-resize", f"{WIDTH_PX}x", 
        "-colorspace", "gray", "-threshold", f"{threshold}%", 
        "-depth", "1", f"MONO:{mono_output}"
    ]
    
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
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(mono_output):
            os.remove(mono_output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PDF to T11 (Optimized Startup)')
    parser.add_argument('pdf')
    parser.add_argument('--page', type=int, default=0)
    parser.add_argument('--threshold', type=int, default=50, help='Darkness threshold (1-99, default 50)')
    args = parser.parse_args()
    print_pdf_page(args.pdf, args.page, args.threshold)
