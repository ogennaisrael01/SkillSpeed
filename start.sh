#!/bin/bash
# 1. Kill any existing processes
fuser -k 3000/tcp || true
pkill -f celery || true

# 2. Set the path so Python finds your 'core' folder inside 'src'
export PYTHONPATH=$PYTHONPATH:/home/runner/workspace/src

# 3. Go to the source directory
cd /home/runner/workspace/src

# 4. Start Celery worker and beat in the background
celery -A core worker --loglevel=info &
celery -A core beat --loglevel=info &

# 5. Start Gunicorn (The main process that keeps the deployment alive)
exec gunicorn --bind 0.0.0.0:3000 --reuse-port core.wsgi:application
