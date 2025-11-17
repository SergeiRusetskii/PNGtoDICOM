# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
PNGtoDICOM is a standalone Python script for converting PNG images to uncompressed DICOM format. The script handles both RGB color images and grayscale images, with support for alpha channel transparency.

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
The script currently uses hardcoded filenames:
```bash
python png_to_dicom.py
```

Expected input: `input.png` in the current directory
Output: `output.dcm` in the current directory

## Architecture

### Core Conversion Logic (png_to_dicom.py)
The script is structured as a single-file utility with one main function:

**`png_to_dicom(png_path, dicom_path)`**: Main conversion function that:
1. Loads PNG using PIL/Pillow
2. Handles alpha channel transparency by compositing against black background
3. Converts to numpy array for pixel manipulation
4. Detects color vs grayscale format
5. Creates DICOM dataset with pydicom
6. Populates mandatory DICOM metadata fields
7. Writes uncompressed pixel data

### Key Technical Specifications

**DICOM Metadata (Hardcoded Values):**
- SOP Class: Secondary Capture Image Storage (1.2.840.10008.5.1.4.1.1.7)
- Modality: SC (Secondary Capture)
- Transfer Syntax: Explicit VR Little Endian (uncompressed)
- Patient: "PNG^CONVERTED" / "PNG001"
- Study ID: "1" / Accession: "ACC001"

**Image Handling:**
- Bit depth: 8-bit unsigned
- Color images: RGB, PlanarConfiguration = 0 (color-by-pixel interleaving)
- Grayscale: MONOCHROME2
- Alpha channel: Composited against black (0,0,0) for RGB or 0 for grayscale

### Important Implementation Notes

**Transparency Handling (lines 28-42):**
- RGBA → composite against black RGB background using PIL.Image.composite()
- LA (Luminance+Alpha) → composite against black grayscale background
- Alpha channel treated as lowest density (transparent = black)

**Pixel Data Format:**
- No compression applied - pixel data written directly as bytes
- RGB images maintain color-by-pixel format (R1G1B1 R2G2B2...)
- Pixel array shape: (rows, cols, 3) for RGB or (rows, cols) for grayscale

## Planned Enhancements
The README indicates future plans for:
- Command-line argument support for flexible input/output paths
- Windows executable (.exe) with parameter support

When implementing these features, maintain backwards compatibility with the core `png_to_dicom()` function.
