#!/usr/bin/env python
import os
import time
import psycopg2
from psycopg2 import OperationalError

def wait_for_db():
    db_conn = None
    while not db_conn:
        try:
            db_conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'db'),
                port=os.environ.get('DB_PORT', '5432'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'password'),
                database=os.environ.get('DB_NAME', 'cwspaces')
            )
            print("Database connection successful!")
        except OperationalError:
            print("Database unavailable, waiting 1 second...")
            time.sleep(1)

if __name__ == "__main__":
    wait_for_db()