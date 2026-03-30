import socket
import sys
import subprocess
import os
import argparse
import time

# Printer configuration
PRINTER_ADDR = '41:42:86:99:6F:BA'
RFCOMM_CHANNEL = 2

# US Letter Thermal Printer Specs (8.5 inches)
WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8
LINES_PER_BLOCK = 24

def print_pdf_gold(pdf_path, page_num=0, threshold=180):
    print(f"Connecting to {PRINTER_ADDR}...")
    try:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.connect((PRINTER_ADDR, RFCOMM_CHANNEL))
        print("Connected!")
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    print(f"Rendering PDF {pdf_path}...")
    raw_gray = "gold.gray"
    
    # 1. Render to raw 8-bit grayscale (Solid reliability)
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
    print(f"Packing {WIDTH_PX}x{height} pixels (Manual MSB Mode)...")

    # 2. Manual Packing (This is the secret to non-garbled text)
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
        # Clear printer buffer
        sock.send(b'\x00' * 10)
        sock.send(b'\x1b@') # Init
        
        # SWITCH TO CONTINUOUS MODE (Disable Black Mark / Page sensing)
        # Standard command for many Chinese A4 printers to use continuous roll
        print("Setting printer to Continuous Mode...")
        sock.send(b'\x1f\x1b\x1f\xa1\x00') 
        time.sleep(0.5)
        
        print(f"Printing {height} lines...")
        for y_start in range(0, height, LINES_PER_BLOCK):
            y_end = min(y_start + LINES_PER_BLOCK, height)
            num_lines = y_end - y_start
            
            start_idx = y_start * BYTES_PER_LINE
            end_idx = y_end * BYTES_PER_LINE
            block_data = bit_data[start_idx:end_idx]
            
            # GS v 0 Header
            header = bytes([0x1d, 0x76, 0x30, 0, BYTES_PER_LINE % 256, BYTES_PER_LINE // 256, num_lines % 256, num_lines // 256])
            
            sock.sendall(header + block_data)
            time.sleep(0.2) # High stability delay
            
            if y_start % 240 == 0:
                print(f"Progress: {y_start}/{height} lines...")
        
        # CLEAN EXIT SEQUENCE
        print("Finishing job and feeding paper...")
        sock.send(b'\x1bd\x00') # No feed - fix overshoot
        time.sleep(2.0)         # WAIT for the physical motor to finish
        sock.send(b'\x1b@')     # Reset printer state for the next job
        time.sleep(0.5)         # Let the reset settle
        
        sock.close()
        print("Success! Printer ready for next page.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(raw_gray):
            os.remove(raw_gray)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='T11 Gold Standard BT Driver')
    parser.add_argument('pdf')
    parser.add_argument('--page', type=int, default=0)
    parser.add_argument('--threshold', type=int, default=180)
    args = parser.parse_args()
    print_pdf_gold(args.pdf, args.page, args.threshold)
