"""
Tests for card generation with different spell types and combinations.
"""
import pytest
import io
import sys
import os
import generate


@pytest.mark.unit
class TestCardGenerationBySpellType:
    """Test card generation for different spell types."""

    def test_generate_cantrip_card(self, cantrip_spell, capsys):
        """Test generating a card for a cantrip."""
        generate.print_spell(**cantrip_spell)
        output = capsys.readouterr().out
        
        assert "\\begin{spell}" in output
        assert cantrip_spell['name'] in output
        assert "cantrip" in output.lower()
        assert "0" in output or "cantrip" in output.lower()

    def test_generate_first_level_card(self, sample_spell, capsys):
        """Test generating a card for a 1st level spell."""
        generate.print_spell(**sample_spell)
        output = capsys.readouterr().out
        
        assert "\\begin{spell}" in output
        assert sample_spell['name'] in output
        assert "1st level" in output.lower()

    def test_generate_high_level_card(self, capsys):
        """Test generating a card for a high level spell."""
        spell = {
            "name": "Ninth Level Test",
            "level": 9,
            "ritual": False,
            "time": "1 action",
            "range": "Unlimited",
            "components": ["V", "S"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Transmutation",
            "attack_save": "None",
            "damage_effect": "Reality",
            "text": "Reality bends to your will.",
            "material": None,
            "classes": ["Wizard"],
            "source": "Test",
            "source_page": 1
        }
        
        generate.print_spell(**spell)
        output = capsys.readouterr().out
        
        assert "9th level" in output.lower()

    def test_generate_ritual_card(self, ritual_spell, capsys):
        """Test generating a card for a ritual spell."""
        generate.print_spell(**ritual_spell)
        output = capsys.readouterr().out
        
        assert "ritual" in output.lower()
        assert "|RITUAL" in output
        assert ritual_spell['material'] in output

    def test_generate_concentration_card(self, concentration_spell, capsys):
        """Test generating a card for a concentration spell."""
        generate.print_spell(**concentration_spell)
        output = capsys.readouterr().out
        
        assert "|CONCENTRATION" in output
        assert concentration_spell['name'] in output

    def test_generate_ritual_concentration_card(self, capsys):
        """Test generating a card for a spell that is both ritual and concentration."""
        spell = {
            "name": "Ritual Concentration Test",
            "level": 3,
            "ritual": True,
            "time": "10 minutes",
            "range": "Self",
            "components": ["V", "S", "M"],
            "concentration": True,
            "duration": "Concentration, up to 1 hour",
            "school": "Divination",
            "attack_save": "None",
            "damage_effect": "Detection",
            "text": "You enter a trance to detect magical auras.",
            "material": "incense worth 50gp",
            "classes": ["Wizard", "Cleric"],
            "source": "Test",
            "source_page": 1
        }
        
        generate.print_spell(**spell)
        output = capsys.readouterr().out
        
        assert "|RITUAL" in output
        assert "|CONCENTRATION" in output

    def test_generate_material_component_card(self, capsys):
        """Test generating a card with material components."""
        spell = {
            "name": "Material Test",
            "level": 2,
            "ritual": False,
            "time": "1 action",
            "range": "Touch",
            "components": ["V", "S", "M"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Transmutation",
            "attack_save": "None",
            "damage_effect": "Buff",
            "text": "You enhance an object.",
            "material": "diamond dust worth 100gp, which the spell consumes",
            "classes": ["Wizard"],
            "source": "Test",
            "source_page": 1
        }
        
        generate.print_spell(**spell)
        output = capsys.readouterr().out
        
        assert "M *" in output
        assert spell['material'] in output
        assert "* -" in output


@pytest.mark.unit
class TestAreaEffectCards:
    """Test card generation for different area effects."""

    def test_generate_cone_effect_card(self, area_effect_spells, capsys):
        """Test generating a card with cone area effect."""
        generate.print_spell(**area_effect_spells['cone'])
        output = capsys.readouterr().out
        
        assert "|cone" in output
        assert "Cone Spell" in output

    def test_generate_sphere_effect_card(self, area_effect_spells, capsys):
        """Test generating a card with sphere area effect."""
        generate.print_spell(**area_effect_spells['sphere'])
        output = capsys.readouterr().out
        
        assert "|sphere" in output
        assert "Sphere Spell" in output

    def test_generate_cube_effect_card(self, area_effect_spells, capsys):
        """Test generating a card with cube area effect."""
        generate.print_spell(**area_effect_spells['cube'])
        output = capsys.readouterr().out
        
        assert "|cube" in output
        assert "Cube Spell" in output

    def test_generate_line_effect_card(self, area_effect_spells, capsys):
        """Test generating a card with line area effect."""
        generate.print_spell(**area_effect_spells['line'])
        output = capsys.readouterr().out
        
        assert "|line" in output
        assert "Line Spell" in output

    def test_generate_cylinder_effect_card(self, area_effect_spells, capsys):
        """Test generating a card with cylinder area effect."""
        generate.print_spell(**area_effect_spells['cylinder'])
        output = capsys.readouterr().out
        
        assert "|cylinder" in output
        assert "Cylinder Spell" in output

    def test_generate_emanation_effect_card(self, area_effect_spells, capsys):
        """Test generating a card with emanation area effect."""
        generate.print_spell(**area_effect_spells['emanation'])
        output = capsys.readouterr().out
        
        assert "|emanation" in output
        assert "Emanation Spell" in output

    def test_generate_no_area_effect_card(self, sample_spell, capsys):
        """Test generating a card with no area effect."""
        generate.print_spell(**sample_spell)
        output = capsys.readouterr().out
        
        assert "|none" in output


@pytest.mark.unit
class TestBatchCardGeneration:
    """Test generating multiple cards in various combinations."""

    def test_generate_all_cantrips(self, capsys):
        """Test generating all cantrip cards."""
        cantrips = generate.get_spells(levels={0})
        
        assert len(cantrips) > 0
        
        for name, spell in cantrips:
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        spell_count = output.count("\\begin{spell}")
        
        assert spell_count == len(cantrips)

    def test_generate_wizard_spells_level_1_to_3(self, capsys):
        """Test generating wizard spells levels 1-3."""
        spells = generate.get_spells(
            classes={"Wizard"},
            levels={1, 2, 3}
        )
        
        assert len(spells) > 0
        
        for name, spell in spells:
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        spell_count = output.count("\\begin{spell}")
        
        assert spell_count == len(spells)

    def test_generate_evocation_spells(self, capsys):
        """Test generating all evocation spells."""
        spells = generate.get_spells(schools={"Evocation"})
        
        assert len(spells) > 0
        
        for name, spell in spells:
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        spell_count = output.count("\\begin{spell}")
        
        assert spell_count == len(spells)

    def test_generate_multiclass_spells(self, capsys):
        """Test generating spells available to multiple classes."""
        spells = generate.get_spells(
            classes={"Wizard", "Sorcerer", "Warlock"}
        )
        
        assert len(spells) > 0
        
        for name, spell in spells:
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        spell_count = output.count("\\begin{spell}")
        
        assert spell_count == len(spells)

    def test_generate_specific_spell_list(self, capsys):
        """Test generating a specific list of spells."""
        spell_names = ["Fireball", "Lightning Bolt", "Magic Missile", "Shield"]
        spells = generate.get_spells(names=set(spell_names))
        
        # Some spells might not exist, so check what we got
        spell_count = len(spells)
        
        for name, spell in spells:
            generate.print_spell(name, **spell)
        
        output = capsys.readouterr().out
        latex_count = output.count("\\begin{spell}")
        
        assert latex_count == spell_count

    def test_generate_all_spell_levels(self, capsys):
        """Test generating spells from all levels 0-9."""
        for level in range(10):
            spells = generate.get_spells(levels={level})
            assert len(spells) > 0, f"No spells found for level {level}"

    def test_counter_tracking(self):
        """Test that spell counters are properly tracked."""
        # Reset counters
        generate.SPELLS_TRUNCATED = 0
        generate.SPELLS_TOTAL = 0
        
        # Generate some spells
        spells = generate.get_spells(levels={0, 1})
        
        for name, spell in spells[:10]:  # Just do 10 to be fast
            generate.print_spell(name, **spell)
        
        assert generate.SPELLS_TOTAL == 10
        assert generate.SPELLS_TRUNCATED >= 0


@pytest.mark.unit  
class TestEdgeCases:
    """Test edge cases in card generation."""

    def test_empty_text_spell(self, capsys):
        """Test spell with empty text."""
        spell = {
            "name": "Empty Text Test",
            "level": 1,
            "ritual": False,
            "time": "1 action",
            "range": "Touch",
            "components": ["V"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Transmutation",
            "attack_save": "None",
            "damage_effect": "None",
            "text": "",
            "material": None,
            "classes": ["Wizard"],
            "source": "Test",
            "source_page": 1
        }
        
        generate.print_spell(**spell)
        output = capsys.readouterr().out
        
        assert "\\begin{spell}" in output
        assert spell['name'] in output

    def test_spell_with_special_characters(self, capsys):
        """Test spell with special characters in name and text."""
        spell = {
            "name": "Test's \"Special\" Spell",
            "level": 1,
            "ritual": False,
            "time": "1 action",
            "range": "30 ft.",
            "components": ["V", "S"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Evocation",
            "attack_save": "None",
            "damage_effect": "None",
            "text": "This spell uses special characters: & % $ # @",
            "material": None,
            "classes": ["Wizard"],
            "source": "Test",
            "source_page": 1
        }
        
        generate.print_spell(**spell)
        output = capsys.readouterr().out
        
        assert "\\begin{spell}" in output

    def test_spell_with_latex_commands(self, capsys):
        """Test spell text that already contains LaTeX commands."""
        spell = {
            "name": "LaTeX Test",
            "level": 1,
            "ritual": False,
            "time": "1 action",
            "range": "Self",
            "components": ["V"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Transmutation",
            "attack_save": "None",
            "damage_effect": "None",
            "text": "This spell has {\\textbf{bold text}} and {\\textit{italic text}}.",
            "material": None,
            "classes": ["Wizard"],
            "source": "Test",
            "source_page": 1
        }
        
        generate.print_spell(**spell)
        output = capsys.readouterr().out
        
        assert "\\textbf{bold text}" in output
        assert "\\textit{italic text}" in output

    def test_spell_with_long_name(self, capsys):
        """Test spell with very long name."""
        spell = {
            "name": "This Is A Very Long Spell Name That Should Still Work Correctly",
            "level": 5,
            "ritual": False,
            "time": "1 action",
            "range": "60 ft.",
            "components": ["V", "S"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Evocation",
            "attack_save": "None",
            "damage_effect": "None",
            "text": "Long name test.",
            "material": None,
            "classes": ["Wizard"],
            "source": "Test",
            "source_page": 1
        }
        
        generate.print_spell(**spell)
        output = capsys.readouterr().out
        
        assert spell['name'] in output

    def test_spell_without_source(self, capsys):
        """Test spell without source information."""
        spell = {
            "name": "No Source Test",
            "level": 1,
            "ritual": False,
            "time": "1 action",
            "range": "Touch",
            "components": ["V"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Transmutation",
            "attack_save": "None",
            "damage_effect": "None",
            "text": "No source info.",
            "material": None,
            "classes": ["Wizard"]
        }
        
        generate.print_spell(**spell)
        output = capsys.readouterr().out
        
        assert "\\begin{spell}" in output

    def test_spell_with_all_components(self, capsys):
        """Test spell with all component types."""
        spell = {
            "name": "All Components Test",
            "level": 3,
            "ritual": False,
            "time": "1 action",
            "range": "60 ft.",
            "components": ["V", "S", "M"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Evocation",
            "attack_save": "DEX Save",
            "damage_effect": "Fire",
            "text": "All component types.",
            "material": "a pinch of sulfur",
            "classes": ["Wizard"],
            "source": "Test",
            "source_page": 1
        }
        
        generate.print_spell(**spell)
        output = capsys.readouterr().out
        
        assert "V" in output
        assert "S" in output
        assert "M *" in output
        assert spell['material'] in output

    def test_spell_with_only_verbal_component(self, capsys):
        """Test spell with only verbal component."""
        spell = {
            "name": "Verbal Only Test",
            "level": 0,
            "ritual": False,
            "time": "1 action",
            "range": "60 ft.",
            "components": ["V"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Enchantment",
            "attack_save": "WIS Save",
            "damage_effect": "Control",
            "text": "Verbal only.",
            "material": None,
            "classes": ["Bard"],
            "source": "Test",
            "source_page": 1
        }
        
        generate.print_spell(**spell)
        output = capsys.readouterr().out
        
        assert "V" in output
        assert "S" not in output or ", S" not in output

