#!/usr/bin/env python3
import usb.core
import usb.util
import socket
import sys
import os
import argparse
import subprocess
import time

# Printer configuration
DEFAULT_BT_ADDR = '41:42:86:99:6F:BA'
RFCOMM_CHANNEL = 2
VENDOR_ID = 0x0483
PRODUCT_ID = 0x5720

# Hardware Specs (8.5 inches / US Letter / A4 at 203 DPI)
WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8
LINES_PER_BLOCK = 24

def find_usb_printer():
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        return None
    
    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)
    usb.util.claim_interface(dev, 0)
    return dev

def connect_bt_printer(addr):
    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    sock.settimeout(10)
    sock.connect((addr, RFCOMM_CHANNEL))
    return sock

def init_printer(conn, is_usb=True):
    init_cmds = b'\x1b@' + b'\x1f\x1b\x1f\xa1\x00' # Reset + Continuous Mode
    if is_usb:
        conn.write(0x01, init_cmds)
    else:
        conn.sendall(init_cmds)
    time.sleep(0.5)

def send_block(conn, data, is_usb=True):
    if is_usb:
        conn.write(0x01, data)
        time.sleep(0.2) # High stability delay
    else:
        # CRITICAL FIX: Send in 64-byte packets for Bluetooth stability
        packet_size = 64
        for i in range(0, len(data), packet_size):
            conn.send(data[i:i+packet_size])
            time.sleep(0.005) # 5ms delay
        time.sleep(0.2)

def process_file(file_path, threshold=128, mirror=False, page=0):
    ext = os.path.splitext(file_path)[1].lower()
    raw_gray = "/tmp/t11_print.raw"
    
    if ext in ['.pdf']:
        cmd = ["magick", "-density", "300", "-background", "white", f"{file_path}[{page}]", "-alpha", "remove", "-flatten", "-resize", f"{WIDTH_PX}x", "-colorspace", "gray", "-depth", "8", f"GRAY:{raw_gray}"]
    elif ext in ['.txt', '.text']:
        thresh_pct = int((threshold / 255.0) * 100)
        cmd = ["magick", "-background", "white", "-fill", "black", "-font", "DejaVu-Sans-Mono", "-pointsize", "12", "-size", f"{WIDTH_PX}x", f"caption:@{file_path}", "-colorspace", "gray", "-threshold", f"{thresh_pct}%", "-depth", "8", f"GRAY:{raw_gray}"]
    else: # Images
        cmd = ["magick", "-background", "white", file_path, "-alpha", "remove", "-flatten", "-resize", f"{WIDTH_PX}x"]
        if mirror: cmd.insert(-1, "-flop")
        cmd += ["-colorspace", "gray", "-depth", "8", f"GRAY:{raw_gray}"]

    print(f"Rendering {file_path}...")
    subprocess.run(cmd, check=True)
    
    with open(raw_gray, "rb") as f:
        gray_data = f.read()
    
    height = len(gray_data) // WIDTH_PX
    bit_data = bytearray()
    for y in range(height):
        for x_byte in range(BYTES_PER_LINE):
            byte_val = 0
            for bit in range(8):
                pixel_idx = (y * WIDTH_PX) + (x_byte * 8) + bit
                if pixel_idx < len(gray_data) and gray_data[pixel_idx] < threshold:
                    byte_val |= (1 << (7 - bit))
            bit_data.append(byte_val)
    
    if os.path.exists(raw_gray): os.remove(raw_gray)
    return bit_data, height

def main():
    parser = argparse.ArgumentParser(description="Unified T11 Thermal Printer Driver")
    parser.add_argument("file", help="File to print (PDF, Image, Text)")
    parser.add_argument("--mode", choices=['usb', 'bt'], default='usb', help="Connection mode")
    parser.add_argument("--bt-addr", default=DEFAULT_BT_ADDR, help="Bluetooth MAC address")
    parser.add_argument("--threshold", type=int, default=128, help="Threshold 0-255 (Lower = Darker)")
    parser.add_argument("--mirror", action="store_true", help="Mirror image (for tattoos)")
    parser.add_argument("--page", type=int, default=0, help="PDF page number")
    args = parser.parse_args()

    try:
        bit_data, height = process_file(args.file, args.threshold, args.mirror, args.page)
        
        conn = None
        is_usb = (args.mode == 'usb')
        
        if is_usb:
            print("Connecting via USB...")
            conn = find_usb_printer()
            if not conn: print("Error: USB Printer not found."); return
        else:
            print(f"Connecting to {args.bt_addr} via Bluetooth...")
            conn = connect_bt_printer(args.bt_addr)
            print("Connected!")

        init_printer(conn, is_usb)
        
        print(f"Printing {height} lines...")
        for y_start in range(0, height, LINES_PER_BLOCK):
            y_end = min(y_start + LINES_PER_BLOCK, height)
            num_lines = y_end - y_start
            header = bytes([0x1d, 0x76, 0x30, 0, BYTES_PER_LINE % 256, BYTES_PER_LINE // 256, num_lines % 256, num_lines // 256])
            send_block(conn, header + bit_data[y_start * BYTES_PER_LINE : y_end * BYTES_PER_LINE], is_usb)
            if y_start % 240 == 0: print(f"Progress: {y_start}/{height}")

        # Finish without overshoot
        end_cmds = b'\x1bd\x00'
        if is_usb:
            conn.write(0x01, end_cmds)
            time.sleep(1.0)
            usb.util.release_interface(conn, 0)
        else:
            conn.sendall(end_cmds)
            time.sleep(1.0)
            conn.close()
            
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
