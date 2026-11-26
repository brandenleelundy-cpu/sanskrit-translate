FROM python:3.10-slim

# IndicTransToolkit compiles a small Cython extension
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces run as user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH HF_HOME=/home/user/.cache/huggingface
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY --chown=user app.py .

EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
