#!/usr/bin/env python3
"""
D&D Spelldeck Generator
======================

This script generates spell cards in one go by:
1. Running the generate.py script to create spells.tex
2. Compiling the LaTeX files to generate PDFs
3. Optionally cleaning up intermediate files

Usage:
    python3 generate_cards.py [options]

Options:
    -i, --input FILE      Input spells JSON file (default: data/spells.json)
    -c, --class CLASS     Filter by class (can be used multiple times)
    -l, --level LEVEL     Filter by level (can be used multiple times, supports ranges like 1-3)
    -s, --school SCHOOL   Filter by school (can be used multiple times)
    -n, --name NAME       Filter by spell name (can be used multiple times)
    --sort-by {name,level} Sort spells by name (default) or by level (then by name)
    -o, --output DIR      Output directory (default: pdf/)
    --clean               Clean up intermediate files after generation
    --no-compile          Skip LaTeX compilation (only generate spells.tex)
    --latex-compiler CMD  LaTeX compiler to use with latexmk (default: xelatex)
    --help               Show this help message
"""

import argparse
import os
import sys
import subprocess
import shutil
from pathlib import Path
import shlex


def check_dependencies(input_file='data/spells.json'):
    """Check if required dependencies are available."""
    missing_deps = []
    
    # Check Python
    if sys.version_info < (3, 6):
        missing_deps.append("Python 3.6 or higher")
    
    # Check if generate.py exists
    if not os.path.exists('generate.py'):
        missing_deps.append("generate.py script")
    
    # Check if input spells.json exists
    if not os.path.exists(input_file):
        missing_deps.append(f"{input_file} file")
    
    # Check LaTeX tools
    latexmk = shutil.which('latexmk')
    if not latexmk:
        missing_deps.append("latexmk (LaTeX build tool)")
    
    xelatex = shutil.which('xelatex')
    if not xelatex:
        missing_deps.append("xelatex (LaTeX compiler)")
    
    if missing_deps:
        print("Error: Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install the missing dependencies and try again.")
        return False
    
    return True


def run_command(cmd, cwd=None, check=True, show_progress=False):
    """Run a command and return the result."""
    try:
        if show_progress:
            # Run with real-time output for progress indication
            process = subprocess.Popen(cmd, shell=True, cwd=cwd,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, bufsize=1)

            # Print output line by line as it comes
            for line in process.stdout:
                print(line, end='', flush=True)

            process.wait()

            if check and process.returncode != 0:
                print(f"Error running command: {cmd}")
                print(f"Return code: {process.returncode}")
                return None

            # Create a result-like object for compatibility
            class Result:
                def __init__(self, returncode):
                    self.returncode = returncode
                    self.stdout = ""
                    self.stderr = ""

            return Result(process.returncode)
        else:
            result = subprocess.run(cmd, shell=True, cwd=cwd, check=check,
                                  capture_output=True, text=True)
            return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return None


def ensure_tex_templates():
    """Ensure required LaTeX template files exist in tex/ directory."""
    print("Checking LaTeX template files...")
    
    # Check if required files exist in tex/ directory
    required_files = ['cards.tex', 'printable.tex']
    
    for template_file in required_files:
        file_path = os.path.join('tex', template_file)
        if not os.path.exists(file_path):
            print(f"Error: Template file {file_path} not found")
            return False
        print(f"  Found {template_file}")
    
    # Check if images directory exists in root
    images_dir = 'images'
    if not os.path.exists(images_dir):
        print(f"Warning: Images directory {images_dir} not found")
    else:
        print("  Found images directory")
    
    return True


