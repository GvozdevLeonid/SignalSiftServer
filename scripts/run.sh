#!/bin/sh
set -e

python manage.py wait_for_db
echo yes | python manage.py collectstatic
python manage.py migrate
python manage.py compilemessages

daphne --bind "0.0.0.0" app.asgi:application
