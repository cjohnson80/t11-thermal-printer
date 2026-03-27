import socket
import sys
import subprocess
import os
import argparse
import time

# Printer configuration
PRINTER_ADDR = '41:42:86:99:6F:BA'
RFCOMM_CHANNEL = 2

# US Letter Thermal Printer Specs (8.5 inches) - Confirmed correct width
WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8
LINES_PER_BLOCK = 24

def print_pdf_bt(pdf_path, page_num=0, threshold=50):
    print(f"Connecting to {PRINTER_ADDR} via Bluetooth...")
    try:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.connect((PRINTER_ADDR, RFCOMM_CHANNEL))
        print("Connected!")
    except Exception as e:
        print(f"Bluetooth Connection Error: {e}")
        return

    print(f"Converting PDF {pdf_path} [Page {page_num}]...")
    mono_output = "page.mono"
    
    cmd = [
        "magick", "-density", "300", 
        "-background", "white", f"{pdf_path}[{page_num}]", 
        "-alpha", "remove", "-flatten", 
        "-resize", f"{WIDTH_PX}x", 
        "-colorspace", "gray", "-threshold", f"{threshold}%", 
        "-depth", "1", f"MONO:{mono_output}"
    ]
    subprocess.run(cmd, check=True)
    
    with open(mono_output, "rb") as f:
        bit_data = f.read()
    
    height = len(bit_data) // BYTES_PER_LINE
    print(f"Image ready: {WIDTH_PX}x{height}")

    try:
        sock.send(b'\x1b@') # Init
        print(f"Printing {height} lines (Slow Packet Mode)...")
        
        for y_start in range(0, height, LINES_PER_BLOCK):
            y_end = min(y_start + LINES_PER_BLOCK, height)
            num_lines = y_end - y_start
            
            start_idx = y_start * BYTES_PER_LINE
            end_idx = y_end * BYTES_PER_LINE
            block_data = bit_data[start_idx:end_idx]
            
            header = bytes([0x1d, 0x76, 0x30, 0, BYTES_PER_LINE % 256, BYTES_PER_LINE // 256, num_lines % 256, num_lines // 256])
            
            full_block = header + block_data
            
            # CRITICAL FIX: Send in tiny 64-byte packets to prevent BT buffer overflow
            packet_size = 64
            for i in range(0, len(full_block), packet_size):
                sock.send(full_block[i:i+packet_size])
                time.sleep(0.005) # 5ms delay between packets
            
            # Delay between 24-line blocks
            time.sleep(0.2) 
            
            if y_start % 240 == 0:
                print(f"Progress: {y_start}/{height} lines...")
        
        sock.send(b'\x1bd\x0a') # Feed
        sock.close()
        print("Done!")
    except Exception as e:
        print(f"Bluetooth Error: {e}")
    finally:
        if os.path.exists(mono_output):
            os.remove(mono_output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PDF to T11 via Bluetooth (Safe Packets)')
    parser.add_argument('pdf')
    parser.add_argument('--page', type=int, default=0)
    parser.add_argument('--threshold', type=int, default=50)
    args = parser.parse_args()
    print_pdf_bt(args.pdf, args.page, args.threshold)
