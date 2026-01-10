#!/bin/bash
# ─────────────────────────────────────────────
#  NL2SQL Compiler - Startup Script
# ─────────────────────────────────────────────

set -e

echo "╔══════════════════════════════════════════╗"
echo "║        NL2SQL Compiler  v1.0             ║"
echo "╚══════════════════════════════════════════╝"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌  Python 3 not found. Install it first."
    exit 1
fi

# Create virtual environment if missing
if [ ! -d "venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies
echo "→ Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create logs directory
mkdir -p app/logs
touch app/logs/query.log

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copy .env.example and fill in your keys."
    exit 1
fi

echo "→ Starting Streamlit app..."
echo ""
streamlit run app/main.py --server.port=8501 --server.headless=false
