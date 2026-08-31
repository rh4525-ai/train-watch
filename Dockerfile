FROM mcr.microsoft.com/playwright/python:v1.52.0-noble
WORKDIR /app
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "server.py"]
