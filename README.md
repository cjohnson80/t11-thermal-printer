# THE ULTIMATE T11 / Phomemo M08F Linux Driver (Unified Edition)

This is the **only stable, high-quality Linux driver solution** for the generic Chinese T11 and Phomemo M08F A4 Thermal Printers.

## 🚀 Recent Critical Fixes (v2.0)

This driver has been refined to solve the most common "Chinese Thermal Printer" issues:

1.  **Infinite Paper Feeding:** Fixed a critical bug in the height calculation where raw 8-bit grayscale data was misinterpreted, causing the printer to feed 8x more paper than needed.
2.  **Tear-off Alignment:** Updated the end-of-job sequence to stop exactly at the last printed line (`\x1bd\x00`), preventing the 1.5" overshoot past the tear-off bar.
3.  **Unified Driver:** Replaced fragmented scripts with a single `t11-print.py` that handles all file types (PDF, PNG, JPG, TXT) and connection modes (USB, Bluetooth).
4.  **Bluetooth Stability:** Implemented "Safe Packet" mode (64-byte chunks with 5ms delays) to prevent the printer's internal buffer from crashing on Bluetooth.

## 📦 Installation

### 1. Requirements

- Python 3 with pyusb: `pip install pyusb`
- ImageMagick (`magick` command available in PATH)
- Ghostscript (for PDF rendering)

### 2. Standard Usage (Recommended)

The new `t11-print.py` script is the most reliable way to print.

```bash
# Print a PDF (USB)
python3 t11-print.py document.pdf

# Print a Text file (USB)
python3 t11-print.py notes.txt

# Print via Bluetooth
python3 t11-print.py image.png --mode bt --bt-addr 41:42:86:99:6F:BA

# Mirror image (for Tattoo Stencils)
python3 t11-print.py design.png --mirror
```

## 🛠 CUPS Integration (System Printer)

To use the T11 as a standard system printer (visible in Chrome, LibreOffice, etc.):

### 1. Install Backend
```bash
sudo cp t11-usb-backend /usr/lib/cups/backend/t11-usb
sudo chmod +x /usr/lib/cups/backend/t11-usb
```

### 2. Add Printer
Use the provided `t11.ppd` file. When prompted for a driver in CUPS, select **"Provide a PPD File"** and point to `t11.ppd`.

```bash
sudo lpadmin -p T11_Printer -E -v "t11-usb://" -i t11.ppd
```

## 🔧 Options & Customization

- `--threshold [0-255]`: Adjust darkness (Default 128). Lower values are darker.
- `--page [num]`: Select specific page from a PDF.
- `--mode [usb|bt]`: Choose connection method.

## 📋 Hardware Specs
- **Device ID:** `0483:5720`
- **Resolution:** 203 DPI (1728 pixels wide)
- **Paper:** US Letter (8.5") or A4 Thermal Roll/Fold
- **Protocol:** ESC/POS (Customized)

---
*Maintained by Chris Johnson. Refined with the help of Gemini CLI for extreme stability.*
