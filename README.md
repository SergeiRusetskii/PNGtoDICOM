# PNGtoDICOM
Small standalone script for converting PNG to DICOM (uncompressed)

## Features
- Converts PNG images to uncompressed DICOM CT format
- Automatically converts all images to grayscale (MONOCHROME2) for CT compliance
- Handles transparency (alpha channel) by treating it as lowest density (black)
- Maps pixel values to Hounsfield Units (HU) for proper CT display
- Uses standard CT metadata with dummy/default values

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
- DICOM SOP Class: CT Image Storage (1.2.840.10008.5.1.4.1.1.2)
- Modality: CT (Computed Tomography)
- Transfer Syntax: Explicit VR Little Endian
- Pixel data: Uncompressed, 8-bit, unsigned
- Photometric Interpretation: MONOCHROME2 (grayscale only)
- Image Type: DERIVED, SECONDARY
- Conversion Type: WSD (Workstation)

## CT-Specific Parameters
The converter adds standard CT DICOM parameters to simulate a single CT slice:
- **Slice Thickness**: 1.0 mm
- **KVP (Peak Kilovoltage)**: 120 kV
- **Pixel Spacing**: 1.0 x 1.0 mm
- **Image Position/Orientation**: Standard axial orientation at origin
- **Hounsfield Units Mapping**:
  - PNG pixel value 0 (black) → -160 HU
  - PNG pixel value 255 (white) → 240 HU
  - Rescale Slope: 1.5686 (400/255)
  - Rescale Intercept: -160
- **Window Settings**: Center 40 / Width 400 HU (soft tissue window)
- **Additional Attributes**: AcquisitionNumber, ConversionType, Equipment info
