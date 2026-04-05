#!/bin/bash
# LIBR8 Developer Environment Setup Script
set -euo pipefail

if [ ! -f "scripts/setup_dev.sh" ]; then
    echo "Please run this script from the repository root."
    exit 1
fi

echo "Setting up LIBR8 developer environment..."

# 1. Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 2. Upgrade pip
pip install --upgrade pip

# 3. Install core dependencies
echo "Installing dependencies..."
pip install python-dotenv maturin pytest psycopg[binary] dspy-ai zep-python

# 4. Initialize storage directories
echo "Initializing storage directories..."
mkdir -p .storage/.runs

# 5. Build Rust extensions
echo "Building Rust extensions..."
if command -v maturin > /dev/null; then
    (
        cd rust/retrieval_ranker
        maturin develop
    )
else
    echo "Warning: maturin not found, skipping Rust build."
fi

# 6. Create initial .env if missing
if [ ! -f ".env" ]; then
    echo "Creating default .env file..."
    cat > .env << 'EOF'
LIBR8_COGNITION_BACKEND=fallback
LIBR8_STORAGE_DIR=.storage
LIBR8_SERVICE_HOST=127.0.0.1
LIBR8_SERVICE_PORT=8080
LIBR8_LOG_LEVEL=INFO
LIBR8_LOG_JSON=True
LIBR8_AUTO_MIGRATE=False
LIBR8_REQUIRE_ISOLATION_FOR_WRITES=False
LIBR8_EXECUTION_ISOLATION_BACKEND=none
LIBR8_ALLOW_UNAUTHENTICATED_NON_LOOPBACK=False
EOF
fi

echo "Setup complete! Use 'source .venv/bin/activate' to start."

# 7. Final Healthcheck
echo "Running post-setup healthcheck..."
if python main.py healthcheck; then
    echo "Environment verified successfully."
else
    echo "Warning: Healthcheck failed. Review the output above."
fi
