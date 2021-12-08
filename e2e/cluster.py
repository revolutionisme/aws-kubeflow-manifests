import subprocess
import pytest

from e2e.utils import rand_name
from e2e.config import configure_resource_fixture

def create_cluster(cluster_name, region, cluster_version='1.19'):
    cmd = []
    cmd += "eksctl create cluster".split()
    cmd += f"--name {cluster_name}".split()
    cmd += f"--version {cluster_version}".split()
    cmd += f"--region {region}".split()
    cmd += "--node-type m5.xlarge".split()
    cmd += "--nodes 5".split()
    cmd += "--nodes-min 1".split()
    cmd += "--nodes-max 10".split()
    cmd += "--managed".split()

    retcode = subprocess.call(cmd)
    assert retcode == 0

def delete_cluster(cluster_name, region):
    cmd = []
    cmd += "eksctl delete cluster".split()
    cmd += f"--name {cluster_name}".split()
    cmd += f"--region {region}".split()

    retcode = subprocess.call(cmd)
    assert retcode == 0

@pytest.fixture(scope="class")
def cluster(metadata, region, request):
    cluster_name = rand_name("e2e-test-cluster-")

    def on_create():
        create_cluster(cluster_name, region)
    
    def on_delete():
        delete_cluster(cluster_name, region)

    configure_resource_fixture(metadata, request, cluster_name, 'cluster_name', on_create, on_delete)

    return cluster_name