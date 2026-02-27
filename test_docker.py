import pytest
import docker

def test_docker_container():
    client = docker.from_env()
    container = client.containers.run('library-management-system', detach=True)
    assert container.status == 'running'