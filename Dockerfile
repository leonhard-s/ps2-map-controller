FROM python:3.8-slim

# Copy Python module
COPY ./apl_backend /usr/src/backend/

# Install dependencies
COPY ./requirements.txt /usr/src/backend/
RUN pip install --no-cache-dir -r /usr/src/backend/requirements.txt

# Update working directory
WORKDIR /usr/src/backend/

# Run the application
CMD ["python3", "-m", "apl_backend"]
