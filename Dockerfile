# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables to avoid Python buffering issues
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY src /app/src

EXPOSE 8000

ENV MONGO_URI=""

# Copy the .env file into the container
COPY .env /app/.env


# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
