#!/usr/bin/env python3
"""
D&D Spell Card Image Exporter
==============================

This script exports a single spell card as an image file (PNG).

Usage:
    python3 export_card_image.py "Spell Name" [options]

Options:
    -o, --output FILE     Output image file path (default: spell_name.png)
    -d, --dpi DPI        Image resolution in DPI (default: 600)
    -f, --format FORMAT  Image format: png, jpg, or svg (default: png)
    --keep-pdf           Keep the intermediate PDF file
    --help              Show this help message
"""

import argparse
import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
import json



def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []

    # Check if generate_cards.py exists
    if not os.path.exists('generate_cards.py'):
        missing_deps.append("generate_cards.py script")

    # Check if pdf2image conversion tool is available (ImageMagick or pdftoppm)
    convert_tool = shutil.which('convert') or shutil.which('magick')
    pdftoppm = shutil.which('pdftoppm')

    if not convert_tool and not pdftoppm:
        missing_deps.append("ImageMagick (convert/magick command) or pdftoppm for PDF to image conversion")

    if missing_deps:
        print("Error: Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install the missing dependencies and try again.")
        print("\nInstall ImageMagick:")
        print("  macOS: brew install imagemagick")
        print("  Ubuntu/Debian: sudo apt-get install imagemagick")
        print("  Windows: Download from https://imagemagick.org/")
        return False

    return True


def sanitize_filename(filename):
    """Convert spell name to safe filename."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    return filename.lower()


def generate_single_card_pdf(spell_name, output_pdf):
    """Generate PDF for a single spell card using generate_cards.py."""
    print("Generating spell card PDF...")

    # Create temporary directory for output
    temp_dir = tempfile.mkdtemp()

    try:
        # Run generate_cards.py with the specific spell name
        cmd = [
            'python3', 'generate_cards.py',
            '-n', spell_name,
            '-o', temp_dir
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print("Error running generate_cards.py:")
            print(result.stdout)
            print(result.stderr)
            return False

        # Check if cards.pdf was generated
        temp_pdf = os.path.join(temp_dir, 'cards.pdf')
        if not os.path.exists(temp_pdf):
            print("Error: cards.pdf was not generated")
            print(result.stdout)
            return False

        # Copy PDF to output location
        shutil.copy(temp_pdf, output_pdf)
        print(f"✓ Generated PDF: {output_pdf}")

        return True

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def convert_pdf_to_image(pdf_path, output_path, dpi=600, image_format='png'):
    """Convert PDF to image using ImageMagick or pdftoppm."""
    print(f"Converting PDF to {image_format.upper()} at {dpi} DPI...")

    # Try ImageMagick first
    convert_cmd = shutil.which('convert') or shutil.which('magick')

    if convert_cmd:
        # Determine quality settings based on format
        if image_format.lower() == 'jpg':
            quality = '80'
            # Add mozjpeg-like compression settings for efficient encoding
            extra_args = [
                '-sampling-factor', '4:2:0',  # Chroma subsampling
                '-interlace', 'JPEG',          # Progressive JPEG
                '-colorspace', 'sRGB'          # Color space optimization
            ]
        else:
            quality = '100'
            extra_args = []

        # Use ImageMagick
        if convert_cmd.endswith('magick'):
            # New ImageMagick syntax
            cmd = [
                convert_cmd, 'convert',
                '-density', str(dpi),
                pdf_path,
                '-quality', quality
            ] + extra_args + [output_path]
        else:
            # Old ImageMagick syntax
            cmd = [
                convert_cmd,
                '-density', str(dpi),
                pdf_path,
                '-quality', quality
            ] + extra_args + [output_path]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error converting PDF with ImageMagick:")
            print(result.stderr)
            return False
    else:
        # Fallback to pdftoppm (only for PNG/JPG)
        if image_format.lower() == 'svg':
            print("Error: SVG conversion requires ImageMagick")
            return False

        pdftoppm = shutil.which('pdftoppm')
        if not pdftoppm:
            print("Error: No conversion tool available")
            return False

        # pdftoppm outputs to a different format, need to specify output base
        output_base = str(Path(output_path).with_suffix(''))

        format_flag = '-png' if image_format.lower() == 'png' else '-jpeg'

        cmd = [
            pdftoppm,
            format_flag,
            '-r', str(dpi),
            '-singlefile',
            pdf_path,
            output_base
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error converting PDF with pdftoppm:")
            print(result.stderr)
            return False

    if os.path.exists(output_path):
        print(f"✓ Generated image: {output_path}")
        return True
    else:
        print("Error: Image file was not created")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Export a single D&D spell card as an image",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export Fireball as PNG
  python3 export_card_image.py "Fireball"

  # Export with custom output path
  python3 export_card_image.py "Magic Missile" -o my_spell.png

  # Export as high-res JPG
  python3 export_card_image.py "Lightning Bolt" -f jpg -d 900

  # Keep the intermediate PDF
  python3 export_card_image.py "Cure Wounds" --keep-pdf
        """
    )

    parser.add_argument(
        'spell_name',
        type=str,
        help="Name of the spell to export"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help="Output image file path (default: spell_name.png)"
    )
    parser.add_argument(
        '-d', '--dpi',
        type=int,
        default=600,
        help="Image resolution in DPI (default: 600)"
    )
    parser.add_argument(
        '-f', '--format',
        type=str,
        default='png',
        choices=['png', 'jpg', 'jpeg', 'svg'],
        help="Image format (default: png)"
    )
    parser.add_argument(
        '--keep-pdf',
        action='store_true',
        help="Keep the intermediate PDF file"
    )

    args = parser.parse_args()

    # Normalize format
    image_format = 'jpg' if args.format == 'jpeg' else args.format

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check if required files exist
    if not os.path.exists('data/spells.json'):
        print("Error: data/spells.json not found")
        sys.exit(1)

    print("D&D Spell Card Image Exporter")
    print("=" * 50)

    spell_name = args.spell_name
    print(f"Spell: {spell_name}")

    # Determine output path
    if args.output:
        output_image = args.output
    else:
        # Use samples directory by default
        os.makedirs('samples', exist_ok=True)
        safe_name = sanitize_filename(spell_name)
        output_image = f"samples/{safe_name}.{image_format}"

    # Create output directory if needed
    output_dir = os.path.dirname(output_image)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Generate PDF using generate_cards.py
    pdf_output = output_image.rsplit('.', 1)[0] + '.pdf'
    if not generate_single_card_pdf(spell_name, pdf_output):
        print("Error: Failed to generate PDF")
        sys.exit(1)

    # Convert PDF to image
    if not convert_pdf_to_image(pdf_output, output_image, args.dpi, image_format):
        print("Error: Failed to convert PDF to image")
        sys.exit(1)

    # Remove PDF if not keeping it
    if not args.keep_pdf and os.path.exists(pdf_output):
        os.remove(pdf_output)
        print(f"Removed intermediate PDF: {pdf_output}")

    print("\n✓ Spell card image exported successfully!")
    print(f"  - Output: {output_image}")
    print(f"  - Format: {image_format.upper()}")
    print(f"  - Resolution: {args.dpi} DPI")
    print("\nDone!")


if __name__ == '__main__':
    main()
