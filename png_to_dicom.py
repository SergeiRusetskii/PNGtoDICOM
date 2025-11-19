#!/usr/bin/env python3
"""
PNG to DICOM Converter
Converts PNG images to uncompressed DICOM format
"""

import numpy as np
from PIL import Image
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import generate_uid
import datetime
import os


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
    # Use data folder structure
    input_png = os.path.join("data", "input_png", "input.png")
    output_dicom = os.path.join("data", "output_DICOM", "output.dcm")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_dicom), exist_ok=True)

    # Check if input file exists
    if not os.path.exists(input_png):
        print(f"Error: Input file '{input_png}' not found!")
        print(f"Please place a PNG file named 'input.png' in the '{os.path.dirname(input_png)}' directory.")
        exit(1)

    try:
        png_to_dicom(input_png, output_dicom)
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
