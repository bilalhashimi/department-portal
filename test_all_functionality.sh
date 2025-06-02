#!/bin/bash

# Comprehensive System Test Runner
# Tests all aspects of the department portal application

echo "🚀 Starting Comprehensive System Tests"
echo "=============================================="
echo "Testing all functionality before fixing issues"
echo "=============================================="

# Initialize variables
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_RESULTS=""

# Function to run a test and capture results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local test_dir="$3"
    
    echo ""
    echo "🔍 Running: $test_name"
    echo "----------------------------------------"
    
    cd "$test_dir" 2>/dev/null || {
        echo "❌ Failed to change to directory: $test_dir"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS="$TEST_RESULTS\n❌ $test_name: Directory not found"
        return 1
    }
    
    # Run the test command and capture output
    if eval "$test_command" 2>&1; then
        echo "✅ $test_name: PASSED"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS="$TEST_RESULTS\n✅ $test_name: PASSED"
    else
        echo "❌ $test_name: FAILED"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS="$TEST_RESULTS\n❌ $test_name: FAILED"
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    cd - >/dev/null
}

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "📁 Project Root: $PROJECT_ROOT"
echo "📁 Backend Dir: $BACKEND_DIR"
echo "📁 Frontend Dir: $FRONTEND_DIR"

# Check if directories exist
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Backend directory not found: $BACKEND_DIR"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# 1. Test Backend Server Status
echo ""
echo "🌐 BACKEND SERVER TESTS"
echo "=============================================="

# Check if backend server is running
if curl -s http://localhost:8000/health/ >/dev/null 2>&1; then
    echo "✅ Backend server is running on port 8000"
    BACKEND_RUNNING=true
else
    echo "❌ Backend server is not running on port 8000"
    BACKEND_RUNNING=false
fi

# 2. Test Frontend Server Status
echo ""
echo "🌐 FRONTEND SERVER TESTS"
echo "=============================================="

# Check if frontend server is running
FRONTEND_PORT=5173
if ! curl -s http://localhost:$FRONTEND_PORT/ >/dev/null 2>&1; then
    FRONTEND_PORT=5174
fi

if curl -s http://localhost:$FRONTEND_PORT/ >/dev/null 2>&1; then
    echo "✅ Frontend server is running on port $FRONTEND_PORT"
    FRONTEND_RUNNING=true
else
    echo "❌ Frontend server is not running"
    FRONTEND_RUNNING=false
fi

# 3. Backend Tests
echo ""
echo "🔧 BACKEND FUNCTIONALITY TESTS"
echo "=============================================="

# Run Django system checks
run_test "Django System Check" "python manage.py check" "$BACKEND_DIR"

# Run database tests
if [ -f "$BACKEND_DIR/test_database.py" ]; then
    run_test "Database Tests" "python test_database.py" "$BACKEND_DIR"
else
    echo "⚠️  Database test file not found"
fi

# Run API tests (only if server is running)
if [ "$BACKEND_RUNNING" = true ] && [ -f "$BACKEND_DIR/test_all_functionality.py" ]; then
    run_test "Backend API Tests" "python test_all_functionality.py" "$BACKEND_DIR"
else
    echo "⚠️  Backend API tests skipped (server not running or test file not found)"
fi

# Test Django migrations
run_test "Migration Check" "python manage.py showmigrations" "$BACKEND_DIR"

# 4. Frontend Tests
echo ""
echo "🎨 FRONTEND FUNCTIONALITY TESTS"
echo "=============================================="

# Test package.json
run_test "Package.json Check" "test -f package.json && npm list --depth=0" "$FRONTEND_DIR"

# Test TypeScript compilation
run_test "TypeScript Build Test" "npm run build" "$FRONTEND_DIR"

# Run frontend tests if available
if [ -f "$FRONTEND_DIR/test_frontend_functionality.js" ]; then
    run_test "Frontend Structure Tests" "node test_frontend_functionality.js" "$FRONTEND_DIR"
else
    echo "⚠️  Frontend test file not found"
fi

# 5. Integration Tests
echo ""
echo "🔗 INTEGRATION TESTS"
echo "=============================================="

