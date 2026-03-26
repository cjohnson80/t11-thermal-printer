# T11 / M08F A4 Thermal Printer Linux Driver (USB)

This repository provides custom Python scripts and a pre-compiled CUPS filter to enable high-quality printing on the **T11 / Phomemo M08F** A4/US-Letter thermal printer using Linux.

## Hardware Support
- **Device ID:** `0483:5720` (STMicroelectronics STM32 Mass Storage/Printer)
- **Paper Size:** 8.5" x 11" (US Letter) or A4
- **Interface:** USB (`/dev/usb/lp0`)

## Features
- **Reliable Printing:** Uses a "block-printing" method (24 lines at a time) with intentional delays to prevent the USB buffer overflows common with these STM32-based printers.
- **High Quality PDF Printing:** Renders PDFs at 300 DPI with explicit white-background flattening and manual bit-packing for sharp, non-inverted text.
- **Image/Stencil Mode:** Supports printing common image formats with optional **mirroring** (essential for tattoo stencils) and adjustable brightness thresholds.

## Requirements
- Linux (Arch, Ubuntu, etc.)
- Python 3
- ImageMagick (`magick` command available in PATH)

## Usage

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

## Acknowledgments
Includes the `rastertozj` filter and PPDs derived from the [zj-58 project](https://github.com/klirichek/zj-58) for generic ESC/POS support.
