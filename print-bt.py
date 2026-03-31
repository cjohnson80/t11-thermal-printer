#!/usr/bin/env python3
import socket
import subprocess
import os
import argparse
import time

PRINTER_ADDR = "41:42:86:99:6F:BA"
RFCOMM_CHANNEL = 2
WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8
LINES_PER_BLOCK = 24


def connect_printer():
    """Connect to T11 via Bluetooth RFCOMM"""
    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    sock.settimeout(10)
    sock.connect((PRINTER_ADDR, RFCOMM_CHANNEL))
    return sock


def print_image_bt(image_path, threshold=128, mirror=False):
    print(f"Connecting to {PRINTER_ADDR} via Bluetooth...")
    try:
        sock = connect_printer()
        print("Connected!")
    except Exception as e:
        print(f"Connection Failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure T11 is paired: bluetoothctl pair 41:42:86:99:6F:BA")
        print("2. Trust the device: bluetoothctl trust 41:42:86:99:6F:BA")
        print("3. Connect first: bluetoothctl connect 41:42:86:99:6F:BA")
        print("4. Then run this script immediately while connection is active")
        return

    raw_gray = "/tmp/t11_bt_gray.raw"
    cmd = [
        "magick",
        "-background",
        "white",
        image_path,
        "-alpha",
        "remove",
        "-flatten",
        "-resize",
        f"{WIDTH_PX}x",
    ]
    if mirror:
        cmd.insert(-1, "-flop")
    cmd += ["-colorspace", "gray", "-depth", "8", f"GRAY:{raw_gray}"]
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
                    byte_val |= 1 << (7 - bit)
            bit_data.append(byte_val)

    try:
        sock.send(b"\x1b@")

        print("Setting printer to Continuous Mode...")
        sock.send(b"\x1f\x1b\x1f\xa1\x00")
        time.sleep(0.5)

        print(f"Printing {height} lines...")
        for y_start in range(0, height, LINES_PER_BLOCK):
            y_end = min(y_start + LINES_PER_BLOCK, height)
            num_lines = y_end - y_start
            header = bytes(
                [
                    0x1D,
                    0x76,
                    0x30,
                    0,
                    BYTES_PER_LINE % 256,
                    BYTES_PER_LINE // 256,
                    num_lines % 256,
                    num_lines // 256,
                ]
            )
            sock.sendall(
                header + bit_data[y_start * BYTES_PER_LINE : y_end * BYTES_PER_LINE]
            )
            time.sleep(0.2)

            if y_start % 240 == 0:
                print(f"Progress: {y_start}/{height}")

        print("Finishing job and feeding paper...")
        sock.send(b"\x1bd\x02")
        time.sleep(2.0)
        sock.send(b"\x1b@")

        sock.close()
        print("Success!")
    except Exception as e:
        print(f"Print Error: {e}")
    finally:
        if os.path.exists(raw_gray):
            os.remove(raw_gray)


def print_pdf_bt(pdf_path, page_num=0, threshold=180):
    print(f"Connecting to {PRINTER_ADDR} via Bluetooth...")
    try:
        sock = connect_printer()
        print("Connected!")
    except Exception as e:
        print(f"Connection Failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure T11 is paired: bluetoothctl pair 41:42:86:99:6F:BA")
        print("2. Trust the device: bluetoothctl trust 41:42:86:99:6F:BA")
        print("3. Connect first: bluetoothctl connect 41:42:86:99:6F:BA")
        print("4. Then run this script immediately while connection is active")
        return

    raw_gray = "/tmp/t11_bt_gray.raw"
    cmd = [
        "magick",
        "-density",
        "300",
        "-background",
        "white",
        f"{pdf_path}[{page_num}]",
        "-alpha",
        "remove",
        "-flatten",
        "-resize",
        f"{WIDTH_PX}x",
        "-colorspace",
        "gray",
        "-depth",
        "8",
        f"GRAY:{raw_gray}",
    ]
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
                    byte_val |= 1 << (7 - bit)
            bit_data.append(byte_val)

    try:
        sock.send(b"\x1b@")

        print("Setting printer to Continuous Mode...")
        sock.send(b"\x1f\x1b\x1f\xa1\x00")
        time.sleep(0.5)

        print(f"Printing {height} lines...")
        for y_start in range(0, height, LINES_PER_BLOCK):
            y_end = min(y_start + LINES_PER_BLOCK, height)
            num_lines = y_end - y_start
            header = bytes(
                [
                    0x1D,
                    0x76,
                    0x30,
                    0,
                    BYTES_PER_LINE % 256,
                    BYTES_PER_LINE // 256,
                    num_lines % 256,
                    num_lines // 256,
                ]
            )
            sock.sendall(
                header + bit_data[y_start * BYTES_PER_LINE : y_end * BYTES_PER_LINE]
            )
            time.sleep(0.2)

            if y_start % 240 == 0:
                print(f"Progress: {y_start}/{height}")

        print("Finishing job and feeding paper...")
        sock.send(b"\x1bd\x00")
        time.sleep(2.0)
        sock.send(b"\x1b@")

        sock.close()
        print("Success!")
    except Exception as e:
        print(f"Print Error: {e}")
    finally:
        if os.path.exists(raw_gray):
            os.remove(raw_gray)


