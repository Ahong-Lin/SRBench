FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir numpy pandas sympy scipy scikit-learn
COPY train_data.csv /app/data/train_data.csv
