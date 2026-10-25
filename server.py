import os

import psycopg
from flask import Flask, jsonify

app = Flask(__name__, static_folder="public", static_url_path="")


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/health")
def health():
    try:
        with psycopg.connect(
            host=os.environ["PGHOST"],
            dbname=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
            connect_timeout=3,
        ) as connection:
            connection.execute("SELECT 1").fetchone()
        return jsonify(app="online", database="connected")
    except (psycopg.Error, KeyError):
        app.logger.warning("Database health check failed")
        return jsonify(app="online", database="unavailable"), 503
