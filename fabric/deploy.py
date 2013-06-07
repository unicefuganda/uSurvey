from fabric.api import env, run, sudo, local, put
from fabulous_conf import *

def production():
    """Defines production environment"""
    env.user = fabconf['SERVER_USERNAME']
    env.key_filename = fabconf['SSH_PRIVATE_KEY_PATH']
    env.hosts = [fabconf['SERVER_HOSTNAME'], ]
    env.base_dir = fabconf['APPS_DIR']
    env.app_name = fabconf['PROJECT_NAME']
    env.domain_name = fabconf['DOMAIN_NAME']
    env.domain_path = fabconf['DOMAIN_HOME']
    env.current_path = fabconf['CURRENT_PATH']
    env.releases_path = fabconf['RELEASES_PATH']
    env.shared_path = fabconf['SHARED_PATH']
    env.git_clone = fabconf['GIT_URL']
    env.env_file = fabconf['ENV_FILE']

def releases():
    """List a releases made"""
    env.releases = sorted(run('ls -x %(releases_path)s' % { 'releases_path':env.releases_path }).split())
    if len(env.releases) >= 1:
        env.current_revision = env.releases[-1]
        env.current_release = "%(releases_path)s/%(current_revision)s" % { 'releases_path':env.releases_path, 'current_revision':env.current_revision }
    if len(env.releases) > 1:
        env.previous_revision = env.releases[-2]
        env.previous_release = "%(releases_path)s/%(previous_revision)s" % { 'releases_path':env.releases_path, 'previous_revision':env.previous_revision }

def start():
    """Start the application servers"""
    sudo("supervisorctl start mics")

def restart():
    """Restarts your application"""
    sudo("supervisorctl restart mics")

def stop():
    """Stop the application servers"""
    sudo("supervisorctl stop mics")

def permissions():
    """Make the release group-writable"""
    sudo("chmod -R g+w %(domain_path)s" % { 'domain_path':env.domain_path })
    sudo("chown -R mics:mics %(domain_path)s" % { 'domain_path':env.domain_path })

def setup():
    """Prepares one or more servers for deployment"""
    run("mkdir -p %(domain_path)s/{releases,shared}" % { 'domain_path':env.domain_path })
    run("mkdir -p %(shared_path)s/{system,log,index}" % { 'shared_path':env.shared_path })
    permissions()

def checkout():
    """Checkout code to the remote servers"""
    from time import time
    env.current_release = "%(releases_path)s/%(time).0f" % { 'releases_path':env.releases_path, 'time':time() }
    run("cd %(releases_path)s; git clone -q -o deploy --depth 1 %(git_clone)s %(current_release)s" % { 'releases_path':env.releases_path, 'git_clone':env.git_clone, 'current_release':env.current_release })

def update():
    """Copies your project and updates environment and symlink"""
    update_code()
    update_env()
    symlink()
    permissions()

def update_code():
    """Copies your project to the remote servers"""
    checkout()
    permissions()

def symlink():
    """Updates the symlink to the most recently deployed version"""
    if not env.has_key('current_release'):
        releases()
    run("rm -f %(current_path)s" % { 'current_path':env.current_path })
    run("ln -nfs %(current_release)s %(current_path)s" % { 'current_release':env.current_release, 'current_path':env.current_path })
    place_gunicorn_conf()
    run("ln -nfs %(shared_path)s/log %(current_release)s/log" % { 'shared_path':env.shared_path, 'current_release':env.current_release })
    run("ln -nfs %(shared_path)s/index %(current_release)s/index" % { 'shared_path':env.shared_path, 'current_release':env.current_release })
    run("ln -nfs %(shared_path)s/cdlm.db %(current_release)s/cdlm.db" % { 'shared_path':env.shared_path, 'current_release':env.current_release })
    run("ln -nfs %(shared_path)s/system/local.py %(current_release)s/%(app_name)s/local.py" % { 'shared_path':env.shared_path, 'current_release':env.current_release, 'app_name':env.app_name })
    # run("ln -nfs %(virtual_env)s/src/django/django/contrib/admin/media %(current_release)s/%(app_name)s/media/admin" % { 'virtual_env': fabconf["VENV_PATH"], 'current_release':env.current_release, 'app_name':env.app_name })
    copy_local_settings()

