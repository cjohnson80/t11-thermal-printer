# THE ULTIMATE T11 / Phomemo M08F Linux Driver

This is the **only stable, high-quality Linux driver solution** for the generic Chinese T11 and Phomemo M08F A4 Thermal Printers. 

If you have tried other thermal printer drivers and experienced **USB crashes (EPROTO -71)**, **garbled/slanted text**, or **infinite paper feeding**, this repository contains the fix.

## 🚀 The Fixes
This driver solves the four major problems with this hardware:
1. **USB Stability:** Standard drivers send data too fast, crashing the printer's fragile STM32 chip. We use a **Block-Printing method** with intentional hardware delays.
2. **Perfect Alignment:** Standard filters often output incorrect bit-packing. We use **Manual MSB Bit-Packing** to ensure every pixel is exactly where it belongs.
3. **No Paper Overshoot:** We force the printer into **Continuous Mode** (`\x1f\x1b\x1f\xa1\x00`) to stop it from jumping 1.5 inches after every print.
4. **Professional Quality:** Renders PDFs and images at **300+ DPI** with white-background flattening for sharp, readable documents and tattoo stencils.

## 🛠 Hardware Compatibility
- **Device ID:** `0483:5720` (STMicroelectronics Mass Storage/Printer)
- **Common Names:** T11, T11PRO, Phomemo M08F, WBK, SPRT SP-RMT11.
- **Paper Size:** US Letter (8.5"x11") and A4.
- **Connection:** Bluetooth (Primary/Stable) and USB.

## 📦 Installation & Usage

### 1. Requirements
- Linux (Arch, Ubuntu, etc.)
- Python 3
- ImageMagick (`magick` command available in PATH)

### 2. Standalone Drivers (Recommended for Stencils/PDFs)
The standalone scripts bypass the fragile CUPS system and talk directly to the printer for maximum reliability.

**Print a PDF Document:**
```bash
python3 print-pdf-t11.py document.pdf
```

**Print an Image / Tattoo Stencil:**
```bash
# Add --mirror for tattoo carbon transfers
python3 print-image-t11-usb.py image.png --mirror
```

**Print Plain Text:**
```bash
python3 print-text-t11.py notes.txt
```

### 3. CUPS Integration (System Printer)
If you want the printer to appear in your standard system print dialog:
1. Copy the filter: `sudo cp rastertozj /usr/lib/cups/filter/ && sudo chmod +x /usr/lib/cups/filter/rastertozj`
2. Copy the PPD: `sudo cp t11.ppd /usr/share/cups/model/`
3. Add the printer: `sudo lpadmin -p T11_Printer -E -v usb://0483/5720?serial=0001 -m t11.ppd`

## ⚖️ Options
- `--threshold [1-99]`: Adjust darkness (Default 50). Use a higher number for thinner lines.
- `--mirror`: Flips the image horizontally (Essential for tattoo stencils).
- `--page [num]`: Select which page of a PDF to print.

## 🛡 Future Proof
Unlike standard CUPS drivers which are being deprecated, the **Python Standalone Drivers** in this repo talk directly to the hardware node. They will continue to work regardless of changes to the Linux printing architecture.

---
*Created by Chris Johnson & Gemini MAS. Derived from the zj-58 project with massive stability and A4-specific refinements.*
