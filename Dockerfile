FROM python:3.8-slim

# Copy Python module
COPY ./apl_backend /usr/src/backend/apl_backend/

# Install dependencies
COPY ./requirements.txt /usr/src/backend/
WORKDIR /usr/src/backend/
RUN pip install --no-cache-dir -r /usr/src/backend/requirements.txt

# Run the application
CMD cd /usr/src/backend/ && python3 -m apl_backend
