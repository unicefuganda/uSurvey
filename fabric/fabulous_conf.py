import os.path

fabconf = {}

#  Do not edit
fabconf['FABULOUS_PATH'] = os.path.dirname(__file__)

# Hostname for instance
fabconf['SERVER_HOSTNAME'] = "mics-server"

# Username for connecting to instaces
fabconf['SERVER_USERNAME'] = "mics"

# Domain name
fabconf['DOMAIN_NAME'] = "app.mics"

# User home path
fabconf['DOMAIN_HOME'] = "/home/mics/%s" % fabconf['DOMAIN_NAME']

# Current Path
fabconf['CURRENT_PATH'] = "%s/current" % fabconf['DOMAIN_HOME']

# Releases Path
fabconf['RELEASES_PATH'] = "%s/releases" % fabconf['DOMAIN_HOME']

# Shared path
fabconf['SHARED_PATH'] = "%s/shared" % fabconf['DOMAIN_HOME']

# GIT URL
fabconf['GIT_URL'] = "git@github.com:unicefuganda/mics.git"

# Env file
fabconf['ENV_FILE'] = "pip-requires.txt"

# Full local path for .ssh
fabconf['SSH_PATH'] = "~/.ssh"

# Full local path for .ssh
fabconf['SSH_PRIVATE_KEY_PATH'] = "~/.ssh/mics_rsa"

# Project name: polls
fabconf['PROJECT_NAME'] = "mics"

# Where to install apps
fabconf['APPS_DIR'] = fabconf['DOMAIN_HOME']

# Where you want your project installed: /APPS_DIR/PROJECT_NAME
fabconf['PROJECT_PATH'] = fabconf['CURRENT_PATH']

# App domains
fabconf['DOMAINS'] = "mics.com www.mics.com"

# Path for virtualenvs
fabconf['VIRTUALENV_DIR'] = "/var/www/apps/env"

# Path for pip
fabconf['PIP_PATH'] = "/var/www/apps/env/mics/bin/pip"

# Email for the server admin
fabconf['ADMIN_EMAIL'] = "mics@thoughtworks.com"

# Git username for the server
fabconf['GIT_USERNAME'] = "mics-server"

# Name of the private key file used for github deployments
fabconf['GITHUB_DEPLOY_KEY_NAME'] = "id_rsa"

# Don't edit. Local path for deployment key you use for github
fabconf['GITHUB_DEPLOY_KEY_PATH'] = "%s/%s" % (fabconf['SSH_PATH'], fabconf['GITHUB_DEPLOY_KEY_NAME'])

# Path to the repo of the application you want to install
fabconf['GITHUB_REPO'] = "git@github.com:unicefuganda/mics.git"

# Virtualenv path
fabconf["VENV_PATH"] = "/var/www/apps/env/%s" % fabconf['PROJECT_NAME']

# Virtualenv activate command
fabconf['ACTIVATE'] = "source %s/bin/activate" % fabconf['VENV_PATH']

# Name tag for your server instance
fabconf['INSTANCE_NAME_TAG'] = "mics Server"