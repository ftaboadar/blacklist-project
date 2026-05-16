FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# newrelic-admin run-program instrumenta gunicorn automáticamente
# La license_key viene de la variable de entorno NEW_RELIC_LICENSE_KEY
CMD ["newrelic-admin", "run-program", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "application:application"]
