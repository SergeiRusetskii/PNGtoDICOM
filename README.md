# PNGtoDICOM
Small standalone script for converting PNG to DICOM (uncompressed)

## Features
- Converts PNG images to uncompressed DICOM format
- Supports both color (RGB) and grayscale images
- Handles transparency (alpha channel) by treating it as lowest density
- Uses dummy/default values for DICOM metadata

## Requirements
- Python 3.6 or higher
- pydicom
- Pillow (PIL)
- numpy

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Currently uses hardcoded filenames:
1. Place your PNG file in the same directory as the script and name it `input.png`
2. Run the script:
   ```bash
   python png_to_dicom.py
   ```
3. The converted DICOM file will be saved as `output.dcm`

## Future Enhancements
- Command-line arguments support
- Executable (.exe) file for Windows with parameter support

## Technical Details
- DICOM SOP Class: Secondary Capture Image Storage (1.2.840.10008.5.1.4.1.1.7)
- Modality: SC (Secondary Capture)
- Transfer Syntax: Explicit VR Little Endian
- Pixel data: Uncompressed, 8-bit
- Photometric Interpretation: RGB for color, MONOCHROME2 for grayscale
