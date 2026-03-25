FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    apache2 apache2-dev libapache2-mod-wsgi-py3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/DAR

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "wsgi.py"]
