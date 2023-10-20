# Use an official Python runtime as a base image
FROM python:3.9-slim-buster
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

ENV NAME World

# Run app.py when the container launches
CMD ["python", "script.py"]