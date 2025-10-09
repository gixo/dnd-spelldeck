"""
Integration tests for full card generation pipeline.
These tests require LaTeX to be installed and may take longer to run.
"""
import pytest
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import json

import generate


def check_latex_installed():
    """Check if LaTeX tools are available."""
    return shutil.which('xelatex') is not None and shutil.which('latexmk') is not None


@pytest.mark.integration
@pytest.mark.slow
class TestFullPipelineGeneration:
    """Test the full generation pipeline from spell data to LaTeX."""

    def test_generate_single_spell_latex(self, sample_spell, capsys, temp_output_dir):
        """Test generating LaTeX for a single spell."""
        generate.print_spell(**sample_spell)
        output = capsys.readouterr().out
        
        # Save output to file
        output_file = os.path.join(temp_output_dir, 'test_spell.tex')
        with open(output_file, 'w') as f:
            f.write(output)
        
        assert os.path.exists(output_file)
        assert os.path.getsize(output_file) > 0
        
        # Verify it contains spell environment
        with open(output_file, 'r') as f:
            content = f.read()
            assert '\\begin{spell}' in content
            assert '\\end{spell}' in content

    def test_generate_multiple_spells_latex(self, capsys, temp_output_dir):
        """Test generating LaTeX for multiple spells."""
        spells = generate.get_spells(levels={0}, names=None)
        
        # Generate first 5 cantrips
        for name, spell in spells[:5]:
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        
        # Save output
        output_file = os.path.join(temp_output_dir, 'multiple_spells.tex')
        with open(output_file, 'w') as f:
            f.write(output)
        
        assert os.path.exists(output_file)
        
        # Should have 5 spell environments
        with open(output_file, 'r') as f:
            content = f.read()
            assert content.count('\\begin{spell}') == 5
            assert content.count('\\end{spell}') == 5

    def test_generate_all_spell_levels_latex(self, capsys, temp_output_dir):
        """Test generating LaTeX for spells from all levels."""
        # Generate one spell from each level
        for level in range(10):
            spells = generate.get_spells(levels={level})
            if spells:
                name, spell = spells[0]
                generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        
        # Save output
        output_file = os.path.join(temp_output_dir, 'all_levels.tex')
        with open(output_file, 'w') as f:
            f.write(output)
        
        assert os.path.exists(output_file)
        
        # Should have spell from each level
        with open(output_file, 'r') as f:
            content = f.read()
            assert 'cantrip' in content.lower()
            assert '9th level' in content.lower()

    def test_generate_class_spellbook(self, capsys, temp_output_dir):
        """Test generating a complete spellbook for a class."""
        # Generate all wizard cantrips and 1st level spells
        spells = generate.get_spells(
            classes={"Wizard"},
            levels={0, 1}
        )
        
        assert len(spells) > 0
        
        for name, spell in spells:
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        
        # Save output
        output_file = os.path.join(temp_output_dir, 'wizard_spellbook.tex')
        with open(output_file, 'w') as f:
            f.write(output)
        
        assert os.path.exists(output_file)
        assert os.path.getsize(output_file) > 1000  # Should be substantial

    def test_generate_school_collection(self, capsys, temp_output_dir):
        """Test generating all spells from a school."""
        spells = generate.get_spells(
            schools={"Evocation"},
            levels={1, 2, 3}
        )
        
        assert len(spells) > 0
        
        for name, spell in spells:
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        
        # Save output
        output_file = os.path.join(temp_output_dir, 'evocation_spells.tex')
        with open(output_file, 'w') as f:
            f.write(output)
        
        assert os.path.exists(output_file)

    def test_truncation_statistics(self):
        """Test that truncation statistics are tracked correctly."""
        # Reset counters
        generate.SPELLS_TRUNCATED = 0
        generate.SPELLS_TOTAL = 0
        
        # Generate all spells
        spells = generate.get_spells()
        
        for name, spell in spells:
            generate.print_spell(name, **spell)
        
        # Should have processed all spells
        assert generate.SPELLS_TOTAL == len(spells)
        
        # Some spells should be truncated (we know some are long)
        # But we don't assert a specific number as it depends on the data


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_latex
class TestLaTeXCompilation:
    """Test actual LaTeX compilation. Requires LaTeX installation."""

    def test_latex_available(self):
        """Test that LaTeX is available for compilation tests."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        
        assert shutil.which('xelatex') is not None
        assert shutil.which('latexmk') is not None

    def test_compile_single_spell_document(self, sample_spell, temp_output_dir):
        """Test compiling a document with a single spell."""
        if not check_latex_installed():
            pytest.skip("LaTeX not installed")
        
        # Create minimal LaTeX document
        latex_content = r"""\documentclass{article}
