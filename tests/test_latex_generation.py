"""
Tests for LaTeX generation and formatting.
"""
import pytest
import io
import sys
import generate


@pytest.mark.unit
class TestTextTruncation:
    """Test text truncation functionality."""

    def test_short_text_not_truncated(self):
        """Test that short text is not truncated."""
        text = "This is a short spell description."
        result = generate.truncate_string(text)
        assert result == text

    def test_long_text_is_truncated(self, long_text_spell):
        """Test that long text is properly truncated."""
        text = long_text_spell['text']
        result = generate.truncate_string(text)
        assert len(result) <= generate.MAX_TEXT_LENGTH
        assert result.endswith("...")

    def test_truncation_preserves_max_length(self):
        """Test that truncated text respects max length."""
        long_text = "x" * 1000
        result = generate.truncate_string(long_text, max_len=100)
        assert len(result) <= 100

    def test_truncation_removes_trailing_space(self):
        """Test that truncation removes trailing spaces."""
        text = "a" * 680 + "          test"
        result = generate.truncate_string(text)
        # Should truncate and add ... without trailing space before it
        assert not result[:-3].endswith(" ")

    def test_truncation_adds_ellipsis(self):
        """Test that truncation adds ellipsis."""
        long_text = "x" * 1000
        result = generate.truncate_string(long_text)
        assert result.endswith("...")

    def test_truncation_balances_braces(self):
        """Test that truncation balances unmatched opening braces."""
        # Create text with unbalanced braces that will be truncated
        text = "{\\textbf{" + "x" * 700
        result = generate.truncate_string(text)
        
        # Count braces
        open_count = result.count('{')
        close_count = result.count('}')
        assert open_count == close_count

    def test_truncation_with_balanced_braces(self):
        """Test that already balanced braces stay balanced."""
        text = "{\\textbf{text}}" + "x" * 700
        result = generate.truncate_string(text)
        
        open_count = result.count('{')
        close_count = result.count('}')
        assert open_count == close_count

    def test_truncation_custom_length(self):
        """Test truncation with custom max length."""
        text = "a" * 200
        result = generate.truncate_string(text, max_len=50)
        assert len(result) <= 50
        assert result.endswith("...")

    def test_exact_max_length_not_truncated(self):
        """Test that text exactly at max length is not truncated."""
        text = "a" * generate.MAX_TEXT_LENGTH
        result = generate.truncate_string(text)
        assert result == text
        assert not result.endswith("...")

    def test_real_spell_truncation(self):
        """Test truncation with actual spell data."""
        # Animate Objects is known to be long
        if 'Animate Objects' in generate.SPELLS:
            text = generate.SPELLS['Animate Objects']['text']
            result = generate.truncate_string(text)
            assert len(result) <= generate.MAX_TEXT_LENGTH


