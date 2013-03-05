from fabric.context_managers import cd
from fabric.decorators import task
from fabric.operations import run
from fabric.state import env


env.use_ssh_config = True
env.hosts = ['lt-web1', 'lt-web2']


# TODO: remove servers from the load balancer
# TODO: run migrations and syncdb
@task(default=True)
def deploy_staging():
    git_pull_develop()
    cycle_uwsgi()


@task
def git_pull_develop():
    with cd('/web/bltalk'):
        run('git checkout fdb')
        run('git pull origin fdb')


@task
def cycle_uwsgi():
    run('sudo supervisorctl restart uwsgi')