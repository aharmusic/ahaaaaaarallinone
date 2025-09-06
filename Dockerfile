FROM python:3.13-slim

# Install OpenGL (libGL) dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of your application
COPY . /app
WORKDIR /app

CMD ["python", "run.py"]
