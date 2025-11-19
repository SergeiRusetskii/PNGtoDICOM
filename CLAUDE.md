# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
PNGtoDICOM is a standalone Python script and Windows executable for converting PNG images to uncompressed DICOM CT format. The application supports command-line arguments for flexible input/output and can be built as a standalone .exe using PyInstaller.

**Current Version**: 1.0

## Development Setup

### Environment Setup
```bash
pip install -r requirements.txt
```

Required dependencies:
- pydicom >= 2.3.0 (DICOM file handling)
- Pillow >= 9.0.0 (PNG image processing)
- numpy >= 1.21.0 (pixel array manipulation)

### Running the Script

**With command-line arguments** (recommended):
```bash
python png_to_dicom.py input.png [-o output.dcm]
```

**Legacy mode** (backwards compatible, no arguments):
```bash
python png_to_dicom.py
```
Expected input: `data/input_png/input.png`
Output: `data/output_DICOM/output.dcm`

### Building the Executable
See [BUILD.md](BUILD.md) for PyInstaller build instructions.

## Architecture

### Core Conversion Logic (png_to_dicom.py)
The script is structured as a single-file utility with the following key components:

**Mock Encoder Classes** (lines 13-35):
- `MockEncoder`: Provides mock implementation for pydicom optional encoder plugins
- `MockModule`: Module-level mock for gdcm, pylibjpeg, pyjpegls
- Required for PyInstaller compatibility to avoid ImportError on missing optional dependencies

**`get_unique_filename(base_path)`** (lines 38-51):
- Generates unique filenames by appending numeric suffixes (_1, _2, etc.)
- Prevents accidental file overwrites
- Returns base_path if file doesn't exist, otherwise finds next available number

**`png_to_dicom(png_path, dicom_path)`** (lines 54-213):
Main conversion function that:
1. Loads PNG using PIL/Pillow
2. Handles alpha channel transparency by compositing against black background
3. Converts to grayscale (required for CT modality)
4. Maps 8-bit PNG (0-255) to 16-bit pixel values (0-4000) for HU range
5. Creates DICOM dataset with pydicom
6. Populates mandatory DICOM metadata fields including Frame of Reference
7. Writes uncompressed pixel data

**Command-line Interface** (lines 215-283):
- Uses argparse for flexible argument handling
- Supports positional input_png argument and optional -o/--output flag
- Falls back to legacy data/ folder structure when no arguments provided
- Validates input file exists and has .png extension

### Key Technical Specifications

**DICOM Metadata (Hardcoded Values):**
- SOP Class: CT Image Storage (1.2.840.10008.5.1.4.1.1.2)
- Modality: CT (Computed Tomography)
- Transfer Syntax: Implicit VR Little Endian (uncompressed)
- Patient: "PNG^CONVERTED" / "PNG001" / Sex: "O"
- Study ID: "1" / Accession: "ACC001"
- Equipment: "PNG to DICOM Converter" / Model: "PNGtoDICOM v1.0"

**Image Handling:**
- Bit depth: 16-bit unsigned (BitsAllocated=16, BitsStored=16, HighBit=15)
- All images converted to grayscale: MONOCHROME2
- Alpha channel: Composited against black (0) for grayscale
- Pixel values: 0-4000 range mapping to -1000 to +3000 HU

### Important Implementation Notes

**PyInstaller Compatibility (lines 13-35):**
- Mock encoder modules must be created BEFORE importing pydicom
- Prevents ImportError when pydicom tries to load optional encoders (gdcm, pylibjpeg, pyjpegls)
- Mock classes must support __getattr__, __call__, __getitem__, and __iter__
- Critical for .exe builds - do not remove or modify without testing PyInstaller build

**Transparency Handling (lines 67-80):**
- RGBA → composite against black RGB background, then convert to grayscale
- LA (Luminance+Alpha) → composite against black grayscale background
- Alpha channel treated as lowest density (transparent = black)

**Pixel Data Format:**
- No compression applied - pixel data written directly as bytes
- 16-bit unsigned pixel values (0-4000)
- Pixel array shape: (rows, cols) for grayscale
- HU mapping: pixel_value * RescaleSlope + RescaleIntercept = HU
  - With RescaleSlope=1, RescaleIntercept=-1000
  - 0 → -1000 HU (air), 4000 → +3000 HU (dense bone)

**CT-Specific Parameters (lines 160-188):**
- SliceThickness: "1.5" mm
- KVP: "120" (kilovoltage)
- PixelSpacing: ["0.9765625", "0.9765625"] mm
- ImagePositionPatient, ImageOrientationPatient: Standard axial orientation
- RescaleIntercept: "-1000", RescaleSlope: "1", RescaleType: "HU"
- WindowCenter: "40", WindowWidth: "200" (soft tissue window)

## Version History

**v1.0 (2025-11-19)**:
- ✅ Command-line argument support (argparse)
- ✅ Windows executable (.exe) with PyInstaller
- ✅ Automatic unique filename generation
- ✅ Proper 16-bit HU mapping (-1000 to +3000)
- ✅ Backwards compatibility with data/ folder structure

**v0.x**: Initial implementation with hardcoded file paths

## Future Considerations
When making changes to this codebase:
- Maintain backwards compatibility with legacy data/ folder mode
- Test both Python script AND PyInstaller executable after changes
- Keep mock encoder classes intact for PyInstaller compatibility
- Preserve the core `png_to_dicom()` function signature
