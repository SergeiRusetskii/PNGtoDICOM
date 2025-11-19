#!/usr/bin/env python3
"""
PNG to DICOM Converter
Converts PNG images to uncompressed DICOM format
"""

# Disable pydicom's optional encoder plugins to avoid PyInstaller import issues
import os
import sys

# Mock the problematic encoder modules before pydicom imports them
# This prevents ImportError when these optional encoders aren't available
class MockEncoder:
    """Mock object that supports all operations pydicom encoder plugins need"""
    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __getitem__(self, key):
        return self

    def __iter__(self):
        return iter([])

class MockModule:
    """Mock module that provides mock encoders"""
    def __getattr__(self, name):
        return MockEncoder()

# Pre-emptively add mock modules for optional pydicom encoders
sys.modules['pydicom.encoders.gdcm'] = MockModule()
sys.modules['pydicom.encoders.pylibjpeg'] = MockModule()
sys.modules['pydicom.encoders.pyjpegls'] = MockModule()

os.environ['PYDICOM_SILENCE_PLUGIN_WARNINGS'] = '1'

import numpy as np
from PIL import Image
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import generate_uid
import datetime
import os
import sys
import argparse


def get_unique_filename(base_path):
    """
    Generate a unique filename by adding a numeric suffix if the file exists.

    Args:
        base_path: The desired output path (e.g., "image.dcm")

    Returns:
        A unique file path (e.g., "image.dcm", "image_1.dcm", "image_2.dcm", etc.)
    """
    if not os.path.exists(base_path):
        return base_path

    # Split the path into directory, basename, and extension
    directory = os.path.dirname(base_path)
    basename = os.path.basename(base_path)
    name, ext = os.path.splitext(basename)

    # Try incrementing numbers until we find a unique filename
    counter = 1
    while True:
        new_name = f"{name}_{counter}{ext}"
        new_path = os.path.join(directory, new_name) if directory else new_name
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def png_to_dicom(png_path, dicom_path):
    """
    Convert a PNG image to an uncompressed DICOM file.

    Args:
        png_path: Path to input PNG file
        dicom_path: Path to output DICOM file
    """

    # Read the PNG image
    png_image = Image.open(png_path)

    # Handle transparency (alpha channel) - treat as lowest density (black)
    if png_image.mode in ('RGBA', 'LA'):
        # Get the alpha channel
        if png_image.mode == 'RGBA':
            rgb = png_image.convert('RGB')
            alpha = png_image.split()[-1]
            # Create a black background
            background = Image.new('RGB', png_image.size, (0, 0, 0))
            # Composite the image with background where alpha is 0
            png_image = Image.composite(rgb, background, alpha)
        elif png_image.mode == 'LA':
            l_channel = png_image.split()[0]
            alpha = png_image.split()[-1]
            background = Image.new('L', png_image.size, 0)
            png_image = Image.composite(l_channel, background, alpha)

    # Always convert to grayscale for CT (MONOCHROME2)
    # CT images are always grayscale
    if png_image.mode != 'L':
        png_image = png_image.convert('L')

    # Convert to numpy array
    pixel_array = np.array(png_image)

    # Map PNG values (0-255) to HU range (-1000 to +3000)
    # PNG 0 (black) -> 0 pixel value -> -1000 HU
    # PNG 255 (white) -> 4000 pixel value -> +3000 HU
    # Using RescaleIntercept=-1000 and RescaleSlope=1
    # So we need pixel values from 0 to 4000
    # Scale PNG 0-255 to pixel values 0-4000
    # Use float conversion to avoid uint16 overflow, then convert to uint16
    pixel_array_16bit = (pixel_array.astype(np.float32) * 4000.0 / 255.0).astype(np.uint16)

    # CT images are always grayscale (MONOCHROME2)
    rows, cols = pixel_array.shape
    samples_per_pixel = 1
    photometric_interpretation = "MONOCHROME2"
    pixel_data = pixel_array_16bit

    # Create a new DICOM dataset
    file_meta = pydicom.Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian  # Uncompressed
    file_meta.ImplementationClassUID = generate_uid()

    # Create the FileDataset instance
    ds = FileDataset(dicom_path, {}, file_meta=file_meta, preamble=b"\0" * 128)

    # Set creation date/time
    dt = datetime.datetime.now()
    ds.ContentDate = dt.strftime('%Y%m%d')
    ds.ContentTime = dt.strftime('%H%M%S.%f')
    ds.InstanceCreationDate = dt.strftime('%Y%m%d')
    ds.InstanceCreationTime = dt.strftime('%H%M%S.%f')

    # Set patient information (dummy values)
    ds.PatientName = "PNG^CONVERTED"
    ds.PatientID = "PNG001"
    ds.PatientBirthDate = "19700101"
    ds.PatientSex = "O"

    # Set study information (dummy values)
    ds.StudyDate = dt.strftime('%Y%m%d')
    ds.StudyTime = dt.strftime('%H%M%S.%f')
    ds.StudyInstanceUID = generate_uid()
    ds.StudyID = "1"
    ds.AccessionNumber = "ACC001"

    # Set series information (dummy values)
    ds.SeriesInstanceUID = generate_uid()
    ds.SeriesNumber = "1"
    ds.Modality = "CT"  # Computed Tomography
    ds.SeriesDescription = "PNG to CT Conversion"

    # Frame of Reference (required for CT Image Storage)
    ds.FrameOfReferenceUID = generate_uid()
    ds.PositionReferenceIndicator = ""  # Empty string (no specific anatomical reference)

    # Set instance information
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.InstanceNumber = "1"

    # Set image information
    ds.SamplesPerPixel = samples_per_pixel
    ds.PhotometricInterpretation = photometric_interpretation
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0  # Unsigned

    # CT-specific parameters (copied from example CT_1slice.dcm)
    ds.SliceThickness = "1.5"  # Slice thickness in mm
    ds.KVP = "120"  # Peak kilovoltage output
    ds.DataCollectionDiameter = "600.5"  # Data collection diameter in mm

    # Image position and orientation (patient coordinate system)
    # ImagePositionPatient: x, y, z coordinates of upper left corner (use strings for DS type)
    ds.ImagePositionPatient = ["-249.51171875", "-499.01171875", "138"]
    # ImageOrientationPatient: direction cosines of first row and first column
    ds.ImageOrientationPatient = ["1", "0", "0", "0", "1", "0"]

    # Pixel spacing: physical distance between pixel centers (row spacing, column spacing)
    ds.PixelSpacing = ["0.9765625", "0.9765625"]  # From example CT

    # Slice location
    ds.SliceLocation = "138"

    # Rescale parameters for Hounsfield Units (HU)
    # Map pixel values 0-4000 to HU range -1000 to +3000
    # HU = pixel_value * RescaleSlope + RescaleIntercept
    # HU = pixel_value * 1 + (-1000)
    ds.RescaleIntercept = "-1000"  # Minimum HU value
    ds.RescaleSlope = "1"  # 1:1 mapping
    ds.RescaleType = "HU"

    # Window settings for display (from example CT)
    # Standard soft tissue window
    ds.WindowCenter = "40"  # Center of window in HU
    ds.WindowWidth = "200"  # Width of window in HU

    # Required CT attributes
    ds.AcquisitionNumber = "1"
    ds.ImageType = ["DERIVED", "SECONDARY"]  # Derived from non-DICOM source
    ds.ConversionType = "WSD"  # Workstation conversion

    # Equipment information
    ds.Manufacturer = "PNG to DICOM Converter"
    ds.ManufacturerModelName = "PNGtoDICOM v1.0"
    ds.SoftwareVersions = "1.0"

    # Set pixel data (uncompressed)
    ds.PixelData = pixel_data.tobytes()

    # Save the DICOM file
    ds.save_as(dicom_path, write_like_original=False)

    print(f"Successfully converted {png_path} to {dicom_path}")
    print(f"Image type: Grayscale (MONOCHROME2)")
    print(f"Dimensions: {cols} x {rows}")
    print(f"Modality: CT (Computed Tomography)")
    print(f"Bit depth: 16-bit (BitsAllocated={ds.BitsAllocated})")
    print(f"Transfer Syntax: {file_meta.TransferSyntaxUID} (Uncompressed)")
    print(f"HU Range: {int(ds.RescaleIntercept)} to {int(ds.RescaleIntercept) + 4000} (mapped from PNG 0-255)")


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Convert PNG images to DICOM CT format",
        epilog="Example: png_to_dicom.exe image.png"
    )
    parser.add_argument(
        "input_png",
        nargs='?',
        help="Path to input PNG file"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to output DICOM file (optional, defaults to same name/location as input)"
    )

    args = parser.parse_args()

    # If no arguments provided, use default data folder structure for backwards compatibility
    if args.input_png is None:
        input_png = os.path.join("data", "input_png", "input.png")
        output_dicom = os.path.join("data", "output_DICOM", "output.dcm")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_dicom), exist_ok=True)

        # Check if input file exists
        if not os.path.exists(input_png):
            print(f"Error: No input file specified and default '{input_png}' not found!")
            print(f"\nUsage: {os.path.basename(sys.argv[0])} <input.png> [-o output.dcm]")
            print(f"\nExample: {os.path.basename(sys.argv[0])} image.png")
            sys.exit(1)
    else:
        input_png = args.input_png

        # Check if input file exists
        if not os.path.exists(input_png):
            print(f"Error: Input file '{input_png}' not found!")
            sys.exit(1)

        # Check if input is a PNG file
        if not input_png.lower().endswith('.png'):
            print(f"Error: Input file must be a PNG image (got: {input_png})")
            sys.exit(1)

        # Determine output path
        if args.output:
            output_dicom = args.output
        else:
            # Create output filename in same directory as input with .dcm extension
            input_dir = os.path.dirname(input_png)
            input_basename = os.path.basename(input_png)
            output_basename = os.path.splitext(input_basename)[0] + ".dcm"
            output_dicom = os.path.join(input_dir, output_basename) if input_dir else output_basename

        # Ensure output directory exists
        output_dir = os.path.dirname(output_dicom)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Get unique filename if file already exists
        output_dicom = get_unique_filename(output_dicom)

    try:
        png_to_dicom(input_png, output_dicom)
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
