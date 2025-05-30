# Start with an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app_backend

# Copy the requirements file into the container at /app_backend
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app_backend
COPY ./app /app_backend/app

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV MODULE_NAME="app.main"
ENV VARIABLE_NAME="app"

# Run main.py when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
