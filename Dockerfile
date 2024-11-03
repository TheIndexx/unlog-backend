# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Install tini
RUN apt-get update && apt-get install -y tini && apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY app/requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the webhook server's code into the container
COPY app/ .

# Set environment variables
ENV PYTHONUNBUFFERED=1

EXPOSE 80

# Use tini to manage zombie processes and signal forwarding
ENTRYPOINT ["/usr/bin/tini", "--"]

# Add a healthcheck
#HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#    CMD curl -f http://localhost:80/health || exit 1

# Run the FastAPI server on port 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]