def place_gunicorn_conf():
    """Upload gunicorn conf file"""
    local_path = "%s/templates/gunicorn.conf.py" % fabconf['FABULOUS_PATH']
    remote_path = "%s/gunicorn.conf.py" % fabconf['PROJECT_PATH']
    put(local_path, remote_path)

def activate_virtualenv():
    """Activate virtual env"""
    run(fabconf['ACTIVATE'])

def update_env():
    """Update servers environment on the remote servers"""
    if not env.has_key('current_release'):
        releases()
    activate_virtualenv()
    run("%(pip_path)s install -r %(current_release)s/%(env_file)s" % { 'pip_path': fabconf['PIP_PATH'], 'current_release':env.current_release, 'env_file':env.env_file })
    permissions()

def migrate():
    """Run the migrate task"""
    if not env.has_key('current_release'):
        releases()
    run("%(pip_activate)s; cd %(current_release)s; python manage.py migrate" % { 'pip_activate': fabconf['ACTIVATE'], 'current_release':env.current_path })

def migrations():
    """Deploy and run pending migrations"""
    update_code()
    update_env()
    symlink()
    migrate()
    restart()

def cleanup():
    """Clean up old releases"""
    if not env.has_key('releases'):
        releases()
    if len(env.releases) > 3:
        directories = env.releases
        directories.reverse()
        del directories[:3]
        env.directories = ' '.join([ "%(releases_path)s/%(release)s" % { 'releases_path':env.releases_path, 'release':release } for release in directories ])
        run("rm -rf %(directories)s" % { 'directories':env.directories })

def enable():
    """Makes the application web-accessible again"""
    run("rm %(shared_path)s/system/maintenance.html" % { 'shared_path':env.shared_path })

def disable(**kwargs):
    """Present a maintenance page to visitors"""
    import os, datetime
    from django.conf import settings
    try:
        settings.configure(
            DEBUG=False, TEMPLATE_DEBUG=False,
            TEMPLATE_DIRS=(os.path.join(os.getcwd(), 'templates/'),)
        )
    except EnvironmentError:
        pass
    from django.template.loader import render_to_string
    env.deadline = kwargs.get('deadline', None)
    env.reason = kwargs.get('reason', None)
    open("maintenance.html", "w").write(
        render_to_string("maintenance.html", { 'now':datetime.datetime.now(), 'deadline':env.deadline, 'reason':env.reason }).encode('utf-8')
    )
    put('maintenance.html', '%(shared_path)s/system/maintenance.html' % { 'shared_path':env.shared_path })
    local("rm maintenance.html")

def rollback_code():
    """Rolls back to the previously deployed version"""
    if not env.has_key('releases'):
        releases()
    if len(env.releases) >= 2:
        env.current_release = env.releases[-1]
        env.previous_revision = env.releases[-2]
        env.current_release = "%(releases_path)s/%(current_revision)s" % { 'releases_path':env.releases_path, 'current_revision':env.current_revision }
        env.previous_release = "%(releases_path)s/%(previous_revision)s" % { 'releases_path':env.releases_path, 'previous_revision':env.previous_revision }
        run("rm %(current_path)s; ln -s %(previous_release)s %(current_path)s && rm -rf %(current_release)s" % { 'current_release':env.current_release, 'previous_release':env.previous_release, 'current_path':env.current_path })

def copy_local_settings():
    run("cp %(current_path)s/mics/localsettings.py.example %(current_path)s/mics/localsettings.py" % {'current_path':env.current_path })
    run("cp %(current_path)s/survey/investigator_configs.py.example %(current_path)s/survey/investigator_configs.py" % {'current_path':env.current_path })

def rollback():
    """Rolls back to a previous version and restarts"""
    rollback_code()
    restart()

def cold():
    """Deploys and starts a `cold' application"""
    update()
    migrate()
    start()

def deploy():
    """Deploys your project. This calls both `update' and `restart'"""
    update()
    restart()