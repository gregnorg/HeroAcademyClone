FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home game
COPY server.py accounts.py rules.py dwarves.py bot.py ./
COPY public ./public
USER game
EXPOSE 8080
CMD ["sh", "-c", "python server.py && exec gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 90 --access-logfile - server:app"]
