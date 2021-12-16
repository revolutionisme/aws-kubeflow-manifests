"""
Client fixtures module
"""

import subprocess
import time
import requests

import pytest

from kubernetes import client, config
import kfp
import boto3
import mysql.connector

from e2e.utils.constants import (
    DEFAULT_HOST,
    DEFAULT_PASSWORD,
    DEFAULT_USER_NAMESPACE,
    DEFAULT_USERNAME,
)


def client_from_config(cluster, region):
    context = f"Administrator@{cluster}.{region}.eksctl.io"
    return config.new_client_from_config(context=context)


def k8s_core_api_client(cluster, region):
    """
    API client for interacting with k8s core API, e.g. describe_pods, etc.
    """

    return client.CoreV1Api(api_client=client_from_config(cluster, region))


def k8s_custom_objects_api_client(cluster, region):
    """
    API client for performing CRUD operations on custom resources.
    """

    return client.CustomObjectsApi(api_client=client_from_config(cluster, region))

def create_k8s_admission_registration_api_client(cluster, region):
    """
    API client for interacting with k8s core API, e.g. describe_pods, etc.
    """

    return client.AdmissionregistrationV1Api(api_client=client_from_config(cluster, region))


# todo make port random
@pytest.fixture(scope="class")
def port_forward(kustomize):
    """
    Opens port forwarding to the istio-ingressgateway to allow making requests
    to kubeflow components from localhost.

    Without this, services will need to be exposed via a public loadbalancer (e.g. ALB).
    """

    cmd = (
        "kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80".split()
    )
    proc = subprocess.Popen(cmd)
    time.sleep(10)  # Wait 10 seconds for port forwarding to open
    yield
    proc.terminate()


# Defaults, fixtures can be overriden if implemented in the test class
# E.g. create a new fixture in the class with the same name but different return value
#
# @pytest.fixture(scope="class")
# def host():
#     return "https://alb-address.abcd.com"
#


@pytest.fixture(scope="class")
def host():
    return DEFAULT_HOST


@pytest.fixture(scope="class")
def login():
    return DEFAULT_USERNAME


@pytest.fixture(scope="class")
def password():
    return DEFAULT_PASSWORD


# Not sure why this has to be set considering KFP is multi user
@pytest.fixture(scope="class")
def client_namespace():
    return DEFAULT_USER_NAMESPACE


@pytest.fixture(scope="class")
def session_cookie(port_forward, host, login, password):
    session = requests.Session()
    response = session.get(host)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"login": login, "password": password}
    session.post(response.url, headers=headers, data=data)
    session_cookie = session.cookies.get_dict()["authservice_session"]

    return session_cookie


@pytest.fixture(scope="class")
def kfp_client(port_forward, host, client_namespace, session_cookie):
    """
    Kubeflow pipelines client. Requires portforwarding to call from localhost.
    """

    client = kfp.Client(
        host=f"{host}/pipeline",
        cookies=f"authservice_session={session_cookie}",
        namespace=client_namespace,
    )
    client._context_setting[
        "namespace"
    ] = client_namespace  # needs to be set for list_experiments

    return client


@pytest.fixture(scope="class")
def cfn_client(region):
    return boto3.client("cloudformation", region_name=region)


@pytest.fixture(scope="class")
def ec2_client(region):
    return boto3.client("ec2", region_name=region)

@pytest.fixture(scope="class")
def s3_client(region):
    return boto3.client("s3", region_name=region)


def create_mysql_client(user, password, host, database) ->  mysql.connector.MySQLConnection:
    return mysql.connector.connect(user=user, password=password,
                              host=host,
                              database=database)