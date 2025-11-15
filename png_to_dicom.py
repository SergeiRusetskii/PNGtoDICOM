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

    # Handle transparency (alpha channel) - treat as lowest density
    if png_image.mode in ('RGBA', 'LA'):
        # Get the alpha channel
        if png_image.mode == 'RGBA':
            rgb = png_image.convert('RGB')
            alpha = png_image.split()[-1]
            # Create a white background
            background = Image.new('RGB', png_image.size, (0, 0, 0))
            # Composite the image with background where alpha is 0
            png_image = Image.composite(rgb, background, alpha)
        elif png_image.mode == 'LA':
            l_channel = png_image.split()[0]
            alpha = png_image.split()[-1]
            background = Image.new('L', png_image.size, 0)
            png_image = Image.composite(l_channel, background, alpha)

    # Convert to numpy array
    pixel_array = np.array(png_image)

    # Determine if image is color or grayscale
    if len(pixel_array.shape) == 3:
        # Color image (RGB)
        is_color = True
        rows, cols, _ = pixel_array.shape
        samples_per_pixel = 3
        photometric_interpretation = "RGB"

        # Ensure the array is in the correct shape for DICOM (rows, cols, samples)
        # PIL gives us this format already
        pixel_data = pixel_array
    else:
        # Grayscale image
        is_color = False
        rows, cols = pixel_array.shape
        samples_per_pixel = 1
        photometric_interpretation = "MONOCHROME2"
        pixel_data = pixel_array

    # Create a new DICOM dataset
    file_meta = pydicom.Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
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

    # Set instance information
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.InstanceNumber = "1"

    # Set image information
    ds.SamplesPerPixel = samples_per_pixel
    ds.PhotometricInterpretation = photometric_interpretation
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0  # Unsigned

    # For color images, set planar configuration
    if is_color:
        ds.PlanarConfiguration = 0  # Color-by-pixel (R1G1B1 R2G2B2 ...)

    # CT-specific parameters
    ds.SliceThickness = "1.0"  # Slice thickness in mm
    ds.KVP = "120"  # Peak kilovoltage output
    ds.DataCollectionDiameter = "500"  # Data collection diameter in mm

    # Image position and orientation (patient coordinate system)
    # ImagePositionPatient: x, y, z coordinates of upper left corner
    ds.ImagePositionPatient = [0.0, 0.0, 0.0]
    # ImageOrientationPatient: direction cosines of first row and first column
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    # Pixel spacing: physical distance between pixel centers (row spacing, column spacing)
    ds.PixelSpacing = [1.0, 1.0]  # 1mm x 1mm pixels

    # Slice location
    ds.SliceLocation = "0.0"

    # Rescale parameters for Hounsfield Units (HU)
    # HU = pixel_value * RescaleSlope + RescaleIntercept
    ds.RescaleIntercept = "-1024"  # Standard CT intercept
    ds.RescaleSlope = "1"
    ds.RescaleType = "HU"

    # Window settings for display
    # Standard soft tissue window
    ds.WindowCenter = "40"  # Center of window in HU
    ds.WindowWidth = "400"  # Width of window in HU

    # Equipment information
    ds.Manufacturer = "PNG to DICOM Converter"
    ds.ManufacturerModelName = "PNGtoDICOM v1.0"
    ds.SoftwareVersions = "1.0"

    # Set pixel data (uncompressed)
    ds.PixelData = pixel_data.tobytes()

    # Save the DICOM file
    ds.save_as(dicom_path, write_like_original=False)

    print(f"Successfully converted {png_path} to {dicom_path}")
    print(f"Image type: {'Color (RGB)' if is_color else 'Grayscale'}")
    print(f"Dimensions: {cols} x {rows}")
    print(f"Samples per pixel: {samples_per_pixel}")


if __name__ == "__main__":
    # Hardcoded filenames
    input_png = "input.png"
    output_dicom = "output.dcm"

    # Check if input file exists
    if not os.path.exists(input_png):
        print(f"Error: Input file '{input_png}' not found!")
        print("Please place a PNG file named 'input.png' in the current directory.")
        exit(1)

    try:
        png_to_dicom(input_png, output_dicom)
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
