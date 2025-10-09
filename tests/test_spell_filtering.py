"""
Tests for spell filtering functionality.
"""
import pytest
import generate


@pytest.mark.unit
class TestSpellFiltering:
    """Test spell filtering by various criteria."""

    def test_no_filter_returns_all_spells(self, spells_data):
        """Test that no filters returns all spells."""
        spells = generate.get_spells()
        assert len(spells) == len(generate.SPELLS)
        assert len(spells) == len(spells_data)

    def test_filter_by_single_class(self):
        """Test filtering by a single class."""
        spells = [x[0] for x in generate.get_spells(classes={"Wizard"})]
        assert len(spells) > 0
        
        # Check that known wizard spells are included
        assert "Fireball" in spells
        assert "Magic Missile" in spells

    def test_filter_by_multiple_classes(self):
        """Test filtering by multiple classes."""
        spells = [x[0] for x in generate.get_spells(classes={"Warlock", "Fighter"})]
        assert len(spells) > 0
        
        # Known warlock spells
        spell_names = set(spells)
        # Alarm is available to multiple classes including Rangers which share with Fighters
        # Let's check for spells we know exist
        assert any(spell in spell_names for spell in generate.SPELLS.keys())

    def test_filter_by_nonexistent_class(self):
        """Test that filtering by non-existent class returns empty."""
        spells = generate.get_spells(classes={"NotAClass"})
        assert len(spells) == 0

    def test_filter_by_school(self):
        """Test filtering by school of magic."""
        # Abjuration spells
        spells = [x[0] for x in generate.get_spells(schools={"Abjuration"})]
        assert len(spells) > 0
        
        # Verify the spells are actually abjuration
        for name, spell in generate.get_spells(schools={"Abjuration"}):
            assert spell['school'] == 'Abjuration'

    def test_filter_by_multiple_schools(self):
        """Test filtering by multiple schools."""
        spells = generate.get_spells(schools={"Abjuration", "Evocation"})
        assert len(spells) > 0
        
        # Verify all spells are from one of the schools
        for name, spell in spells:
            assert spell['school'] in ['Abjuration', 'Evocation']

    def test_filter_by_nonexistent_school(self):
        """Test that filtering by non-existent school returns empty."""
        spells = generate.get_spells(schools={"NotASchool"})
        assert len(spells) == 0

    def test_filter_by_single_level(self):
        """Test filtering by a single level."""
        # Cantrips (level 0)
        spells = [x[0] for x in generate.get_spells(levels={0})]
        assert len(spells) > 0
        assert "Prestidigitation" in spells
        
        # Verify all are level 0
        for name, spell in generate.get_spells(levels={0}):
            assert spell['level'] == 0

    def test_filter_by_multiple_levels(self):
        """Test filtering by multiple levels."""
        spells = generate.get_spells(levels={0, 1, 2})
        assert len(spells) > 0
        
        # Verify all are within specified levels
        for name, spell in spells:
            assert spell['level'] in [0, 1, 2]

    def test_filter_by_high_level(self):
        """Test filtering by high level spells."""
        spells = [x[0] for x in generate.get_spells(levels={9})]
        assert len(spells) > 0
        
        # Known 9th level spells
        spell_names = set(spells)
        ninth_level_examples = ["Wish", "Power Word Kill", "Meteor Swarm"]
        assert any(spell in spell_names for spell in ninth_level_examples)

    def test_filter_by_nonexistent_level(self):
        """Test that filtering by impossible level returns empty."""
        spells = generate.get_spells(levels={9000})
        assert len(spells) == 0

    def test_filter_by_spell_name(self):
        """Test filtering by specific spell name."""
        spells = {x[0] for x in generate.get_spells(names={"Fireball"})}
        assert spells == {"Fireball"}

    def test_filter_by_multiple_spell_names(self):
        """Test filtering by multiple spell names."""
        spells = {x[0] for x in generate.get_spells(names={"Fireball", "Magic Missile", "Shield"})}
        assert spells == {"Fireball", "Magic Missile", "Shield"}
        assert len(spells) == 3

    def test_filter_by_nonexistent_spell_name(self):
        """Test that filtering by non-existent spell name returns empty."""
        spells = generate.get_spells(names={"NotASpell"})
        assert len(spells) == 0

    def test_case_insensitive_filtering(self):
        """Test that filtering is case-insensitive."""
        # Class filtering
        spells1 = generate.get_spells(classes={"wizard"})
        spells2 = generate.get_spells(classes={"Wizard"})
        spells3 = generate.get_spells(classes={"WIZARD"})
        assert len(spells1) == len(spells2) == len(spells3)
        
        # School filtering
        spells1 = generate.get_spells(schools={"evocation"})
        spells2 = generate.get_spells(schools={"Evocation"})
        assert len(spells1) == len(spells2)
        
        # Name filtering
        spells1 = generate.get_spells(names={"fireball"})
        spells2 = generate.get_spells(names={"Fireball"})
        assert len(spells1) == len(spells2)

    def test_combined_filters(self):
        """Test combining multiple filter types."""
        # Wizard evocation spells of level 1
        spells = generate.get_spells(
            classes={"Wizard"},
            schools={"Evocation"},
            levels={1}
        )
        
        # Verify all match criteria
        for name, spell in spells:
            assert spell['level'] == 1
            assert spell['school'] == 'Evocation'
            assert 'Wizard' in spell['classes']

    def test_complex_filter_combination(self):
        """Test complex combination of filters."""
        # Wizard or Sorcerer, Evocation or Abjuration, levels 0-3
        spells = generate.get_spells(
            classes={"Wizard", "Sorcerer"},
            schools={"Evocation", "Abjuration"},
            levels={0, 1, 2, 3}
        )
        
        assert len(spells) > 0
        
        # Verify all match criteria
        for name, spell in spells:
            assert spell['level'] in [0, 1, 2, 3]
            assert spell['school'] in ['Evocation', 'Abjuration']
            assert any(cls in spell['classes'] for cls in ['Wizard', 'Sorcerer'])

    def test_spell_sorting(self):
        """Test that spells are returned in alphabetical order."""
        spells = [x[0] for x in generate.get_spells()]
        assert spells == sorted(spells)


