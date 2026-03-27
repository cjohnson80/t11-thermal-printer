import socket, sys, subprocess, os, argparse, time

PRINTER_ADDR = '41:42:86:99:6F:BA'
RFCOMM_CHANNEL = 2
WIDTH_PX = 1728
BYTES_PER_LINE = WIDTH_PX // 8
LINES_PER_BLOCK = 24

def print_image_gold(image_path, threshold=128, mirror=False):
    print(f"Connecting to {PRINTER_ADDR}...")
    try:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.connect((PRINTER_ADDR, RFCOMM_CHANNEL))
        print("Connected!")
    except Exception as e:
        print(f"Connection Failed: {e}"); return

    raw_gray = "gold_img.gray"
    cmd = ["magick", "-background", "white", image_path, "-alpha", "remove", "-flatten", "-resize", f"{WIDTH_PX}x"]
    if mirror: cmd.insert(-1, "-flop")
    cmd += ["-colorspace", "gray", "-depth", "8", f"GRAY:{raw_gray}"]
    subprocess.run(cmd, check=True)
    
    with open(raw_gray, "rb") as f: gray_data = f.read()
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

    try:
        sock.send(b'\x1b@')
        for y_start in range(0, height, LINES_PER_BLOCK):
            y_end = min(y_start + LINES_PER_BLOCK, height)
            num_lines = y_end - y_start
            header = bytes([0x1d, 0x76, 0x30, 0, BYTES_PER_LINE % 256, BYTES_PER_LINE // 256, num_lines % 256, num_lines // 256])
            sock.sendall(header + bit_data[y_start * BYTES_PER_LINE : y_end * BYTES_PER_LINE])
            time.sleep(0.2)
        # CLEAN EXIT SEQUENCE
        print("Finishing job and feeding paper...")
        sock.send(b'\x1bd\x02') # Reduced feed to 2 lines
        time.sleep(2.0)         # WAIT for the physical motor to finish
        sock.send(b'\x1b@')     # Reset printer state for the next job
        time.sleep(0.5)         # Let the reset settle
        
        sock.close()
        print("Success! Printer ready for next page.")
    finally:
        if os.path.exists(raw_gray): os.remove(raw_gray)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('--threshold', type=int, default=128)
    parser.add_argument('--mirror', action='store_true')
    args = parser.parse_args()
    print_image_gold(args.image, args.threshold, args.mirror)
