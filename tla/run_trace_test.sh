#!/bin/bash
set -e

# Generate the trace file using Quint
echo "Generating trace with Quint..."
npx @informalsystems/quint run --mbt --max-steps=10 --out-itf=trace.itf.json tcp_simple.qnt

# Run the Python verification script
echo "Running Python verification..."
if command -v uv >/dev/null 2>&1; then
    # uv handles dependencies (pydantic) automatically via script metadata
    uv run test_tcp.py
else
    echo "uv not found. Please install uv or ensure pydantic is installed in your python environment."
    python3 test_tcp.py
fi