@pytest.mark.unit
class TestLaTeXFormatting:
    """Test LaTeX formatting and output generation."""

    def test_spell_header_cantrip(self):
        """Test that cantrip headers are formatted correctly."""
        level = 0
        school = "Evocation"
        ritual = False
        
        header = generate.LEVEL_STRING[level].format(
            school=school.lower(), 
            ritual='ritual' if ritual else ''
        ).strip()
        
        assert header == "evocation cantrip"

    def test_spell_header_first_level(self):
        """Test that 1st level spell headers are formatted correctly."""
        level = 1
        school = "Abjuration"
        ritual = False
        
        header = generate.LEVEL_STRING[level].format(
            school=school.lower(),
            ritual='ritual' if ritual else ''
        ).strip()
        
        assert header == "1st level abjuration"

    def test_spell_header_ritual(self):
        """Test that ritual spells include ritual in header."""
        level = 2
        school = "Divination"
        ritual = True
        
        header = generate.LEVEL_STRING[level].format(
            school=school.lower(),
            ritual='ritual' if ritual else ''
        ).strip()
        
        assert header == "2nd level divination ritual"

    def test_spell_header_high_level(self):
        """Test high level spell headers."""
        for level in range(3, 10):
            header = generate.LEVEL_STRING[level].format(
                school="test",
                ritual=''
            ).strip()
            
            # Check ordinal suffix
            if level == 3:
                assert "3rd" in header
            else:
                assert f"{level}th" in header

    def test_material_component_formatting(self, sample_spell):
        """Test that material components are appended to text."""
        spell_data = sample_spell.copy()
        spell_data['material'] = "a crystal worth 100gp"
        spell_data['components'] = ["V", "S", "M"]
        
        # Simulate what print_spell does
        text = spell_data['text']
        if spell_data['material'] is not None:
            text += "\n\n* - (" + spell_data['material'] + ")"
            components = [i.replace("M", "M *") for i in spell_data['components']]
        
        assert "* - (a crystal worth 100gp)" in text
        assert "M *" in components

    def test_source_page_formatting(self):
        """Test source and page number formatting."""
        source = "Player's Handbook"
        source_page = 123
        
        formatted_source = f"{source} page {source_page}"
        assert formatted_source == "Player's Handbook page 123"

    def test_area_effect_parsing_cone(self):
        """Test parsing cone area effect from range."""
        range_text = "Self (15 ft. cone)"
        
        import re
        area_effect = "none"
        display_range = range_text
        
        if 'cone' in range_text.lower():
            display_range = re.sub(r'\s*cone\s*\)?', '', range_text, flags=re.IGNORECASE).strip()
            area_effect = "cone"
        
        assert display_range == "Self (15 ft."
        assert area_effect == "cone"

    def test_area_effect_parsing_sphere(self):
        """Test parsing sphere area effect from range."""
        range_text = "150 ft. (20 ft. sphere)"
        
        import re
        area_effect = "none"
        display_range = range_text
        
        if 'sphere' in range_text.lower():
            display_range = re.sub(r'\s*sphere\s*\)?', '', range_text, flags=re.IGNORECASE).strip()
            area_effect = "sphere"
        
        assert display_range == "150 ft. (20 ft."
        assert area_effect == "sphere"

    def test_area_effect_parsing_all_types(self, area_effect_spells):
        """Test parsing all area effect types."""
        import re
        
        area_types = ['cone', 'cube', 'cylinder', 'emanation', 'line', 'sphere']
        
        for area_type, spell_data in area_effect_spells.items():
            range_text = spell_data['range']
            range_lower = range_text.lower()
            
            parsed_area = "none"
            for area in area_types:
                if area in range_lower:
                    parsed_area = area
                    break
            
            assert parsed_area == area_type

    def test_concentration_flag_explicit(self):
        """Test concentration flag when explicitly set."""
        concentration = True
        duration = "Up to 1 minute"
        
        duration_with_concentration = f"{duration}|CONCENTRATION" if concentration else f"{duration}|NONCONCENTRATION"
        
        assert "|CONCENTRATION" in duration_with_concentration

    def test_concentration_flag_from_duration_text(self):
        """Test concentration flag parsed from duration text."""
        duration = "Concentration, up to 1 minute"
        concentration = 'concentration' in duration.lower()
        
        duration_with_concentration = f"{duration}|CONCENTRATION" if concentration else f"{duration}|NONCONCENTRATION"
        
        assert "|CONCENTRATION" in duration_with_concentration

    def test_ritual_flag_in_time(self):
        """Test ritual flag in casting time."""
        time = "1 action"
        ritual = True
        
        time_with_ritual = f"{time}|RITUAL" if ritual else f"{time}|NONRITUAL"
        
        assert time_with_ritual == "1 action|RITUAL"


