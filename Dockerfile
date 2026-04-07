# Base image with PyTorch, CUDA 12.4, and cuDNN 9
# FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including ffmpeg and other essentials)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy only the necessary application files
COPY *.py /app/
COPY router/asr_api.py /app/router/asr_api.py
COPY router/asr_front.py /app/router/asr_front.py
COPY requirements.txt /app/
COPY *.wav /app/

# update packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# install torch first
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# install requirements
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# expose port
EXPOSE 8101 9002

# set start command
CMD ["python", "main_server.py"]