import argparse
import os
import shutil
from typing import Any

import yaml
from azure.ai.ml import MLClient
from azure.identity import EnvironmentCredential
from azureml.core import Workspace
from azureml.core.authentication import ServicePrincipalAuthentication

from model_downloader.modify_requirements_script import (
    append_list_to_requirements,
    modify_requirements_file,
)


def copy_model_folder(source: str, dest: str):
    shutil.copytree(source, dest, dirs_exist_ok=True)


def download_model(
    ml_client: MLClient,
    model_name_to_download: str,
    model_version_to_download: str,
    model_download_location: str,
):
    ml_client.models.download(
        name=model_name_to_download,
        version=model_version_to_download,
        download_path=model_download_location,
    )


def load_config(config_file: str, config_secrets_file: str = None):
    with open(config_file, "r") as f:
        config_dict = yaml.safe_load(f)

    azure_config_dict = config_dict["azure_ml"]["dev"]
    os.environ["AZURE_TENANT_ID"] = azure_config_dict["service_principal_tenant_id"]
    os.environ["AZURE_CLIENT_ID"] = azure_config_dict["service_principal_client_id"]
    os.environ["AZURE_ML_SUBSCRIPTION_ID"] = azure_config_dict["azure_subscription_id"]
    os.environ["DEV_AZURE_ML_WORKSPACE_NAME"] = azure_config_dict["workspace_name"]
    os.environ["DEV_AZURE_ML_RESOURCE_GROUP_NAME"] = azure_config_dict[
        "resource_group_name"
    ]

    if config_secrets_file is not None:
        # in the pipeline the secrets will be saved
        # if run locally, argument azure-config-secrets-file must be provided
        with open(config_secrets_file, "r") as f:
            secrets_config_dict = yaml.safe_load(f)

        azure_secrets_config_dict = secrets_config_dict["azure_ml"]["dev"]
        os.environ["AZURE_CLIENT_SECRET"] = azure_secrets_config_dict[
            "service_principal_client_secret"
        ]


def get_config_dict(config_file: str) -> dict[str, Any]:
    with open(config_file, "r") as f:
        config_dict = yaml.safe_load(f)
    return config_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file", type=str)
    parser.add_argument("--config-secrets-file", type=str)
    args = parser.parse_args()

    config_file = args.config_file
    config_secrets_file = args.config_secrets_file
    load_config(config_file, config_secrets_file)
    config_dict = get_config_dict(config_file)

    download_params = config_dict["download_params"]

    sp_auth = ServicePrincipalAuthentication(
        tenant_id=os.environ["AZURE_TENANT_ID"],
        service_principal_id=os.environ["AZURE_CLIENT_ID"],
        service_principal_password=os.environ["AZURE_CLIENT_SECRET"],
    )
    ws = Workspace(
        subscription_id=os.environ["AZURE_ML_SUBSCRIPTION_ID"],
        resource_group=os.environ["DEV_AZURE_ML_RESOURCE_GROUP_NAME"],
        workspace_name=os.environ["DEV_AZURE_ML_WORKSPACE_NAME"],
        auth=sp_auth,
    )

    ml_client = MLClient(
        subscription_id=os.environ["AZURE_ML_SUBSCRIPTION_ID"],
        resource_group_name=os.environ["DEV_AZURE_ML_RESOURCE_GROUP_NAME"],
        workspace_name=os.environ["DEV_AZURE_ML_WORKSPACE_NAME"],
        credential=EnvironmentCredential(),
    )

    ml_client = MLClient(
        subscription_id=os.environ["AZURE_ML_SUBSCRIPTION_ID"],
        resource_group_name=os.environ["DEV_AZURE_ML_RESOURCE_GROUP_NAME"],
        workspace_name=os.environ["DEV_AZURE_ML_WORKSPACE_NAME"],
        credential=EnvironmentCredential(),
    )

    model_download_location = download_params["model_download_location"]

    model_name = config_dict["model_name"]
    model_version = config_dict["version"]

    download_model(
        ml_client,
        model_name,
        model_version,
        model_download_location,
    )

    requirements_file = os.path.join(
        model_download_location,
        model_name,
        "model",
        "requirements.txt",
    )
    torch_output_requirements_filename = os.path.join(
        model_download_location,
        model_name,
        "model",
        "torch_requirements.txt",
    )
    non_torch_output_requirements_filename = os.path.join(
        model_download_location,
        model_name,
        "model",
        "non_torch_requirements.txt",
    )

    modify_requirements_file(
        requirements_file=requirements_file,
        torch_output_requirements_filename=torch_output_requirements_filename,
        non_torch_output_requirements_filename=non_torch_output_requirements_filename,
    )

    append_list_to_requirements(
        requirements_file=non_torch_output_requirements_filename,
        requirements_to_append_as_list=download_params[
            "additional_non_torch_requirements"
        ],
    )

    copy_model_folder(
        os.path.join(model_download_location, model_name),
        os.path.join("st_app"),
    )

    shutil.rmtree(model_download_location)
