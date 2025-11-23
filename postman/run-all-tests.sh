#!/bin/bash

# Backend API - Postman Collections Test Runner
# This script runs all Postman collections using Newman

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
POSTMAN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${POSTMAN_DIR}/Backend-API.Environment.postman_environment.json"
REPORT_DIR="${POSTMAN_DIR}/reports"

# Create reports directory
mkdir -p "${REPORT_DIR}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Backend API - Postman Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Newman is installed
if ! command -v newman &> /dev/null; then
    echo -e "${RED}❌ Newman is not installed${NC}"
    echo -e "${YELLOW}Install with: npm install -g newman${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Newman found${NC}"
echo ""

# Function to run a collection
run_collection() {
    local collection_name=$1
    local collection_file="${POSTMAN_DIR}/${collection_name}.postman_collection.json"
    
    echo -e "${BLUE}Running: ${collection_name}${NC}"
    echo "----------------------------------------"
    
    if newman run "${collection_file}" \
        -e "${ENVIRONMENT}" \
        --reporters cli,json \
        --reporter-json-export "${REPORT_DIR}/${collection_name}-report.json" \
        --color on \
        --timeout-request 10000; then
        echo -e "${GREEN}✅ ${collection_name} - PASSED${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}❌ ${collection_name} - FAILED${NC}"
        echo ""
        return 1
    fi
}

# Track results
TOTAL=0
PASSED=0
FAILED=0

# Run collections in order
collections=(
    "Backend-API.Health"
    "Backend-API.Authentication"
    "Backend-API.Users"
    "Backend-API.Dashboard"
    "Backend-API.Export"
)

for collection in "${collections[@]}"; do
    TOTAL=$((TOTAL + 1))
    if run_collection "${collection}"; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
done

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total Collections: ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo ""

# Reports location
echo -e "${YELLOW}Reports saved to: ${REPORT_DIR}${NC}"
echo ""

# Exit with appropriate code
if [ ${FAILED} -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
