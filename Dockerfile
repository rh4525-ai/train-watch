FROM mcr.microsoft.com/playwright/python:v1.52.0-noble
WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "server.py"]
