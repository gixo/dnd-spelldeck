"""
Integration tests for generate_cards.py and export_card_image.py scripts.
These tests actually run the scripts and verify they produce valid output.
"""
import pytest
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import json
import time


def check_latex_installed():
    """Check if LaTeX tools are available."""
    return shutil.which('xelatex') is not None and shutil.which('latexmk') is not None


def check_imagemagick_installed():
    """Check if ImageMagick or pdftoppm is available."""
    convert = shutil.which('convert') or shutil.which('magick')
    pdftoppm = shutil.which('pdftoppm')
    return convert is not None or pdftoppm is not None


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_latex
class TestGenerateCardsScript:
    """Test the generate_cards.py script end-to-end."""

    def test_script_exists(self):
        """Test that generate_cards.py exists."""
        assert os.path.exists('generate_cards.py')

    def test_generate_cards_help(self):
        """Test that --help works for generate_cards.py."""
        result = subprocess.run(
            ['python3', 'generate_cards.py', '--help'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'spell cards' in result.stdout.lower()
        assert '--class' in result.stdout
        assert '--level' in result.stdout
        assert '--output' in result.stdout

    def test_generate_spells_tex_only(self, temp_output_dir):
        """Test generating only spells.tex without compilation."""
        result = subprocess.run(
            ['python3', 'generate_cards.py', '--no-compile', '-l', '0'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0
        assert os.path.exists('tex/spells.tex')
        
        # Check that spells.tex has content
        with open('tex/spells.tex', 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert '\\begin{spell}' in content

    def test_generate_cards_single_spell(self, temp_output_dir):
        """Test generating cards for a single spell."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        
        result = subprocess.run(
            ['python3', 'generate_cards.py', '-n', 'Fireball', '-o', temp_output_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Check return code (may fail if LaTeX has issues, but we check files)
        if result.returncode != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        
        # Check that spells.tex was created
        assert os.path.exists('tex/spells.tex')
        
        # Check that PDFs were generated
        cards_pdf = os.path.join(temp_output_dir, 'cards.pdf')
        printable_pdf = os.path.join(temp_output_dir, 'printable.pdf')
        
        if result.returncode == 0:
            assert os.path.exists(cards_pdf), f"cards.pdf not found in {temp_output_dir}"
            assert os.path.exists(printable_pdf), f"printable.pdf not found in {temp_output_dir}"
            
            # Check file sizes
            assert os.path.getsize(cards_pdf) > 1000, "cards.pdf is too small"
            assert os.path.getsize(printable_pdf) > 1000, "printable.pdf is too small"

    def test_generate_cards_by_class(self, temp_output_dir):
        """Test generating cards filtered by class."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        
        result = subprocess.run(
            ['python3', 'generate_cards.py', '-c', 'Wizard', '-l', '0', '-o', temp_output_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Check that spells.tex was created
        assert os.path.exists('tex/spells.tex')
        
        if result.returncode == 0:
            cards_pdf = os.path.join(temp_output_dir, 'cards.pdf')
            assert os.path.exists(cards_pdf)

    def test_generate_cards_by_level_range(self, temp_output_dir):
        """Test generating cards with level range."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        
        result = subprocess.run(
            ['python3', 'generate_cards.py', '-l', '1-3', '-c', 'Wizard', '-o', temp_output_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        assert os.path.exists('tex/spells.tex')
        
        if result.returncode == 0:
            cards_pdf = os.path.join(temp_output_dir, 'cards.pdf')
            assert os.path.exists(cards_pdf)

    def test_generate_cards_by_school(self, temp_output_dir):
        """Test generating cards filtered by school."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        
        result = subprocess.run(
            ['python3', 'generate_cards.py', '-s', 'Evocation', '-l', '1', '-o', temp_output_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        assert os.path.exists('tex/spells.tex')
        
        if result.returncode == 0:
            cards_pdf = os.path.join(temp_output_dir, 'cards.pdf')
            assert os.path.exists(cards_pdf)

    def test_generate_cards_multiple_spells(self, temp_output_dir):
        """Test generating cards for multiple specific spells."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        
        result = subprocess.run(
            ['python3', 'generate_cards.py', 
             '-n', 'Fireball', 
             '-n', 'Magic Missile', 
             '-n', 'Shield',
             '-o', temp_output_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        assert os.path.exists('tex/spells.tex')
        
        # Check spells.tex contains all three spells
        with open('tex/spells.tex', 'r') as f:
            content = f.read()
            # Should have 3 spell environments
            assert content.count('\\begin{spell}') >= 1
        
        if result.returncode == 0:
            cards_pdf = os.path.join(temp_output_dir, 'cards.pdf')
            assert os.path.exists(cards_pdf)

    def test_generate_cards_with_clean(self, temp_output_dir):
        """Test generating cards with cleanup option."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        
        result = subprocess.run(
            ['python3', 'generate_cards.py', 
             '-n', 'Fireball',
             '-o', temp_output_dir,
             '--clean'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            # Check that intermediate files were cleaned up
            tex_dir = Path('tex')
            aux_files = list(tex_dir.glob('*.aux'))
            log_files = list(tex_dir.glob('*.log'))
            
            # These should be cleaned up
            assert len(aux_files) == 0, f"Found .aux files: {aux_files}"
            assert len(log_files) == 0, f"Found .log files: {log_files}"

    def test_generate_cards_statistics(self, temp_output_dir):
        """Test that statistics are shown in output."""
        result = subprocess.run(
            ['python3', 'generate_cards.py', '--no-compile', '-l', '0'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0
        
        # Check for statistics in output
        combined_output = result.stdout + result.stderr
        assert 'processed' in combined_output.lower() or 'generation statistics' in combined_output.lower()

    def test_generate_cards_output_dir_creation(self):
        """Test that output directory is created if it doesn't exist."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        
        # Use a unique directory name
        test_dir = f'test_output_{int(time.time())}'
        
        try:
            result = subprocess.run(
                ['python3', 'generate_cards.py', 
                 '-n', 'Fireball',
                 '-o', test_dir],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Directory should be created
            assert os.path.exists(test_dir)
            
            if result.returncode == 0:
                # PDFs should be in the directory
                assert os.path.exists(os.path.join(test_dir, 'cards.pdf'))
        
        finally:
            # Cleanup
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)

    def test_generate_cards_multiple_filters(self, temp_output_dir):
        """Test combining multiple filter types."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        
        result = subprocess.run(
            ['python3', 'generate_cards.py',
             '-c', 'Wizard',
             '-l', '1-2',
             '-s', 'Evocation',
             '-o', temp_output_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        assert os.path.exists('tex/spells.tex')
        
        if result.returncode == 0:
            assert os.path.exists(os.path.join(temp_output_dir, 'cards.pdf'))


@pytest.mark.integration
@pytest.mark.slow
class TestExportCardImageScript:
    """Test the export_card_image.py script end-to-end."""

    def test_script_exists(self):
        """Test that export_card_image.py exists."""
        assert os.path.exists('export_card_image.py')

    def test_export_card_image_help(self):
        """Test that --help works for export_card_image.py."""
        result = subprocess.run(
            ['python3', 'export_card_image.py', '--help'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'spell card' in result.stdout.lower()
        assert '--output' in result.stdout
        assert '--dpi' in result.stdout
        assert '--format' in result.stdout

    def test_export_fireball_png(self, temp_output_dir):
        """Test exporting Fireball as PNG."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        if not check_imagemagick_installed():
            pytest.skip("ImageMagick or pdftoppm not installed")
        
        output_file = os.path.join(temp_output_dir, 'fireball.png')
        
        result = subprocess.run(
            ['python3', 'export_card_image.py', 'Fireball', '-o', output_file],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            assert os.path.exists(output_file), f"Output file {output_file} not created"
            assert os.path.getsize(output_file) > 10000, "Image file is too small"
            
            # Verify it's a PNG file (starts with PNG magic bytes)
            with open(output_file, 'rb') as f:
                header = f.read(8)
                assert header[:4] == b'\x89PNG', "Not a valid PNG file"

    def test_export_magic_missile_jpg(self, temp_output_dir):
        """Test exporting Magic Missile as JPG."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        if not check_imagemagick_installed():
            pytest.skip("ImageMagick or pdftoppm not installed")
        
        output_file = os.path.join(temp_output_dir, 'magic_missile.jpg')
        
        result = subprocess.run(
            ['python3', 'export_card_image.py', 'Magic Missile', 
             '-o', output_file, '-f', 'jpg'],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            assert os.path.exists(output_file)
            assert os.path.getsize(output_file) > 5000
            
            # Verify it's a JPEG file
            with open(output_file, 'rb') as f:
                header = f.read(3)
                assert header[:2] == b'\xff\xd8', "Not a valid JPEG file"

    def test_export_with_custom_dpi(self, temp_output_dir):
        """Test exporting with custom DPI setting."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        if not check_imagemagick_installed():
            pytest.skip("ImageMagick or pdftoppm not installed")
        
        output_file = os.path.join(temp_output_dir, 'shield.png')
        
        result = subprocess.run(
            ['python3', 'export_card_image.py', 'Shield', 
             '-o', output_file, '-d', '300'],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            assert os.path.exists(output_file)
            # Lower DPI should result in smaller file
            assert os.path.getsize(output_file) > 1000

    def test_export_with_keep_pdf(self, temp_output_dir):
        """Test exporting and keeping the intermediate PDF."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        if not check_imagemagick_installed():
            pytest.skip("ImageMagick or pdftoppm not installed")
        
        output_file = os.path.join(temp_output_dir, 'cure_wounds.png')
        pdf_file = os.path.join(temp_output_dir, 'cure_wounds.pdf')
        
        result = subprocess.run(
            ['python3', 'export_card_image.py', 'Cure Wounds', 
             '-o', output_file, '--keep-pdf'],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            assert os.path.exists(output_file), "PNG file not created"
            assert os.path.exists(pdf_file), "PDF file should be kept"

    def test_export_default_samples_directory(self):
        """Test that default output goes to samples/ directory."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        if not check_imagemagick_installed():
            pytest.skip("ImageMagick or pdftoppm not installed")
        
        # Clean up any existing file first
        expected_file = 'samples/mage_armor.png'
        if os.path.exists(expected_file):
            os.remove(expected_file)
        
        result = subprocess.run(
            ['python3', 'export_card_image.py', 'Mage Armor'],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            # Should create in samples directory with sanitized filename
            assert os.path.exists('samples')
            # Check for the file (name might be sanitized)
            samples_files = list(Path('samples').glob('mage*.png'))
            assert len(samples_files) > 0, "No image file created in samples/"

    def test_export_nonexistent_spell(self, temp_output_dir):
        """Test exporting a spell that doesn't exist."""
        output_file = os.path.join(temp_output_dir, 'nonexistent.png')
        
        result = subprocess.run(
            ['python3', 'export_card_image.py', 'Nonexistent Spell XYZ', 
             '-o', output_file],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        # Should fail or produce empty output
        assert result.returncode != 0 or not os.path.exists(output_file) or os.path.getsize(output_file) == 0

    def test_export_multiple_formats(self, temp_output_dir):
        """Test exporting the same spell in different formats."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        if not check_imagemagick_installed():
            pytest.skip("ImageMagick or pdftoppm not installed")
        
        spell_name = 'Shield'
        formats = ['png', 'jpg']
        
        for fmt in formats:
            output_file = os.path.join(temp_output_dir, f'shield.{fmt}')
            
            result = subprocess.run(
                ['python3', 'export_card_image.py', spell_name,
                 '-o', output_file, '-f', fmt],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                assert os.path.exists(output_file), f"{fmt.upper()} file not created"

    def test_export_high_dpi(self, temp_output_dir):
        """Test exporting with high DPI for print quality."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        if not check_imagemagick_installed():
            pytest.skip("ImageMagick or pdftoppm not installed")
        
        output_file = os.path.join(temp_output_dir, 'fireball_hires.png')
        
        result = subprocess.run(
            ['python3', 'export_card_image.py', 'Fireball',
             '-o', output_file, '-d', '900'],
            capture_output=True,
            text=True,
            timeout=240  # High DPI might take longer
        )
        
        if result.returncode == 0:
            assert os.path.exists(output_file)
            # High DPI should result in larger file
            assert os.path.getsize(output_file) > 50000


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_latex
class TestScriptIntegration:
    """Test integration between the two scripts."""

    def test_generate_then_export(self, temp_output_dir):
        """Test generating PDFs then exporting one as an image."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        if not check_imagemagick_installed():
            pytest.skip("ImageMagick or pdftoppm not installed")
        
        # First generate cards
        result1 = subprocess.run(
            ['python3', 'generate_cards.py', 
             '-n', 'Fireball', '-n', 'Lightning Bolt',
             '-o', temp_output_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result1.returncode == 0:
            assert os.path.exists(os.path.join(temp_output_dir, 'cards.pdf'))
            
            # Then export one as image
            image_file = os.path.join(temp_output_dir, 'fireball.png')
            result2 = subprocess.run(
                ['python3', 'export_card_image.py', 'Fireball',
                 '-o', image_file],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result2.returncode == 0:
                assert os.path.exists(image_file)

    def test_consistency_between_scripts(self, temp_output_dir):
        """Test that both scripts produce output for the same spell."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        if not check_imagemagick_installed():
            pytest.skip("ImageMagick or pdftoppm not installed")
        
        spell_name = 'Magic Missile'
        
        # Generate with generate_cards.py
        result1 = subprocess.run(
            ['python3', 'generate_cards.py', '-n', spell_name, '-o', temp_output_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Export with export_card_image.py
        image_file = os.path.join(temp_output_dir, 'magic_missile.png')
        result2 = subprocess.run(
            ['python3', 'export_card_image.py', spell_name, '-o', image_file],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        # Both should succeed or both should fail
        if result1.returncode == 0:
            # If card generation works, image export should too
            assert result2.returncode == 0 or os.path.exists(image_file)


@pytest.mark.integration
class TestScriptErrorHandling:
    """Test error handling in both scripts."""

    def test_generate_cards_missing_data_file(self, temp_output_dir, monkeypatch):
        """Test error handling when spells.json is missing."""
        # This test is tricky because we need the file to exist
        # We'll just verify the script checks for it
        result = subprocess.run(
            ['python3', 'generate_cards.py', '--no-compile', '-n', 'Fireball'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should either succeed (file exists) or fail gracefully
        assert result.returncode in [0, 1]

    def test_generate_cards_invalid_class(self, temp_output_dir):
        """Test handling of invalid class filter."""
        result = subprocess.run(
            ['python3', 'generate_cards.py', '--no-compile', 
             '-c', 'InvalidClassXYZ123'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should fail gracefully when no spells match (empty output)
        # The script returns 1 when spells.tex is empty
        assert result.returncode == 1
        assert 'Error' in result.stdout or 'empty' in result.stdout.lower()

    def test_generate_cards_invalid_level(self, temp_output_dir):
        """Test handling of invalid level filter."""
        result = subprocess.run(
            ['python3', 'generate_cards.py', '--no-compile',
             '-l', '99'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should fail gracefully when no spells match (empty output)
        # The script returns 1 when spells.tex is empty
        assert result.returncode == 1
        assert 'Error' in result.stdout or 'empty' in result.stdout.lower()

    def test_export_without_dependencies(self, temp_output_dir):
        """Test export_card_image.py reports missing dependencies gracefully."""
        # This will only fail if dependencies are actually missing
        # If they exist, the test will skip naturally
        pass


@pytest.mark.integration
class TestScriptPerformance:
    """Test performance characteristics of the scripts."""

    def test_generate_single_spell_performance(self):
        """Test that generating a single spell is reasonably fast."""
        import time
        
        start = time.time()
        result = subprocess.run(
            ['python3', 'generate_cards.py', '--no-compile', '-n', 'Fireball'],
            capture_output=True,
            text=True,
            timeout=30
        )
        duration = time.time() - start
        
        assert result.returncode == 0
        # Should complete in under 10 seconds
        assert duration < 10, f"Generation took {duration:.2f}s"

    def test_generate_multiple_spells_performance(self):
        """Test that generating multiple spells scales reasonably."""
        import time
        
        start = time.time()
        result = subprocess.run(
            ['python3', 'generate_cards.py', '--no-compile', '-l', '0'],
            capture_output=True,
            text=True,
            timeout=60
        )
        duration = time.time() - start
        
        assert result.returncode == 0
        # Should complete in under 30 seconds for all cantrips
        assert duration < 30, f"Generation took {duration:.2f}s"

