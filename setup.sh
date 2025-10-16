#!/bin/bash
# Setup script for RAG Template API

echo "Installing dependencies..."
python3 -m pip install --user -r requirements.txt

echo ""
echo "Installation complete!"
echo ""
echo "To run tests:"
echo "  python3 -m pytest"
echo ""
echo "To start the server:"
echo "  python3 -m uvicorn src.main:app --reload"
echo ""
