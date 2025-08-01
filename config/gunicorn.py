"""Enterprise Gunicorn configuration for production deployment"""

import multiprocessing
from os import getenv

# Server socket
bind = getenv('GUNICORN_BIND', '0.0.0.0:8000')
backlog = 2048

# Worker processes
workers = int(getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = getenv('GUNICORN_WORKER_CLASS', 'sync')
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Load application code before the worker processes are forked
preload_app = True

# Logging
accesslog = '-'
errorlog = '-'
loglevel = getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'coworking_platform'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = getenv('SSL_KEYFILE')
certfile = getenv('SSL_CERTFILE')

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)