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
    -c, --class CLASS     Filter by class (can be used multiple times)
    -l, --level LEVEL     Filter by level (can be used multiple times, supports ranges like 1-3)
    -s, --school SCHOOL   Filter by school (can be used multiple times)
    -n, --name NAME       Filter by spell name (can be used multiple times)
    -o, --output DIR      Output directory (default: tex/)
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


def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []
    
    # Check Python
    if sys.version_info < (3, 6):
        missing_deps.append("Python 3.6 or higher")
    
    # Check if generate.py exists
    if not os.path.exists('generate.py'):
        missing_deps.append("generate.py script")
    
    # Check if data/spells.json exists
    if not os.path.exists('data/spells.json'):
        missing_deps.append("data/spells.json file")
    
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


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    try:
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


def generate_spells_tex(args, output_dir):
    """Generate the spells.tex file using generate.py."""
    print("Generating spells.tex...")
    
    # Build the generate.py command
    cmd_parts = ['python3', 'generate.py']
    
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
            cmd_parts.extend(['-n', f'"{name}"'])
    
    # Run the command and redirect output to spells.tex
    cmd = ' '.join(cmd_parts)
    spells_tex_path = os.path.join(output_dir, 'spells.tex')
    
    result = run_command(f"{cmd} > {spells_tex_path}")
    if result is None:
        return False
    
    if not os.path.exists(spells_tex_path) or os.path.getsize(spells_tex_path) == 0:
        print("Error: spells.tex was not generated or is empty")
        return False
    
    print(f"✓ Generated {spells_tex_path}")
    return True


def compile_latex(output_dir, latex_compiler='xelatex'):
    """Compile the LaTeX files to generate PDFs using latexmk."""
    print(f"Compiling LaTeX files using latexmk with {latex_compiler}...")
    
    # Check if required files exist
    cards_tex = os.path.join(output_dir, 'cards.tex')
    printable_tex = os.path.join(output_dir, 'printable.tex')
    
    if not os.path.exists(cards_tex):
        print(f"Error: {cards_tex} not found")
        return False
    
    if not os.path.exists(printable_tex):
        print(f"Error: {printable_tex} not found")
        return False
    
    # Use latexmk to compile both files
    print("Compiling LaTeX files...")
    cmd = f"latexmk -{latex_compiler} -cd {cards_tex} {printable_tex}"
    result = run_command(cmd)
    if result is None:
        return False
    
    # Check if PDFs were generated
    cards_pdf = os.path.join(output_dir, 'cards.pdf')
    printable_pdf = os.path.join(output_dir, 'printable.pdf')
    
    if not os.path.exists(cards_pdf):
        print("Error: cards.pdf was not generated")
        return False
    
    if not os.path.exists(printable_pdf):
        print("Error: printable.pdf was not generated")
        return False
    
    print("✓ Generated cards.pdf")
    print("✓ Generated printable.pdf")
    return True


def clean_intermediate_files(output_dir):
    """Clean up intermediate LaTeX files."""
    print("Cleaning up intermediate files...")
    
    intermediate_extensions = ['.aux', '.log', '.out', '.toc', '.fdb_latexmk', '.fls', '.synctex.gz']
    
    for ext in intermediate_extensions:
        pattern = f"*{ext}"
        for file_path in Path(output_dir).glob(pattern):
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

  # Generate only wizard spells of levels 1-3
  python3 generate_cards.py -c wizard -l 1-3

  # Generate specific spells
  python3 generate_cards.py -n "Fireball" -n "Lightning Bolt"

  # Generate and clean up intermediate files
  python3 generate_cards.py --clean

  # Skip LaTeX compilation (only generate spells.tex)
  python3 generate_cards.py --no-compile
        """
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
    
    # Output options
    parser.add_argument(
        "-o", "--output", type=str, default="tex",
        help="output directory (default: tex/)"
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
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    print("D&D Spelldeck Generator")
    print("=" * 50)
    
    # Generate spells.tex
    if not generate_spells_tex(args, output_dir):
        print("Error: Failed to generate spells.tex")
        sys.exit(1)
    
    # Compile LaTeX files if requested
    if not args.no_compile:
        if not compile_latex(output_dir, args.latex_compiler):
            print("Error: Failed to compile LaTeX files")
            sys.exit(1)
        
        print("\n✓ Spell cards generated successfully!")
        print(f"  - Individual cards: {os.path.join(output_dir, 'cards.pdf')}")
        print(f"  - Printable sheets: {os.path.join(output_dir, 'printable.pdf')}")
    else:
        print("\n✓ spells.tex generated successfully!")
        print(f"  - Output file: {os.path.join(output_dir, 'spells.tex')}")
        print("  - Run LaTeX compilation manually to generate PDFs")
    
    # Clean up intermediate files if requested
    if args.clean and not args.no_compile:
        clean_intermediate_files(output_dir)
    
    print("\nDone!")


if __name__ == '__main__':
    main()
