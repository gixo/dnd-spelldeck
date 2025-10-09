# D&D Spell Card Generator Test Suite

This directory contains comprehensive tests for the D&D spell card generator.

## Test Structure

The test suite is organized into several modules:

- **`test_spell_filtering.py`** - Tests for spell filtering by class, level, school, and name
- **`test_latex_generation.py`** - Tests for LaTeX generation, formatting, and text truncation
- **`test_card_generation.py`** - Tests for generating cards with different spell types and edge cases
- **`test_integration.py`** - Integration tests for the full generation pipeline (requires LaTeX)
- **`test_script_generation.py`** - End-to-end tests for `generate_cards.py` and `export_card_image.py` scripts

## Running Tests

### Install Test Dependencies

```bash
pip install -r tests/requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests excluding slow tests
pytest -m "not slow"

# Run tests excluding those requiring LaTeX
pytest -m "not requires_latex"
```

### Run Tests in Parallel

```bash
# Run tests using multiple CPU cores for faster execution
pytest -n auto
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest --cov=generate --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
```

### Run Specific Test Files

```bash
# Run only filtering tests
pytest tests/test_spell_filtering.py

# Run only LaTeX generation tests
pytest tests/test_latex_generation.py

# Run only card generation tests
pytest tests/test_card_generation.py

# Run only integration tests
pytest tests/test_integration.py

# Run only script generation tests
pytest tests/test_script_generation.py

# Run only generate_cards.py tests
pytest tests/test_script_generation.py::TestGenerateCardsScript

# Run only export_card_image.py tests
pytest tests/test_script_generation.py::TestExportCardImageScript
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_spell_filtering.py::TestSpellFiltering

# Run a specific test function
pytest tests/test_spell_filtering.py::TestSpellFiltering::test_filter_by_single_class
```

### Verbose Output

```bash
# Show verbose output with full test names
pytest -v

# Show extra verbose output with print statements
pytest -vv -s
```

## Test Markers

Tests are marked with the following markers:

- **`@pytest.mark.unit`** - Unit tests for individual functions
- **`@pytest.mark.integration`** - Integration tests that test the full pipeline
- **`@pytest.mark.slow`** - Tests that take a long time to run
- **`@pytest.mark.requires_latex`** - Tests that require LaTeX to be installed

## Fixtures

Common test fixtures are defined in `conftest.py`:

- **`spells_data`** - Loads the complete spells.json database
- **`sample_spell`** - A basic test spell
- **`ritual_spell`** - A ritual spell for testing
- **`concentration_spell`** - A concentration spell for testing
- **`cantrip_spell`** - A cantrip for testing
- **`area_effect_spells`** - Spells with different area effects (cone, sphere, cube, etc.)
- **`long_text_spell`** - A spell with very long text for truncation testing
- **`temp_output_dir`** - Temporary directory for test outputs (auto-cleanup)
- **`temp_tex_dir`** - Temporary directory for LaTeX testing (auto-cleanup)

## Test Coverage

The test suite aims to cover:

1. **Spell Filtering**
   - Filter by class, level, school, name
   - Multiple filters simultaneously
   - Level range parsing (e.g., "1-3")
   - Case-insensitive filtering

2. **Text Processing**
   - Text truncation for long spell descriptions
   - Brace balancing in truncated text
   - Text wrapping at 80 characters
   - Paragraph preservation

3. **LaTeX Generation**
   - Spell headers for all levels and types
   - Material component formatting
   - Area effect parsing (cone, sphere, cube, line, cylinder, emanation)
   - Concentration and ritual flags
   - Attack/save and damage/effect fields

4. **Card Generation**
   - Cantrips, leveled spells, and 9th level spells
   - Ritual spells
   - Concentration spells
   - Spells with material components
   - Spells with various area effects
   - Edge cases (empty text, special characters, long names, etc.)

5. **Integration**
   - Full LaTeX output generation
   - Command-line interface
   - Real spell data validation
   - LaTeX compilation (requires LaTeX installation)
   - Output validation and integrity checks

6. **Script Generation** (End-to-End)
   - `generate_cards.py` script execution with various filters
   - `export_card_image.py` image export functionality
   - PDF generation and validation
   - Image format conversion (PNG, JPG)
   - DPI settings and image quality
   - Intermediate file cleanup
   - Error handling and edge cases
   - Performance benchmarks

## Continuous Integration

The test suite is designed to work in CI/CD environments:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r tests/requirements.txt
      - run: pytest -m "not requires_latex"
```

## Writing New Tests

When adding new tests:

1. Use appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`, etc.)
2. Use descriptive test names that explain what is being tested
3. Use fixtures from `conftest.py` when possible
4. Clean up any temporary files or resources
5. Add docstrings to test functions explaining the test purpose

Example:

```python
@pytest.mark.unit
def test_my_new_feature(sample_spell):
    """Test that my new feature works correctly."""
    # Arrange
    spell = sample_spell.copy()
    spell['new_field'] = 'test value'
    
    # Act
    result = generate.my_new_function(spell)
    
    # Assert
    assert result == expected_value
```

## Troubleshooting

### Tests Fail Due to Missing LaTeX

If you don't have LaTeX installed, skip tests that require it:

```bash
pytest -m "not requires_latex"
```

### Tests Are Too Slow

Run only fast unit tests:

```bash
pytest -m "unit and not slow"
```

Or use parallel execution:

```bash
pytest -n auto
```

### Import Errors

Make sure you're running pytest from the project root directory:

```bash
cd /path/to/dnd-spellcheck-gixo
pytest
```

## Test Statistics

Current test coverage includes:

- 142 individual test cases
- All 10 spell levels (0-9)
- All 6 area effect types
- Multiple spell schools and classes
- Edge cases and error conditions
- Real spell data validation
- End-to-end script execution tests
- Image export in multiple formats
- LaTeX compilation validation

Run `pytest --collect-only` to see all available tests.

### Script Generation Tests

The `test_script_generation.py` module includes 30 comprehensive tests:

- **TestGenerateCardsScript** (12 tests)
  - Help command validation
  - Spells.tex generation without compilation
  - Single and multiple spell card generation
  - Filtering by class, level, school
  - Level range support (e.g., "1-3")
  - Output directory creation
  - Cleanup functionality
  - Statistics reporting

- **TestExportCardImageScript** (10 tests)
  - Help command validation
  - PNG and JPG export
  - Custom DPI settings (300-900)
  - Keeping intermediate PDFs
  - Default samples directory
  - Nonexistent spell handling
  - Multiple format export
  - High-resolution output

- **TestScriptIntegration** (2 tests)
  - Generate then export workflow
  - Consistency between scripts

- **TestScriptErrorHandling** (4 tests)
  - Missing data file handling
  - Invalid class/level filters
  - Dependency checking

- **TestScriptPerformance** (2 tests)
  - Single spell generation speed
  - Multiple spell generation scalability

