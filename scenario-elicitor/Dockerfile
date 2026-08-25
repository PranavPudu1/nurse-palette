FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Railway injects PORT; default for local docker runs.
CMD streamlit run app.py --server.port ${PORT:-8080} --server.address 0.0.0.0 \
    --server.headless true --server.runOnSave false \
    --browser.gatherUsageStats false
