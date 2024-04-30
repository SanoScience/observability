from dockerspawner import DockerSpawner
from nativeauthenticator import NativeAuthenticator
import os

c.JupyterHub.authenticator_class = NativeAuthenticator


c.GenericOAuthenticator.enable_auth_state = True
c.Spawner.http_timeout = 300
c.JupyterHub.log_level = 'DEBUG'
c.JupyterHub.hub_ip = '0.0.0.0'

c.DockerSpawner.network_name = 'jupyterhub'

c.DockerSpawner.remove = True

c.JupyterHub.spawner_class = DockerSpawner
c.NativeAuthenticator.create_system_users = True


notebook_dir = os.environ.get('DOCKER_NOTEBOOK_DIR') or '/home/jovyan/work'
c.Spawner.notebook_dir = notebook_dir

c.DockerSpawner.volumes = { 'jupyterhub-user-{username}': notebook_dir }
c.DockerSpawner.image = "observability_image"

# Persistence
#c.JupyterHub.db_url = "sqlite:///data/jupyterhub.sqlite"

# Enable user registration
c.Authenticator.allowed_users = set()
c.Authenticator.admin_users = {'myadmin'}
c.NativeAuthenticator.open_signup = True

c.JupyterHub.bind_url = 'http://:7601'

c.DockerSpawner.environment.update(
    {
        "JUPYTER_PREFER_ENV_PATH": "0",
    }
)


c.DockerSpawner.volumes = {
    '/home/ubuntu/conf/shared_resources': '/home/jovyan/scripts',
    '/home/ubuntu/conf/shared_resources/notebooks': notebook_dir
}