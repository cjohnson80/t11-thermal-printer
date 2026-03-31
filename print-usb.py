#!/usr/bin/env python3
import usb.core
import usb.util
import sys
import os
import argparse
import subprocess
import time

WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8
LINES_PER_BLOCK = 24
VENDOR_ID = 0x0483
PRODUCT_ID = 0x5720


def find_printer():
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        raise ValueError("T11 printer not found")
    return dev


def init_printer(dev):
    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)

    usb.util.claim_interface(dev, 0)

    dev.write(0x01, b"\x1b@")
    time.sleep(0.1)

    dev.write(0x01, b"\x1f\x1b\x1f\xa1\x00")
    time.sleep(0.1)


def send_data(dev, data):
    dev.write(0x01, data)


def print_image(image_path, threshold=128, mirror=False):
    print(f"Converting {image_path}...")

    raw_gray = "/tmp/t11_gray.raw"
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
    print(f"Image: {WIDTH_PX}x{height}")

    bit_data = bytearray()
    for y in range(height):
        for x_byte in range(BYTES_PER_LINE):
            byte_val = 0
            for bit in range(8):
                pixel_idx = (y * WIDTH_PX) + (x_byte * 8) + bit
                if pixel_idx < len(gray_data) and gray_data[pixel_idx] < threshold:
                    byte_val |= 1 << (7 - bit)
            bit_data.append(byte_val)

    dev = find_printer()
    init_printer(dev)

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
        block_data = bit_data[y_start * BYTES_PER_LINE : y_end * BYTES_PER_LINE]

        send_data(dev, header + block_data)
        time.sleep(0.2)

        if y_start % 240 == 0:
            print(f"Progress: {y_start}/{height}")

    send_data(dev, b"\x1bd\x02")
    time.sleep(2.0)
    send_data(dev, b"\x1b@")

    usb.util.release_interface(dev, 0)
    usb.util.dispose_resources(dev)

    os.remove(raw_gray)
    print("Done!")


def print_text(text_path, threshold=128):
    print(f"Converting {text_path}...")
    
    # Convert 0-255 threshold to 0-100 percentage for ImageMagick
    thresh_pct = int((threshold / 255.0) * 100)

    raw_gray = "/tmp/t11_gray.raw"
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
        f"{thresh_pct}%",
        "-depth",
        "1",
        f"MONO:{raw_gray}",
    ]
    subprocess.run(cmd, check=True)

    with open(raw_gray, "rb") as f:
        bit_data = f.read()

    height = len(bit_data) // BYTES_PER_LINE
    print(f"Text: {WIDTH_PX}x{height}")

    dev = find_printer()
    init_printer(dev)

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
        block_data = bit_data[y_start * BYTES_PER_LINE : y_end * BYTES_PER_LINE]

        send_data(dev, header + block_data)
        time.sleep(0.2)

        if y_start % 240 == 0:
            print(f"Progress: {y_start}/{height}")

    send_data(dev, b"\x1bd\x02")
    time.sleep(2.0)
    send_data(dev, b"\x1b@")

    usb.util.release_interface(dev, 0)
    usb.util.dispose_resources(dev)

    if os.path.exists(raw_gray):
        os.remove(raw_gray)
    print("Done!")


def print_pdf(pdf_path, page_num=0, threshold=180):
    print(f"Converting PDF {pdf_path} [Page {page_num}]...")

    raw_gray = "/tmp/t11_gray.raw"
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
    print(f"Packing {WIDTH_PX}x{height} pixels...")

    bit_data = bytearray()
    for y in range(height):
        for x_byte in range(BYTES_PER_LINE):
            byte_val = 0
            for bit in range(8):
                pixel_idx = (y * WIDTH_PX) + (x_byte * 8) + bit
                if pixel_idx < len(gray_data) and gray_data[pixel_idx] < threshold:
                    byte_val |= 1 << (7 - bit)
            bit_data.append(byte_val)

    dev = find_printer()
    init_printer(dev)

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
        block_data = bit_data[y_start * BYTES_PER_LINE : y_end * BYTES_PER_LINE]

        send_data(dev, header + block_data)
        time.sleep(0.2)

        if y_start % 240 == 0:
            print(f"Progress: {y_start}/{height}")

    send_data(dev, b"\x1bd\x00")
    time.sleep(2.0)
    send_data(dev, b"\x1b@")

    usb.util.release_interface(dev, 0)
    usb.util.dispose_resources(dev)

    os.remove(raw_gray)
    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="T11 Thermal Printer via USB")
    parser.add_argument("file", help="Image, PDF, or text file to print")
    parser.add_argument("--page", type=int, default=0, help="PDF page number")
    parser.add_argument("--threshold", type=int, default=128, help="Threshold (1-255)")
    parser.add_argument("--mirror", action="store_true", help="Mirror image")
    args = parser.parse_args()

    ext = os.path.splitext(args.file)[1].lower()

    if ext == ".pdf":
        print_pdf(args.file, args.page, args.threshold)
    elif ext in [".txt", ".text"]:
        print_text(args.file, args.threshold)
    else:
        print_image(args.file, args.threshold, args.mirror)
