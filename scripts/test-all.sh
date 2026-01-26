#!/bin/bash
# Script to run all tests for the microservices architecture

echo "🧪 Running comprehensive tests for Music Review App..."

# Ensure we're in the right directory
cd "$(dirname "$0")/.."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TOTAL_TESTS=0

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${YELLOW}--- $test_name ---${NC}"
    ((TOTAL_TESTS++))
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ $test_name PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ $test_name FAILED${NC}"
    fi
}

# Ensure RabbitMQ is running
echo "🐰 Checking RabbitMQ..."
if ! docker-compose ps rabbitmq | grep -q "Up"; then
    echo "Starting RabbitMQ..."
    docker-compose up -d rabbitmq
    sleep 10
fi

# Activate dev-tools environment
echo "🔧 Activating dev-tools environment..."
source ~/.virtualenvs/music_review_devtools/bin/activate

# Run tests
echo -e "\n🚀 Starting test suite..."

# 1. RabbitMQ connectivity tests
run_test "RabbitMQ Connectivity" "cd dev-tools && python test_rabbitmq.py > /dev/null 2>&1"

# 2. Shared module import tests
run_test "Shared Module Imports" "cd dev-tools && python -c 'from shared import MessageBroker, UserRegisteredEvent, AlbumCreatedEvent; print(\"Imports successful\")' > /dev/null 2>&1"

# 3. Event serialization tests
run_test "Event Serialization" "cd dev-tools && python -c '
from shared import UserRegisteredEvent
import json
event = UserRegisteredEvent(user_id=\"test\", email=\"test@test.com\", username=\"test\")
json_data = event.json()
parsed = json.loads(json_data)
assert \"event_id\" in parsed
assert \"timestamp\" in parsed
print(\"Serialization successful\")
' > /dev/null 2>&1"

# 4. Docker services health check
run_test "Docker Services Health" "docker-compose ps | grep -q 'Up.*healthy' || docker-compose ps | grep -q 'Up'"

# Print results summary
echo -e "\n${YELLOW}=================================================${NC}"
echo -e "${YELLOW}TEST RESULTS SUMMARY${NC}"
echo -e "${YELLOW}=================================================${NC}"

if [ $TESTS_PASSED -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 All tests passed! ($TESTS_PASSED/$TOTAL_TESTS)${NC}"
    echo -e "${GREEN}✅ The microservices infrastructure is ready!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. ($TESTS_PASSED/$TOTAL_TESTS passed)${NC}"
    echo -e "${RED}Please check the configuration and try again.${NC}"
    exit 1
fi