#!/bin/bash
# Test runner script for D&D Spell Card Generator
# Usage: ./run_tests.sh [options]

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}D&D Spell Card Generator - Test Suite${NC}"
echo "========================================"
echo ""

# Parse command line arguments
case "$1" in
    --unit)
        echo -e "${GREEN}Running unit tests only...${NC}"
        python3 -m pytest -m unit -v
        ;;
    --integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        python3 -m pytest -m integration -v
        ;;
    --fast)
        echo -e "${GREEN}Running fast tests (excluding slow tests)...${NC}"
        python3 -m pytest -m "not slow and not requires_latex" -v
        ;;
    --no-latex)
        echo -e "${GREEN}Running tests (excluding LaTeX compilation tests)...${NC}"
        python3 -m pytest -m "not requires_latex" -v
        ;;
    --coverage)
        echo -e "${GREEN}Running tests with coverage report...${NC}"
        python3 -m pytest --cov=generate --cov-report=html --cov-report=term -m "not requires_latex"
        echo ""
        echo -e "${YELLOW}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    --parallel)
        echo -e "${GREEN}Running tests in parallel...${NC}"
        python3 -m pytest -n auto -m "not requires_latex"
        ;;
    --file)
        if [ -z "$2" ]; then
            echo -e "${YELLOW}Usage: ./run_tests.sh --file <test_file>${NC}"
            exit 1
        fi
        echo -e "${GREEN}Running tests in $2...${NC}"
        python3 -m pytest "tests/$2" -v
        ;;
    --help|-h)
        echo "Usage: ./run_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  --unit         Run unit tests only"
        echo "  --integration  Run integration tests"
        echo "  --fast         Run fast tests (exclude slow and LaTeX tests)"
        echo "  --no-latex     Run all tests except those requiring LaTeX"
        echo "  --coverage     Run tests with coverage report"
        echo "  --parallel     Run tests in parallel (faster)"
        echo "  --file <name>  Run specific test file"
        echo "  --help, -h     Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh                    # Run all tests"
        echo "  ./run_tests.sh --fast             # Quick test run"
        echo "  ./run_tests.sh --coverage         # Generate coverage report"
        echo "  ./run_tests.sh --file test_spell_filtering.py"
        ;;
    *)
        echo -e "${GREEN}Running all tests (excluding LaTeX compilation tests)...${NC}"
        python3 -m pytest -m "not requires_latex" -v --tb=short
        ;;
esac

exit_code=$?
echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✓ Tests completed successfully!${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed. See output above for details.${NC}"
fi

exit $exit_code

