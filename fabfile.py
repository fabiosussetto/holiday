from __future__ import with_statement
import os
import sys
from fabric.api import task, run, cd, env, local, hosts, settings, puts
from contextlib import contextmanager as _contextmanager
from fabric.context_managers import prefix

REPO_URI = 'git@bynd.beanstalkapp.com:/novartis_moderator.git'
    
ENV_SETTINGS = {
    'dev': {
        'host': 'ec2-107-22-28-227.compute-1.amazonaws.com',
        'code_dir': '/home/ubuntu/holiday',
        'branch': 'master',
        'settings_template': 'dev_settings.py.template'
    }
}

@_contextmanager
def virtualenv():
    """
    Define a python 'with' context manager to handle
    virtualenv activation before the nested commands.
    Since fabric runs on ssh, it's not enough to call 'source bin/activate'
    just one, as the shell will 'forget' this for the following commands.
    """
    with prefix('source %s/bin/activate' % env.virtualenv_dir):
        yield

def bootstrap_project():
    """
    Common operations to be performed the first time
    the project is initialised.
    """
    with settings(warn_only=True):
        if run("test -d %s" % code_dir).failed:
            run("git clone %s %s" % (REPO_URI, code_dir))
            
        if run("test -d %s" % env.virtualenv_dir).failed:
            run("virtualenv %s" % (env.virtualenv_dir))

def git_pull():
    with cd(code_dir):
        run("git pull origin %s" % ENV_SETTINGS['branch'])
        run("git checkout %s" % ENV_SETTINGS['branch'])
    
def pip_install():
    '''
    make sure libraries are uptodate
    '''
    with virtualenv():
        run("echo 'Current pip bin: ' && which pip")
        with cd(code_dir):
            run("pip install -r pip-requirements.txt")
        
def collect_static():
    with virtualenv():
        with cd(code_dir):
            run("python manage.py collectstatic --noinput")

def crontab_update():
    '''
    make sure crontab is reset with our crontab.txt settings
    FYI see cron.log for its output
    '''
    with cd(code_dir):
        with settings(warn_only=True):
            run("sudo crontab -r")
            run("sudo crontab crontab.txt")
            run("sudo crontab -l")

def migrate():
    '''
    do the django south database migration
    this keeps the db schema uptodate
    '''
    with virtualenv():
        with cd(code_dir):
            run("python manage.py syncdb --noinput")
            run("python manage.py migrate --all --noinput")

def delete_pyc():
    with cd(code_dir):
        run("find . -iname '*.pyc' -delete")
        
        
def select_settings():
    with cd(code_dir):
        settings_filename = ENV_SETTINGS['settings_template'].split('.template')[0]
        puts("Copying settings file template to %s" % settings_filename)
        run("find . -maxdepth 1 -type f -iname '*_settings.py' -delete")
        run("cp env_settings/%s %s" % (ENV_SETTINGS['settings_template'], settings_filename))
        
@task
def deploy(env):
    code_dir = ENV_SETTINGS['code_dir']
    
    # Specify fabric evn settings, according to the Jenkins Job name
    env.hosts = [ENV_SETTINGS['host']]
    env.user = 'ubuntu'
    env.remote_workdir = code_dir
    
    # Virtualenv variables
    env.virtualenv_dir = os.path.join(code_dir, 'virtualenv')
    
    bootstrap_project()
    git_pull()
    delete_pyc()
    pip_install()
    select_settings()
    migrate()
    collect_static()
    crontab_update()
