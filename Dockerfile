FROM python:3.10-slim

RUN apt-get update && apt-get install -y libglib2.0-0 libgl1 libxcb1 libx11-6 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=7860

EXPOSE 7860

CMD ["python", "app.py"]
