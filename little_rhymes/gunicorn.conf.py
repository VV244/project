import os

bind = f'0.0.0.0:{os.getenv("PORT", "8000")}'
workers = int(os.getenv('WEB_CONCURRENCY', '1'))
threads = int(os.getenv('GUNICORN_THREADS', '4'))
worker_class = 'gthread'
timeout = 60
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 100
errorlog = '-'
# Request URLs and adult contact fields are deliberately not logged here.
accesslog = None
capture_output = True
