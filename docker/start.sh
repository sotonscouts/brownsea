#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

export DJANGO_SETTINGS_MODULE=brownsea.core.settings.production

cd /app

python /app/manage.py migrate

granian --interface wsgi brownsea.core.wsgi:application --workers 2 --host 0.0.0.0 --port 8000