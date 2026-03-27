# T11 / M08F A4 Thermal Printer Linux Driver (USB)

This repository provides custom Python scripts and a pre-compiled CUPS filter to enable high-quality printing on the **T11 / Phomemo M08F** A4/US-Letter thermal printer using Linux.

**Note:** This solution is currently optimized for printing **PDF and Image files** using the provided standalone Python scripts. While CUPS integration is included, the standalone scripts offer the highest stability for this specific hardware.

## Hardware Support
- **Device ID:** `0483:5720` (STMicroelectronics STM32 Mass Storage/Printer)
- **Paper Size:** 8.5" x 11" (US Letter) or A4
- **Interface:** USB (`/dev/usb/lp0`)

## Features
- **Reliable Printing:** Uses a "block-printing" method (24 lines at a time) with a 20-30ms delay to prevent the USB buffer overflows (EPROTO -71) common with these STM32-based printers.
- **High Quality PDF Printing:** Renders PDFs at 300+ DPI with explicit white-background flattening and manual bit-packing for sharp, non-inverted text.
- **Image/Stencil Mode:** Supports printing common image formats with optional **mirroring** (essential for tattoo stencils) and adjustable brightness thresholds.
- **CUPS Integration:** Includes a custom `t11.ppd` and an optimized `rastertozj` filter for standard system printing.

## 1. CUPS Installation (Standard System Printer)

If you want the printer to show up in Chrome, LibreOffice, or your system print dialog:

```bash
# 1. Install the Filter & PPD
sudo cp rastertozj /usr/lib/cups/filter/
sudo chmod +x /usr/lib/cups/filter/rastertozj
sudo cp t11.ppd /usr/share/cups/model/

# 2. Start CUPS
sudo systemctl enable --now cups

# 3. Create the Print Queue
# Note: Check your serial/URI with 'lpinfo -v' if this fails
sudo lpadmin -p T11_Printer -E -v usb://0483/5720?serial=0001 -m t11.ppd
```

## 2. Python Script Usage (Direct Printing)

For more control (like mirroring for tattoo stencils), use the standalone scripts:

### Printing Documents (PDF)
```bash
python3 print-pdf-t11.py document.pdf
```

### Printing Images / Stencils
```bash
python3 print-image-t11-usb.py image.png --mirror
```

### Options
- `--threshold [0-255]`: Adjust darkness (lower is darker, default 128).
- `--mirror`: Flips the image horizontally (for `print-image` only).
- `--page [num]`: Print a specific page from a PDF (default 0).

## Troubleshooting
- **Input/Output Error (-5):** The printer buffer is full. Unplug and replug the USB cable to reset the `/dev/usb/lp0` node.
- **All Black Page:** Ensure the PDF is flattened against a white background (handled automatically by `print-pdf-t11.py`).
- **White Lines:** Occurs if sending lines individually. Use the "Block Mode" scripts provided here to ensure continuous printing.

## Future Compatibility & CUPS Deprecation
You may see a notice in CUPS stating that "Printer drivers are deprecated and will stop working in a future version." 

**Do not worry.**
1. **Long-term Support:** CUPS (and most Linux distros) will continue to support the current PPD/Filter system for several years.
2. **Standalone Scripts:** The Python scripts included here (`print-pdf-t11.py` and `print-image-t11-usb.py`) **do not use CUPS**. They communicate directly with the printer via the USB device node (`/dev/usb/lp0`). This means even if CUPS completely removes driver support in the distant future, your printer will remain fully functional using these scripts.

## Acknowledgments
The `rastertozj` filter and PPD base are derived from the [zj-58 project](https://github.com/klirichek/zj-58). This version adds essential delays for A4/T11 hardware stability.
