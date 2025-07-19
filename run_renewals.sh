#!/bin/bash
# Auto-renewal runner for LTFPQRR

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run the renewal process
echo "$(date): Starting subscription renewal process" >> logs/renewal.log
python3 scripts/manual_renewal.py --auto >> logs/renewal.log 2>&1
echo "$(date): Renewal process completed" >> logs/renewal.log
