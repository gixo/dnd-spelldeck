# Testing Guide for D&D Spell Card Generator

This document provides comprehensive information about the test suite for the D&D Spell Card Generator.

## Quick Start

```bash
# Install test dependencies
pip3 install -r tests/requirements.txt

# Run all tests
./run_tests.sh

# Or use pytest directly
pytest
```

## Test Suite Overview

The test suite contains **142 test cases** covering all aspects of card generation:

### Test Files

1. **`test_spell_filtering.py`** (25 tests)
   - Filtering by class, level, school, and spell name
   - Level range parsing
   - Case-insensitive filtering
   - Combined filters

2. **`test_latex_generation.py`** (34 tests)
   - Text truncation and brace balancing
   - LaTeX formatting and headers
   - Area effect parsing
   - Component formatting
   - Ritual and concentration flags

3. **`test_card_generation.py`** (28 tests)
   - Different spell types (cantrips, leveled, high-level)
   - Area effects (cone, sphere, cube, line, cylinder, emanation)
   - Batch generation scenarios
   - Edge cases and special characters

4. **`test_integration.py`** (25 tests)
   - Full pipeline testing
   - Command-line interface
   - Real spell data validation
   - Output validation
   - LaTeX compilation (optional)

5. **`test_script_generation.py`** (30 tests) **NEW!**
   - End-to-end testing of `generate_cards.py` script
   - End-to-end testing of `export_card_image.py` script
   - PDF generation and validation
   - Image export (PNG, JPG) with various DPI settings
   - Script error handling and edge cases
   - Performance benchmarks

## Running Tests

### Basic Commands

```bash
# Run all tests (recommended)
./run_tests.sh

# Run specific test categories
./run_tests.sh --unit         # Unit tests only (fastest)
./run_tests.sh --integration  # Integration tests
./run_tests.sh --fast         # Exclude slow tests
./run_tests.sh --no-latex     # Exclude LaTeX compilation tests

# Run specific test file
./run_tests.sh --file test_spell_filtering.py

# Generate coverage report
./run_tests.sh --coverage

# Run tests in parallel (faster)
./run_tests.sh --parallel
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_spell_filtering.py

# Run specific test class
pytest tests/test_spell_filtering.py::TestSpellFiltering

# Run specific test
pytest tests/test_spell_filtering.py::TestSpellFiltering::test_filter_by_single_class

# Run tests by marker
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests only
pytest -m "not slow"              # Exclude slow tests
pytest -m "not requires_latex"    # Exclude LaTeX compilation tests

# Run with coverage
pytest --cov=generate --cov-report=html

# Run in parallel
pytest -n auto
```

## Test Categories (Markers)

Tests are organized with pytest markers:

- **`@pytest.mark.unit`** - Fast unit tests for individual functions
- **`@pytest.mark.integration`** - Integration tests for the full pipeline
- **`@pytest.mark.slow`** - Tests that take longer to run
- **`@pytest.mark.requires_latex`** - Tests that need LaTeX installed

## What's Tested

### 1. Spell Filtering (25 tests)

✅ Filter by class (Wizard, Cleric, etc.)  
✅ Filter by level (0-9)  
✅ Filter by school (Evocation, Abjuration, etc.)  
✅ Filter by spell name  
✅ Level range parsing (e.g., "1-3")  
✅ Case-insensitive filtering  
✅ Multiple filters combined  

### 2. Text Processing (10 tests)

✅ Text truncation at character limit  
✅ Balanced LaTeX braces in truncated text  
✅ Ellipsis addition for truncated text  
✅ Trailing space removal  
✅ Custom truncation lengths  

### 3. LaTeX Generation (24 tests)

✅ Spell headers for all levels (cantrip, 1st-9th)  
✅ Ritual spell formatting  
✅ Material component formatting  
✅ Area effect parsing (cone, sphere, cube, line, cylinder, emanation)  
✅ Concentration flags  
✅ Attack/save information  
✅ Damage/effect types  
✅ Text wrapping at 80 characters  
✅ Paragraph preservation  

### 4. Card Generation (28 tests)

✅ Cantrips  
✅ 1st-9th level spells  
✅ Ritual spells  
✅ Concentration spells  
✅ All area effect types  
✅ Material components  
✅ Batch generation  
✅ Edge cases (empty text, special characters, long names)  

### 5. Integration Tests (25 tests)

✅ Full LaTeX output generation  
✅ Command-line interface  
✅ All real spells from database  
✅ Output validation  
✅ UTF-8 encoding  
✅ Balanced LaTeX environments  
✅ Class spellbooks  
✅ School collections  

