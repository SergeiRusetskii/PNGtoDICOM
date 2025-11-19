# PNGtoDICOM

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Standalone converter for transforming PNG images to DICOM CT format

## Features
- Converts PNG images to uncompressed DICOM CT format
- Automatically converts all images to grayscale (MONOCHROME2) for CT compliance
- Handles transparency (alpha channel) by treating it as lowest density (black)
- Maps pixel values to Hounsfield Units (HU) for proper CT display
- Uses standard CT metadata with dummy/default values
- **Command-line argument support** for flexible input/output
- **Windows executable (.exe)** available - no Python installation required
- **Automatic unique filename generation** to prevent overwrites

## Quick Start

### Option 1: Windows Executable (No Installation Required)
1. Download `png_to_dicom.exe` from the [releases page](https://github.com/SergeiRusetskii/PNGtoDICOM/releases)
2. Run from command line:
   ```cmd
   png_to_dicom.exe image.png
   ```
3. Output will be saved as `image.dcm` in the same directory

### Option 2: Python Script
**Requirements:**
- Python 3.6 or higher
- pydicom >= 2.3.0
- Pillow >= 9.0.0
- numpy >= 1.21.0

**Installation:**
```bash
pip install -r requirements.txt
```

## Usage

### Command-line Arguments (Recommended)
```bash
# Convert a single PNG file (output will be input.dcm)
python png_to_dicom.py input.png

# Specify output filename
python png_to_dicom.py input.png -o output.dcm

# Use with Windows executable
png_to_dicom.exe image.png -o custom_name.dcm
```

### Legacy Mode (Backwards Compatible)
If no arguments are provided, the script uses the `data/` folder structure:
- Input: `data/input_png/input.png`
- Output: `data/output_DICOM/output.dcm`

```bash
python png_to_dicom.py
```

## Building the Executable

See [BUILD.md](BUILD.md) for detailed instructions on building the Windows executable using PyInstaller.

## Technical Details
- DICOM SOP Class: CT Image Storage (1.2.840.10008.5.1.4.1.1.2)
- Modality: CT (Computed Tomography)
- Transfer Syntax: Implicit VR Little Endian (uncompressed)
- Pixel data: Uncompressed, 16-bit, unsigned
- Photometric Interpretation: MONOCHROME2 (grayscale only)
- Image Type: DERIVED, SECONDARY
- Conversion Type: WSD (Workstation)

## CT-Specific Parameters
The converter adds standard CT DICOM parameters to simulate a single CT slice:
- **Slice Thickness**: 1.5 mm
- **KVP (Peak Kilovoltage)**: 120 kV
- **Pixel Spacing**: 0.9765625 x 0.9765625 mm
- **Image Position/Orientation**: Standard axial orientation
- **Hounsfield Units Mapping**:
  - PNG pixel value 0 (black) → -1000 HU (air)
  - PNG pixel value 255 (white) → +3000 HU (dense bone)
  - Rescale Slope: 1
  - Rescale Intercept: -1000
  - Full range: 0-4000 pixel values → -1000 to +3000 HU
- **Window Settings**: Center 40 / Width 200 HU (soft tissue window)
- **Additional Attributes**: AcquisitionNumber, ConversionType, Equipment info, Frame of Reference UID

## Version History
- **v1.0** (2025-11-19): Added command-line arguments, PyInstaller executable support, automatic unique filenames
- **v0.x**: Initial implementation with hardcoded file paths

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Sergei Rusetskii
