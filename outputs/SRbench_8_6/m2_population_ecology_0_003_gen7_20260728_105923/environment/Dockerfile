FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "numpy" "pandas" "scikit-learn" "sympy" "scipy"

COPY train_data.csv /app/data/train_data.csv
