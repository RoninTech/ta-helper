# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a directory for ta-helper
RUN mkdir ta-helper

# Copy the ta-helper scripts into the Docker image
COPY ta-helper-trigger.py /usr/src/app/ta-helper/
COPY ta-helper.py /usr/src/app/ta-helper/

# Set the working directory to the ta-helper directory
WORKDIR /usr/src/app/ta-helper

# Set environment variable for the script path
ENV TA_HELPER_SCRIPT=/usr/src/app/ta-helper/ta-helper.py
ENV APPRISE_TRIGGER_PORT=8001

# Make port 8001 available to the world outside this container
EXPOSE 8001

# Command to run the ta-helper trigger script
CMD ["python", "./ta-helper-trigger.py"]