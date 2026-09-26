FROM python:3.13.7-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/app/ .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]