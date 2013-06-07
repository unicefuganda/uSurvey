#!/bin/bash
source /var/www/apps/env/mics/bin/activate
fab -f setup_environment.py ulous
fab -f deploy.py production deploy