### 6. Script Generation (30 tests)

**generate_cards.py Tests (12 tests):**  
✅ Help command functionality  
✅ Spells.tex generation without compilation  
✅ Single spell card generation  
✅ Multiple spell cards generation  
✅ Filter by class (e.g., Wizard)  
✅ Filter by level range (e.g., "1-3")  
✅ Filter by school (e.g., Evocation)  
✅ Output directory creation  
✅ Cleanup of intermediate files  
✅ Statistics reporting  

**export_card_image.py Tests (10 tests):**  
✅ Help command functionality  
✅ PNG export with various DPI settings  
✅ JPG export with quality optimization  
✅ Custom DPI (300-900)  
✅ Intermediate PDF preservation  
✅ Default samples directory usage  
✅ Nonexistent spell handling  
✅ Multiple format export (PNG/JPG)  
✅ High-resolution output validation  
✅ File format verification (magic bytes)  

**Integration Tests (2 tests):**  
✅ Generate then export workflow  
✅ Consistency between scripts  

**Error Handling Tests (4 tests):**  
✅ Invalid class filter handling  
✅ Invalid level filter handling  
✅ Missing data file detection  
✅ Dependency checking  

**Performance Tests (2 tests):**  
✅ Single spell generation speed (<10s)  
✅ Multiple spell generation scalability (<30s)  

## Test Coverage

Run coverage analysis:

```bash
./run_tests.sh --coverage
```

This generates an HTML coverage report showing:
- Line coverage
- Branch coverage
- Uncovered lines
- Coverage percentages

View the report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Writing New Tests

### Test Structure

```python
import pytest
import generate

@pytest.mark.unit
def test_my_feature(sample_spell):
    """Test description."""
    # Arrange
    spell = sample_spell.copy()
    
    # Act
    result = generate.some_function(spell)
    
    # Assert
    assert result == expected_value
```

### Available Fixtures

Fixtures are defined in `tests/conftest.py`:

- `spells_data` - Complete spell database
- `sample_spell` - Basic test spell
- `ritual_spell` - Ritual spell
- `concentration_spell` - Concentration spell
- `cantrip_spell` - Level 0 spell
- `area_effect_spells` - Dict of spells with different area effects
- `long_text_spell` - Spell with very long text
- `temp_output_dir` - Temporary directory (auto-cleanup)
- `temp_tex_dir` - Temporary LaTeX directory (auto-cleanup)

### Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Add docstrings** to test functions
3. **Use appropriate markers** (`@pytest.mark.unit`, etc.)
4. **Clean up resources** (or use fixtures that auto-cleanup)
5. **Test one thing per test** - keep tests focused
6. **Use fixtures** instead of duplicating setup code

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      
      - name: Run tests
        run: pytest -m "not requires_latex" --cov=generate
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

**Problem**: Tests fail with import errors  
**Solution**: Run pytest from the project root directory

**Problem**: LaTeX tests are skipped  
**Solution**: This is normal if LaTeX isn't installed. Use `--no-latex` flag

**Problem**: Tests are slow  
**Solution**: Use `./run_tests.sh --fast` or `pytest -n auto` for parallel execution

**Problem**: Coverage report not generated  
**Solution**: Install pytest-cov: `pip3 install pytest-cov`

### Debug Mode

Run tests with extra output:

```bash
# Show print statements
pytest -v -s

# Show extra verbose output
pytest -vv

# Stop at first failure
pytest -x

# Drop into debugger on failure
pytest --pdb
```

## Test Results Summary

Latest test run:
```
====================== 110 passed, 2 deselected in 0.46s =======================

✓ All spell filtering tests pass
✓ All LaTeX generation tests pass
✓ All card generation tests pass
✓ All integration tests pass (excluding LaTeX compilation)
✓ All 500+ real spells from database generate without errors
```

## Performance

- **Unit tests**: ~0.15s (87 tests)
- **Integration tests**: ~0.35s (23 tests, excluding LaTeX)
- **Full suite**: ~0.46s (110 tests)
- **Parallel execution**: ~0.2s with `-n auto`

## Contributing Tests

When adding features:

1. Write tests first (TDD approach recommended)
2. Ensure all existing tests still pass
3. Add tests for edge cases
4. Update this documentation if adding new test categories
5. Maintain test coverage above 80%

Run the full test suite before submitting changes:

```bash
./run_tests.sh --coverage
```

## Questions?

See `tests/README.md` for more details about the test structure and fixtures.

