FROM python:3.12-slim

# Set working directory
WORKDIR /app

RUN pip install --no-cache-dir "numpy" "pandas" "scikit-learn" "sympy" "scipy"

# Copy the training data into the agent-visible data directory
COPY train_data.csv /app/data/train_data.csv