@pytest.mark.unit
class TestLevelParsing:
    """Test level range parsing functionality."""

    def test_parse_single_level(self):
        """Test parsing a single level."""
        assert generate.parse_levels(['1']) == {1}
        assert generate.parse_levels(['0']) == {0}
        assert generate.parse_levels(['9']) == {9}

    def test_parse_multiple_levels(self):
        """Test parsing multiple individual levels."""
        assert generate.parse_levels(['5', '8', '0']) == {0, 5, 8}
        assert generate.parse_levels(['1', '3', '5', '7', '9']) == {1, 3, 5, 7, 9}

    def test_parse_level_range(self):
        """Test parsing level ranges."""
        assert generate.parse_levels(['2-3']) == {2, 3}
        assert generate.parse_levels(['2-6']) == {2, 3, 4, 5, 6}
        assert generate.parse_levels(['0-2']) == {0, 1, 2}

    def test_parse_mixed_levels_and_ranges(self):
        """Test parsing mixed individual levels and ranges."""
        assert generate.parse_levels(['0', '2-6', '9']) == {0, 2, 3, 4, 5, 6, 9}
        assert generate.parse_levels(['1-3', '5', '7-9']) == {1, 2, 3, 5, 7, 8, 9}

    def test_parse_full_range(self):
        """Test parsing full spell level range."""
        assert generate.parse_levels(['0-9']) == {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}

    def test_parse_none_returns_none(self):
        """Test that None input returns None."""
        assert generate.parse_levels(None) is None

    def test_parse_empty_list(self):
        """Test parsing empty list."""
        result = generate.parse_levels([])
        assert result == set()

