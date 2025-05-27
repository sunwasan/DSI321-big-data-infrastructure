FROM python:3.9-slim

WORKDIR /frontend

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . /frontend/

# Create expected directories
RUN mkdir -p /data /config

# Add debug script to help troubleshoot
RUN echo '#!/bin/bash\necho "Listing directories:"\nls -la /\nls -la /data\nls -la /src\nls -la /frontend' > /frontend/debug.sh && \
    chmod +x /frontend/debug.sh

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["streamlit", "run", "streamlit.py", "--server.port=8501", "--server.address=0.0.0.0", "--logger.level=debug"]
