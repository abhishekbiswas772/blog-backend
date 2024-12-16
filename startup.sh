#!/bin/bash

python -m flask db init
python -m flask db migrate
python -m flask db upgrade

# Start the Flask application
python app.py