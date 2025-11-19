# Building the Executable

## Prerequisites

1. Python 3.7 or higher
2. PyInstaller: `pip install pyinstaller`
3. Required dependencies (from requirements.txt):
   - pydicom >= 2.3.0
   - Pillow >= 9.0.0
   - numpy >= 1.21.0

## Build Instructions

### Option 1: Using the spec file (recommended)

```bash
pyinstaller png_to_dicom.spec
```

The executable will be created in the `dist/` directory.

### Option 2: Using command line

```bash
pyinstaller --onefile --console --name png_to_dicom png_to_dicom.py
```

## Build Output

- **Executable location**: `dist/png_to_dicom.exe`
- **Build artifacts**: `build/` directory (can be deleted after build)
- **Spec file**: `png_to_dicom.spec` (saved for future builds)

## Usage

Once built, the executable can be used standalone:

```bash
# Convert a PNG file (creates output.dcm in same directory)
png_to_dicom.exe input.png

# Specify custom output path
png_to_dicom.exe input.png -o C:\path\to\output.dcm

# If output.dcm exists, it will automatically create output_1.dcm, output_2.dcm, etc.
```

## Testing the Executable

```bash
# Test with the sample image
dist\png_to_dicom.exe data\input_png\input.png

# Test duplicate file naming
dist\png_to_dicom.exe data\input_png\input.png
dist\png_to_dicom.exe data\input_png\input.png
```

## Troubleshooting

If the build fails with missing modules:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Try adding hidden imports to the spec file's `hiddenimports` list
3. Run with verbose output: `pyinstaller --log-level DEBUG png_to_dicom.spec`
