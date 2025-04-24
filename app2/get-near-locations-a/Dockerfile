# Use a base image of Python
FROM python:3.9-slim

# Install MySQL connector and other dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and establish working dir
WORKDIR /function

# Copy th code of the function to the container
COPY . .

# Install necessary dependencies, if there is equirements.txt
RUN pip install -r requirements.txt

# Expose port of the function (if necessary)
EXPOSE 8080

# Command to execute the function (using http template)
CMD ["python3", "get-near-locations-a.py"]