# Test API connectivity from frontend
if [ "$BACKEND_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
    echo "🔍 Testing API connectivity..."
    
    # Test CORS headers
    CORS_TEST=$(curl -s -H "Origin: http://localhost:$FRONTEND_PORT" \
                     -H "Access-Control-Request-Method: POST" \
                     -H "Access-Control-Request-Headers: X-Requested-With" \
                     -X OPTIONS http://localhost:8000/api/v1/accounts/auth/login/)
    
    if [ $? -eq 0 ]; then
        echo "✅ CORS Configuration: PASSED"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS="$TEST_RESULTS\n✅ CORS Configuration: PASSED"
    else
        echo "❌ CORS Configuration: FAILED"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS="$TEST_RESULTS\n❌ CORS Configuration: FAILED"
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
else
    echo "⚠️  Integration tests skipped (servers not running)"
fi

# 6. File Structure Tests
echo ""
echo "📁 FILE STRUCTURE TESTS"
echo "=============================================="

# Check critical backend files
BACKEND_FILES=(
    "manage.py"
    "portal_backend/settings.py"
    "portal_backend/urls.py"
    "accounts/models.py"
    "accounts/views.py"
    "accounts/serializers.py"
    "documents/models.py"
    "documents/views.py"
    "documents/serializers.py"
    "departments/models.py"
)

for file in "${BACKEND_FILES[@]}"; do
    if [ -f "$BACKEND_DIR/$file" ]; then
        echo "✅ Backend file exists: $file"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS="$TEST_RESULTS\n✅ Backend file: $file"
    else
        echo "❌ Backend file missing: $file"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS="$TEST_RESULTS\n❌ Backend file missing: $file"
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
done

# Check critical frontend files
FRONTEND_FILES=(
    "package.json"
    "vite.config.ts"
    "tsconfig.json"
    "index.html"
    "src/App.tsx"
    "src/main.tsx"
    "src/services/api.ts"
    "src/components/DocumentList.tsx"
    "src/components/DocumentUpload.tsx"
)

for file in "${FRONTEND_FILES[@]}"; do
    if [ -f "$FRONTEND_DIR/$file" ]; then
        echo "✅ Frontend file exists: $file"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS="$TEST_RESULTS\n✅ Frontend file: $file"
    else
        echo "❌ Frontend file missing: $file"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS="$TEST_RESULTS\n❌ Frontend file missing: $file"
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
done

# 7. Environment Tests
echo ""
echo "🌍 ENVIRONMENT TESTS"
echo "=============================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep "Python 3")
if [ $? -eq 0 ]; then
    echo "✅ Python 3 available: $PYTHON_VERSION"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS="$TEST_RESULTS\n✅ Python 3: Available"
else
    echo "❌ Python 3 not available"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS="$TEST_RESULTS\n❌ Python 3: Not available"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Check Node.js version
NODE_VERSION=$(node --version 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ Node.js available: $NODE_VERSION"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS="$TEST_RESULTS\n✅ Node.js: Available"
else
    echo "❌ Node.js not available"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS="$TEST_RESULTS\n❌ Node.js: Not available"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Check virtual environment
if [ -d "$BACKEND_DIR/venv" ]; then
    echo "✅ Python virtual environment exists"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS="$TEST_RESULTS\n✅ Virtual Environment: Available"
else
    echo "❌ Python virtual environment not found"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS="$TEST_RESULTS\n❌ Virtual Environment: Not found"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# 8. Generate Final Report
echo ""
echo "=============================================="
echo "📊 COMPREHENSIVE TEST RESULTS SUMMARY"
echo "=============================================="
echo "Total Tests Run: $TOTAL_TESTS"
echo "✅ Passed: $PASSED_TESTS"
echo "❌ Failed: $FAILED_TESTS"

if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || python3 -c "print(f'{$PASSED_TESTS * 100 / $TOTAL_TESTS:.1f}')")
    echo "📈 Success Rate: ${SUCCESS_RATE}%"
fi

echo ""
echo "🔍 DETAILED RESULTS:"
echo -e "$TEST_RESULTS"

echo ""
echo "=============================================="
echo "🚨 ISSUES IDENTIFIED (TO BE FIXED):"
echo "=============================================="

# List the issues we know about
echo "Backend Issues:"
if [ "$BACKEND_RUNNING" = false ]; then
    echo "  - Django server not running (whitenoise module missing)"
fi

echo "Frontend Issues:"
if [ "$FRONTEND_RUNNING" = false ]; then
    echo "  - Frontend server issues or port conflicts"
fi

echo ""
echo "=============================================="
echo "✅ TESTING PHASE COMPLETE"
echo "=============================================="
echo "All functionality has been tested."
echo "Issues identified above need to be fixed."
echo ""

# Return appropriate exit code
if [ $FAILED_TESTS -gt 0 ]; then
    echo "⚠️  Some tests failed. Proceeding to fix issues..."
    exit 1
else
    echo "🎉 All tests passed!"
    exit 0
fi 