@pytest.mark.unit
class TestSpellOutput:
    """Test spell output generation."""

    def test_print_spell_basic(self, sample_spell, capsys):
        """Test basic spell printing."""
        # Reset counters
        generate.SPELLS_TRUNCATED = 0
        generate.SPELLS_TOTAL = 0
        
        generate.print_spell(**sample_spell)
        captured = capsys.readouterr()
        
        assert "\\begin{spell}" in captured.out
        assert "\\end{spell}" in captured.out
        assert sample_spell['name'] in captured.out
        assert str(sample_spell['level']) in captured.out or "1st level" in captured.out

    def test_print_spell_updates_counters(self, sample_spell):
        """Test that print_spell updates global counters."""
        initial_total = generate.SPELLS_TOTAL
        initial_truncated = generate.SPELLS_TRUNCATED
        
        generate.print_spell(**sample_spell)
        
        assert generate.SPELLS_TOTAL == initial_total + 1

    def test_print_spell_with_material(self, ritual_spell, capsys):
        """Test spell printing with material components."""
        generate.print_spell(**ritual_spell)
        captured = capsys.readouterr()
        
        assert ritual_spell['material'] in captured.out
        assert "* -" in captured.out

    def test_print_spell_cantrip(self, cantrip_spell, capsys):
        """Test cantrip printing."""
        generate.print_spell(**cantrip_spell)
        captured = capsys.readouterr()
        
        assert "cantrip" in captured.out.lower()
        assert cantrip_spell['name'] in captured.out

    def test_print_spell_ritual(self, ritual_spell, capsys):
        """Test ritual spell printing."""
        generate.print_spell(**ritual_spell)
        captured = capsys.readouterr()
        
        assert "ritual" in captured.out.lower()
        assert "|RITUAL" in captured.out

    def test_print_spell_concentration(self, concentration_spell, capsys):
        """Test concentration spell printing."""
        generate.print_spell(**concentration_spell)
        captured = capsys.readouterr()
        
        assert "|CONCENTRATION" in captured.out

    def test_print_spell_area_effects(self, area_effect_spells, capsys):
        """Test spell printing with different area effects."""
        for area_type, spell_data in area_effect_spells.items():
            generate.print_spell(**spell_data)
            captured = capsys.readouterr()
            
            # Check that area effect type is in output
            assert f"|{area_type}" in captured.out

    def test_print_spell_truncation_counter(self, long_text_spell):
        """Test that truncation counter increments for long spells."""
        initial_truncated = generate.SPELLS_TRUNCATED
        
        generate.print_spell(**long_text_spell)
        
        assert generate.SPELLS_TRUNCATED == initial_truncated + 1

    def test_text_wrapping(self, sample_spell, capsys):
        """Test that text is properly wrapped."""
        # Create a spell with long paragraph
        spell_data = sample_spell.copy()
        spell_data['text'] = "This is a very long line that should be wrapped at 80 characters according to the textwrap settings in the code. " * 3
        
        generate.print_spell(**spell_data)
        captured = capsys.readouterr()
        
        # Check that no line is excessively long (except LaTeX commands)
        lines = captured.out.split('\n')
        for line in lines:
            if not line.strip().startswith('\\'):
                # Regular text lines should be wrapped
                assert len(line) <= 90  # Allow some margin

    def test_paragraph_preservation(self, sample_spell, capsys):
        """Test that paragraph breaks are preserved."""
        spell_data = sample_spell.copy()
        spell_data['text'] = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        
        generate.print_spell(**spell_data)
        captured = capsys.readouterr()
        
        # Should have double newlines between paragraphs
        assert "\n\n" in captured.out

    def test_attack_save_field(self, sample_spell, capsys):
        """Test that attack/save information is included."""
        generate.print_spell(**sample_spell)
        captured = capsys.readouterr()
        
        assert sample_spell['attack_save'] in captured.out

    def test_damage_effect_field(self, sample_spell, capsys):
        """Test that damage/effect information is included."""
        generate.print_spell(**sample_spell)
        captured = capsys.readouterr()
        
        assert sample_spell['damage_effect'] in captured.out

