FROM python:3.12-slim AS backend
WORKDIR /app
COPY services/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services/backend ./services/backend
ENV PYTHONPATH=/app/services/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765", "--app-dir", "services/backend"]
