#!/bin/bash

set -eu
APP_ENV="${APP_ENV:-}"

# Run inbuilt Django server if ENV is development
if [ "${APP_ENV^^}" = "DEVELOPMENT" ]; then

    # Install extra non-prod packages
    printf "\n" && echo "Installing dev dependencies for $APP_ENV"
    poetry install

    # Run developments
    printf "\n" && echo "Starting inbuilt django webserver"
    exec python manage.py runserver "0.0.0.0:${PORT:-8081}"
fi

# ===================
# Run Django/Gunicorn
# ===================
if [ "${APP_ENV^^}" = "PRODUCTION" ]; then

    # Run Gunicorn / Django
    printf "\n" && echo " Running Gunicorn / Django"
    exec gunicorn api.wsgi:application \
        --bind "0.0.0.0:${PORT:-8080}" \
        --workers "${GUNICORN_WORKERS:-2}" \
        --keep-alive 20 \
        --log-file - \
        --log-level info \
        --access-logfile - \
        --capture-output \
        --timeout 50
fi

echo "APP_ENV must be DEVELOPMENT or PRODUCTION" >&2
exit 1
