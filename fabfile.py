from __future__ import with_statement
import os
from fabric.api import task, run, cd, env, local, hosts, settings, puts
from contextlib import contextmanager as _contextmanager
from fabric.context_managers import prefix

REPO_URI = 'git@github.com:fabiosussetto/holiday.git'
    
ENV_SETTINGS = {
    'dev': {
        'host': 'ec2-107-22-28-227.compute-1.amazonaws.com',
        'code_dir': '/home/ubuntu/holiday',
        'branch': 'master',
        'settings_template': 'dev_settings.py.template',
        'main_app_dir': 'holiday'
    }
}

@task
def set_hosts(target_env):
    env.hosts = [ENV_SETTINGS[target_env]['host']]


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
        if run("test -d %s" % env.remote_workdir).failed:
            run("git clone %s %s" % (REPO_URI, env.remote_workdir))
            
        if run("test -d %s" % env.virtualenv_dir).failed:
            run("virtualenv %s" % (env.virtualenv_dir))

def git_pull():
    with cd(env.remote_workdir):
        run("git pull origin %s" % env.git_branch)
        run("git checkout %s" % env.git_branch)
    
def pip_install():
    '''
    make sure libraries are uptodate
    '''
    with virtualenv():
        run("echo 'Current pip bin: ' && which pip")
        with cd(env.remote_workdir):
            run("pip install -r pip-requirements.txt")
        
def collect_static():
    with virtualenv():
        with cd(env.remote_workdir):
            run("python manage.py collectstatic --noinput")

def crontab_update():
    '''
    make sure crontab is reset with our crontab.txt settings
    FYI see cron.log for its output
    '''
    with cd(env.remote_workdir):
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
        with cd(env.remote_workdir):
            run("python manage.py syncdb --noinput")
            run("python manage.py migrate --all --noinput")

def delete_pyc():
    with cd(env.remote_workdir):
        run("find . -iname '*.pyc' -delete")
        
        
def select_settings():
    with cd(env.main_app_dir):
        settings_filename = env.settings_template.split('.template')[0]
        puts("Copying settings file template to %s" % settings_filename)
        run("find . -maxdepth 1 -type f -iname '*_settings.py' -delete")
        run("cp %s/%s %s" % (env.main_app_dir, env.settings_template, settings_filename))
        
@task
def deploy(target_env):
    # Specify fabric evn settings, according to the Jenkins Job name
    env.hosts = [ENV_SETTINGS[target_env]['host']]
    env.git_branch = ENV_SETTINGS[target_env]['branch']
    env.user = 'ubuntu'
    env.remote_workdir = ENV_SETTINGS[target_env]['code_dir']
    env.main_app_dir = os.path.join(env.remote_workdir, ENV_SETTINGS[target_env]['main_app_dir'])
    env.settings_template = ENV_SETTINGS[target_env]['settings_template']
    
    # Virtualenv variables
    env.virtualenv_dir = os.path.join(env.remote_workdir, 'virtualenv')
    
    bootstrap_project()
    git_pull()
    delete_pyc()
    pip_install()
    select_settings()
    migrate()
    collect_static()
    #crontab_update()
