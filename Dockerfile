FROM python:3.8-slim

# Copy Python module
COPY ./controller /usr/src/controller/controller/

# Install dependencies
COPY ./requirements.txt /usr/src/backend/
WORKDIR /usr/src/controller/
RUN pip install --no-cache-dir -r /usr/src/controller/requirements.txt

# Run the application
CMD cd /usr/src/controller/ && python3 -m controller
