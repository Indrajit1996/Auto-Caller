#!/bin/bash

set -e

STACK_NAME=${STACK_NAME:-keystone}
REPORT_PORT=2001

show_help() {
  echo "Usage: ./run-tests.sh [OPTION]"
  echo ""
  echo "Options:"
  echo "  -h, --help      Show this help message"
  echo "  -r, --reports   Only start the test reports server"
  echo ""
}

run_tests() {
  echo "🚀 Starting test containers..."
  docker compose -f compose.yml -f compose.test.yml up -d --build

  echo "📋 Showing backend test logs..."
  docker logs -f "${STACK_NAME}-backend-test"

  # Check if the tests were successful
  BACKEND_EXIT_CODE=$(docker inspect "${STACK_NAME}-backend-test" --format='{{.State.ExitCode}}')

  if [ "$BACKEND_EXIT_CODE" -eq 0 ]; then
    echo "✅ Tests completed successfully!"
  else
    echo "❌ Tests failed with exit code $BACKEND_EXIT_CODE"
  fi

  echo ""
  echo "📊 Test reports are available at: http://localhost:${REPORT_PORT}"
  echo "   Reports are stored in:"
  echo "   - ./backend/test-results (Test results)"
  echo "   - ./backend/coverage (Coverage reports)"
  echo ""
  echo "Press any key to stop and remove the test containers..."
  read -n 1

  echo "🧹 Cleaning up test containers..."
  docker compose -f compose.yml -f compose.test.yml down
}

show_reports_only() {
  echo "📊 Starting test reports server only..."
  docker compose -f compose.yml -f compose.test.yml up -d test-report

  echo "📊 Test reports are available at: http://localhost:${REPORT_PORT}"
  echo "Press any key to stop the reports server..."
  read -n 1

  echo "🧹 Stopping reports server..."
  docker compose -f compose.yml -f compose.test.yml stop test-report
  docker compose -f compose.yml -f compose.test.yml rm -f test-report
}

# Parse command line arguments
case "$1" in
  -h|--help)
    show_help
    exit 0
    ;;
  -r|--reports)
    show_reports_only
    ;;
  *)
    run_tests
    ;;
esac