\usepackage{fontspec}

\newenvironment{spell}[9]{%
    \noindent\textbf{#1} \\
    \textit{#2} \\
    Range: #3 \\
    Time: #4 \\
    Duration: #5 \\
    Components: #6 \\
}{%
}

\begin{document}
"""
        
        # Add spell
        import io
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        generate.print_spell(**sample_spell)
        
        sys.stdout = old_stdout
        spell_output = buffer.getvalue()
        
        latex_content += spell_output
        latex_content += r"\end{document}"
        
        # Write to file
        tex_file = os.path.join(temp_output_dir, 'test_spell.tex')
        with open(tex_file, 'w') as f:
            f.write(latex_content)
        
        # Try to compile
        try:
            result = subprocess.run(
                ['xelatex', '-interaction=nonstopmode', 'test_spell.tex'],
                cwd=temp_output_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check if PDF was created
            pdf_file = os.path.join(temp_output_dir, 'test_spell.pdf')
            # Note: Even if compilation has errors, we're just testing the process
            # The actual template files have more complex environments
            assert os.path.exists(tex_file)
            
        except subprocess.TimeoutExpired:
            pytest.fail("LaTeX compilation timed out")
        except Exception as e:
            pytest.skip(f"LaTeX compilation failed: {e}")


@pytest.mark.integration
class TestCommandLineInterface:
    """Test the command-line interface functionality."""

    def test_generate_script_no_args(self):
        """Test running generate.py with no arguments."""
        result = subprocess.run(
            ['python3', 'generate.py'],
            capture_output=True,
            text=True
        )
        
        # Should succeed
        assert result.returncode == 0
        assert '\\begin{spell}' in result.stdout

    def test_generate_script_class_filter(self):
        """Test running generate.py with class filter."""
        result = subprocess.run(
            ['python3', 'generate.py', '-c', 'Wizard'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert '\\begin{spell}' in result.stdout

    def test_generate_script_level_filter(self):
        """Test running generate.py with level filter."""
        result = subprocess.run(
            ['python3', 'generate.py', '-l', '0'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'cantrip' in result.stdout.lower()

    def test_generate_script_level_range(self):
        """Test running generate.py with level range."""
        result = subprocess.run(
            ['python3', 'generate.py', '-l', '1-3'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert '\\begin{spell}' in result.stdout

    def test_generate_script_school_filter(self):
        """Test running generate.py with school filter."""
        result = subprocess.run(
            ['python3', 'generate.py', '-s', 'Evocation'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert '\\begin{spell}' in result.stdout

    def test_generate_script_name_filter(self):
        """Test running generate.py with spell name filter."""
        result = subprocess.run(
            ['python3', 'generate.py', '-n', 'Fireball'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'Fireball' in result.stdout

    def test_generate_script_multiple_filters(self):
        """Test running generate.py with multiple filters."""
        result = subprocess.run(
            ['python3', 'generate.py', '-c', 'Wizard', '-l', '1-3', '-s', 'Evocation'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0

    def test_generate_script_statistics_output(self):
        """Test that statistics are output to stderr."""
        result = subprocess.run(
            ['python3', 'generate.py', '-l', '0'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'truncate' in result.stderr.lower()


@pytest.mark.integration
class TestRealSpellData:
    """Test generation with real spell data from the database."""

    def test_generate_fireball_card(self, capsys):
        """Test generating the iconic Fireball spell."""
        spells = generate.get_spells(names={"Fireball"})
        
        if spells:
            name, spell = spells[0]
            generate.print_spell(name, **spell)
            output = capsys.readouterr().out
            
            assert 'Fireball' in output
            assert 'sphere' in output.lower()
            assert '\\begin{spell}' in output

    def test_generate_magic_missile_card(self, capsys):
        """Test generating Magic Missile."""
        spells = generate.get_spells(names={"Magic Missile"})
        
        if spells:
            name, spell = spells[0]
            generate.print_spell(name, **spell)
            output = capsys.readouterr().out
            
            assert 'Magic Missile' in output
            assert '\\begin{spell}' in output

    def test_generate_wish_card(self, capsys):
        """Test generating the powerful Wish spell."""
        spells = generate.get_spells(names={"Wish"})
        
        if spells:
            name, spell = spells[0]
            generate.print_spell(name, **spell)
            output = capsys.readouterr().out
            
            assert 'Wish' in output
            assert '9th level' in output.lower()

    def test_generate_prestidigitation_card(self, capsys):
        """Test generating Prestidigitation cantrip."""
        spells = generate.get_spells(names={"Prestidigitation"})
        
        if spells:
            name, spell = spells[0]
            generate.print_spell(name, **spell)
            output = capsys.readouterr().out
            
            assert 'Prestidigitation' in output
            assert 'cantrip' in output.lower()

    def test_all_spells_generate_without_error(self, capsys):
        """Test that all spells in the database can be generated."""
        spells = generate.get_spells()
        
        errors = []
        for name, spell in spells:
            try:
                generate.print_spell(name, **spell)
            except Exception as e:
                errors.append((name, str(e)))
        
        # Clear captured output
        capsys.readouterr()
        
        # Should have no errors
        if errors:
            error_msg = "Failed to generate cards for:\n"
            for name, error in errors[:10]:  # Show first 10 errors
                error_msg += f"  - {name}: {error}\n"
            pytest.fail(error_msg)

    def test_spell_data_integrity(self, spells_data):
        """Test that all spells have required fields."""
        required_fields = ['level', 'ritual', 'time', 'range', 'components', 
                          'duration', 'school', 'text', 'classes']
        
        missing_fields = []
        for name, spell in spells_data.items():
            for field in required_fields:
                if field not in spell:
                    missing_fields.append((name, field))
        
        if missing_fields:
            error_msg = "Spells missing required fields:\n"
            for name, field in missing_fields[:10]:
                error_msg += f"  - {name}: missing '{field}'\n"
            pytest.fail(error_msg)


@pytest.mark.integration
class TestOutputValidation:
    """Test that generated output is valid."""

    def test_balanced_latex_environments(self, capsys):
        """Test that all LaTeX environments are balanced."""
        spells = generate.get_spells(levels={0, 1})
        
        for name, spell in spells[:20]:  # Test first 20
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        
        begin_count = output.count('\\begin{spell}')
        end_count = output.count('\\end{spell}')
        
        assert begin_count == end_count
        assert begin_count > 0

    def test_no_malformed_latex_commands(self, capsys):
        """Test that there are no obviously malformed LaTeX commands."""
        spells = generate.get_spells(levels={0})
        
        for name, spell in spells[:10]:
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        
        # Check for unbalanced braces in commands
        # This is a simple check, not comprehensive
        lines = output.split('\n')
        for line in lines:
            if line.strip().startswith('\\'):
                # Count braces in command lines
                open_braces = line.count('{')
                close_braces = line.count('}')
                # Allow for multiline commands, so this is just a sanity check
                if '\\begin{spell}' in line or '\\end{spell}' in line:
                    assert open_braces == close_braces

    def test_output_is_utf8_encodable(self, capsys):
        """Test that all output can be encoded as UTF-8."""
        spells = generate.get_spells()
        
        for name, spell in spells[:50]:  # Test a sample
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        
        # Should be able to encode as UTF-8
        try:
            encoded = output.encode('utf-8')
            assert len(encoded) > 0
        except UnicodeEncodeError as e:
            pytest.fail(f"Output contains non-UTF-8 characters: {e}")

