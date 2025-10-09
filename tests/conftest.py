"""
Pytest configuration and fixtures for spell card testing.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import generate


@pytest.fixture
def spells_data():
    """Load the spells data from JSON file."""
    with open('data/spells.json') as f:
        return json.load(f)


@pytest.fixture
def sample_spell():
    """Return a sample spell for testing."""
    return {
        "name": "Test Spell",
        "level": 1,
        "ritual": False,
        "time": "1 action",
        "range": "30 ft.",
        "components": ["V", "S"],
        "concentration": False,
        "duration": "Instantaneous",
        "school": "Evocation",
        "attack_save": "DEX Save",
        "damage_effect": "Fire",
        "text": "This is a test spell that does test damage.",
        "material": None,
        "classes": ["Wizard", "Sorcerer"],
        "source": "Test Source",
        "source_page": 123
    }


@pytest.fixture
def ritual_spell():
    """Return a ritual spell for testing."""
    return {
        "name": "Test Ritual",
        "level": 2,
        "ritual": True,
        "time": "1 minute",
        "range": "Self",
        "components": ["V", "S", "M"],
        "concentration": False,
        "duration": "10 minutes",
        "school": "Divination",
        "attack_save": "None",
        "damage_effect": "Detection",
        "text": "This is a test ritual spell.",
        "material": "a crystal ball worth 100gp",
        "classes": ["Wizard", "Cleric"],
        "source": "Test Source",
        "source_page": 456
    }


@pytest.fixture
def concentration_spell():
    """Return a concentration spell for testing."""
    return {
        "name": "Test Concentration",
        "level": 3,
        "ritual": False,
        "time": "1 action",
        "range": "60 ft.",
        "components": ["V", "S"],
        "concentration": True,
        "duration": "Concentration, up to 1 minute",
        "school": "Enchantment",
        "attack_save": "WIS Save",
        "damage_effect": "Control",
        "text": "This is a test concentration spell.",
        "material": None,
        "classes": ["Wizard", "Bard"],
        "source": "Test Source",
        "source_page": 789
    }


@pytest.fixture
def cantrip_spell():
    """Return a cantrip for testing."""
    return {
        "name": "Test Cantrip",
        "level": 0,
        "ritual": False,
        "time": "1 action",
        "range": "120 ft.",
        "components": ["V", "S"],
        "concentration": False,
        "duration": "Instantaneous",
        "school": "Evocation",
        "attack_save": "Ranged",
        "damage_effect": "Force",
        "text": "This is a test cantrip that does 1d10 force damage.",
        "material": None,
        "classes": ["Wizard", "Sorcerer", "Warlock"],
        "source": "Test Source",
        "source_page": 100
    }


@pytest.fixture
def area_effect_spells():
    """Return spells with different area effects for testing."""
    return {
        "cone": {
            "name": "Cone Spell",
            "level": 1,
            "ritual": False,
            "time": "1 action",
            "range": "Self (15 ft. cone)",
            "components": ["V", "S"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Evocation",
            "attack_save": "DEX Save",
            "damage_effect": "Cold",
            "text": "A blast of cold air erupts from your hands.",
            "material": None,
            "classes": ["Sorcerer", "Wizard"],
            "source": "Test Source",
            "source_page": 1
        },
        "sphere": {
            "name": "Sphere Spell",
            "level": 3,
            "ritual": False,
            "time": "1 action",
            "range": "150 ft. (20 ft. sphere)",
            "components": ["V", "S", "M"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Evocation",
            "attack_save": "DEX Save",
            "damage_effect": "Fire",
            "text": "A bright streak flashes and explodes.",
            "material": "a tiny ball of bat guano and sulfur",
            "classes": ["Sorcerer", "Wizard"],
            "source": "Test Source",
            "source_page": 2
        },
        "cube": {
            "name": "Cube Spell",
            "level": 2,
            "ritual": False,
            "time": "1 action",
            "range": "90 ft. (10 ft. cube)",
            "components": ["V", "S"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Conjuration",
            "attack_save": "STR Save",
            "damage_effect": "Force",
            "text": "A cube of force appears.",
            "material": None,
            "classes": ["Wizard"],
            "source": "Test Source",
            "source_page": 3
        },
        "line": {
            "name": "Line Spell",
            "level": 3,
            "ritual": False,
            "time": "1 action",
            "range": "Self (100 ft. line)",
            "components": ["V", "S", "M"],
            "concentration": False,
            "duration": "Instantaneous",
            "school": "Evocation",
            "attack_save": "DEX Save",
            "damage_effect": "Lightning",
            "text": "A stroke of lightning forms a line.",
            "material": "a bit of fur and a rod of amber",
            "classes": ["Sorcerer", "Wizard"],
            "source": "Test Source",
            "source_page": 4
        },
        "cylinder": {
            "name": "Cylinder Spell",
            "level": 2,
            "ritual": False,
            "time": "1 action",
            "range": "60 ft. (20 ft. cylinder)",
            "components": ["V", "S"],
            "concentration": True,
            "duration": "Concentration, up to 1 minute",
            "school": "Conjuration",
            "attack_save": "DEX Save",
            "damage_effect": "Fire",
            "text": "A cylinder of flame roars.",
            "material": None,
            "classes": ["Druid"],
            "source": "Test Source",
            "source_page": 5
        },
        "emanation": {
            "name": "Emanation Spell",
            "level": 4,
            "ritual": False,
            "time": "1 action",
            "range": "Self (30 ft. emanation)",
            "components": ["V"],
            "concentration": True,
            "duration": "Concentration, up to 10 minutes",
            "school": "Abjuration",
            "attack_save": "None",
            "damage_effect": "Debuff",
            "text": "An emanation of holy power radiates.",
            "material": None,
            "classes": ["Cleric", "Paladin"],
            "source": "Test Source",
            "source_page": 6
        }
    }


@pytest.fixture
def long_text_spell():
    """Return a spell with very long text that needs truncation."""
    long_text = " ".join(["This is a very long spell description."] * 100)
    return {
        "name": "Long Text Spell",
        "level": 5,
        "ritual": False,
        "time": "1 action",
        "range": "60 ft.",
        "components": ["V", "S", "M"],
        "concentration": False,
        "duration": "Instantaneous",
        "school": "Transmutation",
        "attack_save": "None",
        "damage_effect": "Utility",
        "text": long_text,
        "material": "a bunch of stuff",
        "classes": ["Wizard"],
        "source": "Test Source",
        "source_page": 999
    }


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def temp_tex_dir():
    """Create a temporary tex directory for testing."""
    temp_dir = tempfile.mkdtemp()
    tex_dir = os.path.join(temp_dir, 'tex')
    os.makedirs(tex_dir, exist_ok=True)
    
    # Copy template files if they exist
    if os.path.exists('tex/cards.tex'):
        shutil.copy('tex/cards.tex', tex_dir)
    if os.path.exists('tex/printable.tex'):
        shutil.copy('tex/printable.tex', tex_dir)
    
    yield temp_dir
    
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual functions"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that generate actual cards"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take a long time to run"
    )
    config.addinivalue_line(
        "markers", "requires_latex: Tests that require LaTeX to be installed"
    )

