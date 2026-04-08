# Use a slim version of Python 3.11 for a smaller image size
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies if your tasks require them (optional)
# RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir fastapi uvicorn pydantic

# Copy the rest of the application code
COPY . .

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Hugging Face Spaces and many cloud providers expect port 7860
EXPOSE 7860

# Run the FastAPI server using the module path
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]