def print_text_bt(text_path, threshold=50):
    print(f"Connecting to {PRINTER_ADDR} via Bluetooth...")
    try:
        sock = connect_printer()
        print("Connected!")
    except Exception as e:
        print(f"Connection Failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure T11 is paired: bluetoothctl pair 41:42:86:99:6F:BA")
        print("2. Trust the device: bluetoothctl trust 41:42:86:99:6F:BA")
        print("3. Connect first: bluetoothctl connect 41:42:86:99:6F:BA")
        print("4. Then run this script immediately while connection is active")
        return

    mono_output = "/tmp/t11_bt_text.mono"
    cmd = [
        "magick",
        "-background",
        "white",
        "-fill",
        "black",
        "-font",
        "DejaVu-Sans-Mono",
        "-pointsize",
        "12",
        "-size",
        f"{WIDTH_PX}x",
        f"caption:@{text_path}",
        "-colorspace",
        "gray",
        "-threshold",
        f"{threshold}%",
        "-depth",
        "1",
        f"MONO:{mono_output}",
    ]

    print("Rendering...")
    subprocess.run(cmd, check=True)

    with open(mono_output, "rb") as f:
        bit_data = f.read()

    height = len(bit_data) // BYTES_PER_LINE
    print(f"Image Ready: {WIDTH_PX}x{height}")

    try:
        sock.send(b"\x1b@")

        print("Setting printer to Continuous Mode...")
        sock.send(b"\x1f\x1b\x1f\xa1\x00")
        time.sleep(0.5)

        print(f"Printing {height} lines...")
        for y_start in range(0, height, LINES_PER_BLOCK):
            y_end = min(y_start + LINES_PER_BLOCK, height)
            num_lines = y_end - y_start
            start_idx = y_start * BYTES_PER_LINE
            end_idx = y_end * BYTES_PER_LINE
            block_data = bit_data[start_idx:end_idx]
            header = bytes(
                [
                    0x1D,
                    0x76,
                    0x30,
                    0,
                    BYTES_PER_LINE % 256,
                    BYTES_PER_LINE // 256,
                    num_lines % 256,
                    num_lines // 256,
                ]
            )
            sock.sendall(header + block_data)
            time.sleep(0.2)
            if y_start % 480 == 0:
                print(f"Progress: {y_start}/{height}")

        print("Finishing job and feeding paper...")
        sock.send(b"\x1bd\x02")
        time.sleep(2.0)
        sock.send(b"\x1b@")

        sock.close()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(mono_output):
            os.remove(mono_output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="T11 Thermal Printer via Bluetooth")
    parser.add_argument("file", help="Image, PDF, or text file to print")
    parser.add_argument("--page", type=int, default=0, help="PDF page number")
    parser.add_argument("--threshold", type=int, default=128, help="Threshold (1-255)")
    parser.add_argument("--mirror", action="store_true", help="Mirror image")
    args = parser.parse_args()

    ext = os.path.splitext(args.file)[1].lower()

    if ext == ".pdf":
        print_pdf_bt(args.file, args.page, args.threshold)
    elif ext in [".txt", ".text"]:
        print_text_bt(args.file, args.threshold)
    else:
        print_image_bt(args.file, args.threshold, args.mirror)