def generate_spells_tex(args):
    """Generate the spells.tex file using generate.py in tex/ directory."""
    print("Generating spells.tex...")
    
    # Build the generate.py command
    cmd_parts = ['python3', 'generate.py']
    
    if args.input:
        cmd_parts.extend(['-i', args.input])
    
    if args.classes:
        for cls in args.classes:
            cmd_parts.extend(['-c', cls])
    
    if args.levels:
        for level in args.levels:
            cmd_parts.extend(['-l', level])
    
    if args.schools:
        for school in args.schools:
            cmd_parts.extend(['-s', school])
    
    if args.names:
        for name in args.names:
            cmd_parts.extend(['-n', name])
    
    if args.sort_by:
        cmd_parts.extend(['--sort-by', args.sort_by])
    
    # Run the command and redirect output to spells.tex in tex/ directory
    # Quote each argument to be safe for the shell
    cmd = ' '.join(shlex.quote(part) for part in cmd_parts)
    spells_tex_path = os.path.join('tex', 'spells.tex')
    
    result = run_command(f"{cmd} > {spells_tex_path}")
    if result is None:
        return False, 0, 0, 0
    
    if not os.path.exists(spells_tex_path) or os.path.getsize(spells_tex_path) == 0:
        print("Error: spells.tex was not generated or is empty")
        return False, 0, 0, 0
    
    # Parse the stderr output to get truncation statistics
    spells_truncated = 0
    spells_total = 0
    if result.stderr:
        # Look for the truncation statistics in stderr
        for line in result.stderr.split('\n'):
            if 'Had to truncate' in line and 'out of' in line:
                try:
                    # Parse: "Had to truncate X out of Y spells at Z characters."
                    parts = line.split()
                    spells_truncated = int(parts[3])
                    spells_total = int(parts[6])
                    break
                except (ValueError, IndexError):
                    pass
    
    print(f"✓ Generated {spells_tex_path}")
    return True, spells_total, spells_truncated, 0


def compile_latex(output_dir, latex_compiler='xelatex'):
    """Compile the LaTeX files in tex/ directory and copy PDFs to output directory."""
    print(f"Compiling LaTeX files using latexmk with {latex_compiler}...")
    
    # Check if required files exist in tex/ directory
    cards_tex = os.path.join('tex', 'cards.tex')
    printable_tex = os.path.join('tex', 'printable.tex')
    
    if not os.path.exists(cards_tex):
        print(f"Error: {cards_tex} not found")
        return False, 0
    
    if not os.path.exists(printable_tex):
        print(f"Error: {printable_tex} not found")
        return False, 0
    
    # Use latexmk to compile both files in tex/ directory
    print("Compiling LaTeX files...")
    cmd = f"latexmk -{latex_compiler} -shell-escape -cd tex/cards.tex tex/printable.tex"
    result = run_command(cmd, show_progress=True)
    if result is None:
        return False, 0
    
    # Check if PDFs were generated in tex/ directory
    tex_cards_pdf = os.path.join('tex', 'cards.pdf')
    tex_printable_pdf = os.path.join('tex', 'printable.pdf')
    
    if not os.path.exists(tex_cards_pdf):
        print("Error: cards.pdf was not generated in tex/ directory")
        return False, 0
    
    if not os.path.exists(tex_printable_pdf):
        print("Error: printable.pdf was not generated in tex/ directory")
        return False, 0
    
    # Move PDFs to output directory
    print("Moving PDF files to output directory...")
    output_cards_pdf = os.path.join(output_dir, 'cards.pdf')
    output_printable_pdf = os.path.join(output_dir, 'printable.pdf')
    
    try:
        shutil.move(tex_cards_pdf, output_cards_pdf)
        print(f"  Moved cards.pdf to {output_dir}")
    except OSError as e:
        print(f"Error moving cards.pdf: {e}")
        return False, 0
    
    try:
        shutil.move(tex_printable_pdf, output_printable_pdf)
        print(f"  Moved printable.pdf to {output_dir}")
    except OSError as e:
        print(f"Error moving printable.pdf: {e}")
        return False, 0
    
    print("✓ Generated and moved PDF files")
    return True, 2  # 2 PDF files: cards.pdf and printable.pdf


def clean_intermediate_files():
    """Clean up intermediate LaTeX files in tex/ directory."""
    print("Cleaning up intermediate files...")
    
    intermediate_extensions = ['.aux', '.log', '.out', '.toc', '.fdb_latexmk', '.fls', '.synctex.gz', '.xdv']
    
    for ext in intermediate_extensions:
        pattern = f"*{ext}"
        for file_path in Path('tex').glob(pattern):
            try:
                file_path.unlink()
                print(f"  Removed {file_path.name}")
            except OSError as e:
                print(f"  Warning: Could not remove {file_path.name}: {e}")
    
    print("✓ Cleanup complete")


def main():
    parser = argparse.ArgumentParser(
        description="Generate D&D spell cards in one go",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all spells
  python3 generate_cards.py

  # Generate from a custom spells file
  python3 generate_cards.py -i data/spells_expanded.json

  # Generate only wizard spells of levels 1-3
  python3 generate_cards.py -c wizard -l 1-3

  # Generate specific spells
  python3 generate_cards.py -n "Fireball" -n "Lightning Bolt"

  # Generate and clean up intermediate files
  python3 generate_cards.py --clean

  # Generate spells sorted by level
  python3 generate_cards.py --sort-by level

  # Skip LaTeX compilation (only generate spells.tex)
  python3 generate_cards.py --no-compile
        """
    )
    
    # Input file option
    parser.add_argument(
        "-i", "--input", type=str, default="data/spells.json",
        help="input JSON file containing spells data (default: data/spells.json)"
    )
    
    # Filter options (same as generate.py)
    parser.add_argument(
        "-c", "--class", type=str, action='append', dest='classes',
        help="only select spells for this class, can be used multiple times"
    )
    parser.add_argument(
        "-l", "--level", type=str, action='append', dest='levels',
        help="only select spells of a certain level, can be used multiple times and can contain a range such as '1-3'"
    )
    parser.add_argument(
        "-s", "--school", type=str, action='append', dest='schools',
        help="only select spells of a school, can be used multiple times"
    )
    parser.add_argument(
        "-n", "--name", type=str, action='append', dest='names',
        help="select spells with one of several given names"
    )
    parser.add_argument(
        "--sort-by", type=str, choices=['name', 'level'], default='name',
        help="sort spells by name (default) or by level (then by name)"
    )
    
    # Output options
    parser.add_argument(
        "-o", "--output", type=str, default="pdf",
        help="output directory (default: pdf/)"
    )
    
    # Processing options
    parser.add_argument(
        "--clean", action='store_true',
        help="clean up intermediate files after generation"
    )
    parser.add_argument(
        "--no-compile", action='store_true',
        help="skip LaTeX compilation (only generate spells.tex)"
    )
    parser.add_argument(
        "--latex-compiler", type=str, default="xelatex",
        help="LaTeX compiler to use with latexmk (default: xelatex)"
    )
    parser.add_argument(
        "--open", action='store_true',
        help="open the generated PDF in Preview (macOS only)"
    )

    args = parser.parse_args()
    
    # Always check if the input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)
    
    # Check dependencies unless we are skipping LaTeX compilation
    if not args.no_compile:
        if not check_dependencies(args.input):
            sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    print("D&D Spelldeck Generator")
    print("=" * 50)
    
    # Check LaTeX template files unless we are skipping compilation
    if not args.no_compile:
        if not ensure_tex_templates():
            print("Error: Required LaTeX template files not found")
            sys.exit(1)
    
    # Generate spells.tex
    success, spells_total, spells_truncated, _ = generate_spells_tex(args)
    if not success:
        print("Error: Failed to generate spells.tex")
        sys.exit(1)
    
    # Compile LaTeX files if requested
    pdf_files_generated = 0
    if not args.no_compile:
        success, pdf_files_generated = compile_latex(output_dir, args.latex_compiler)
        if not success:
            print("Error: Failed to compile LaTeX files")
            sys.exit(1)

        print("\n✓ Spell cards generated successfully!")
        print(f"  - Individual cards: {os.path.join(output_dir, 'cards.pdf')}")
        print(f"  - Printable sheets: {os.path.join(output_dir, 'printable.pdf')}")

        # Open the printable PDF in Preview on macOS if requested
        if args.open and sys.platform == 'darwin':
            printable_pdf_path = os.path.join(output_dir, 'printable.pdf')
            try:
                subprocess.run(['open', '-a', 'Preview', printable_pdf_path], check=False)
            except Exception as e:
                print(f"Note: Could not open PDF in Preview: {e}")
    else:
        print("\n✓ spells.tex generated successfully!")
        print(f"  - Output file: {os.path.join('tex', 'spells.tex')}")
        print("  - Run LaTeX compilation manually to generate PDFs")
    
    # Display statistics
    print(f"\n📊 Generation Statistics:")
    print(f"  - Spells processed: {spells_total}")
    if spells_truncated > 0:
        print(f"  - Text truncated: {spells_truncated} spells (text too long for cards)")
    else:
        print(f"  - Text truncated: None (all spells fit within card limits)")
    print(f"  - Output directory: {output_dir}")
    
    # Clean up intermediate files if requested
    if args.clean and not args.no_compile:
        clean_intermediate_files()
    
    print("\nDone!")


if __name__ == '__main__':
    main()
