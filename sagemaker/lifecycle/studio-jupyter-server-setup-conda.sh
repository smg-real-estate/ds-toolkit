#!/bin/bash

set -euxo pipefail

# OVERVIEW
# This script installs a custom, persistent installation of conda on the Notebook Instance's EBS volume, and ensures
# that these custom environments are available as kernels in Jupyter.
# 
# The on-create script downloads and installs a custom conda installation to the EBS volume via Miniconda. Any relevant
# packages can be installed here.
#   1. ipykernel is installed to ensure that the custom environment can be used as a Jupyter kernel   
#   2. Ensure the Notebook Instance has internet connectivity to download the Miniconda installer



# Install a separate conda installation via Miniconda
SAGEMAKER_HOME=/home/sagemaker-user
PRE_COMMIT_HOME=${SAGEMAKER_HOME}/.cache/pre-commit
KERNELS_DIR=$SAGEMAKER_HOME/.kernels
MICROMAMBA_URL=https://micromamba.snakepit.net/api/micromamba/linux-64/latest

if [ ! -d $SAGEMAKER_HOME/.micromamba ]; then
    mkdir $SAGEMAKER_HOME/.micromamba \
    && pushd $SAGEMAKER_HOME/.micromamba \
    && (curl -Ls $MICROMAMBA_URL | tar -xvj bin/micromamba) \
    && popd
fi

pushd $SAGEMAKER_HOME/ds-toolkit && git pull && popd
# source $SAGEMAKER_HOME/ds-toolkit/sagemaker/lifecycle/bashrc

# KERNEL_NAME="smg-re"
# PYTHON_VERSIONS=("3.9" "3.10")

# for python_version in ${PYTHON_VERSIONS[@]}; do
#     ENV_NAME="${KERNEL_NAME}-py${python_version}"
#     micromamba create -q -y python=${python_version} \
#       -p $KERNELS_DIR/$ENV_NAME \
#       ipykernel watchtower urllib3[secure] requests pre-commit nbdime
#    
#     micromamba activate $KERNELS_DIR/$ENV_NAME
#     python -m ipykernel install --user --name "$ENV_NAME" \
#     --display-name "Python (${ENV_NAME})"
# done

# cd ${SAGEMAKER_HOME}/SageMaker

# py310_projects=("ml-homegate-projects")
# micromamba activate "${KERNELS_DIR}/${KERNEL_NAME}-py3.10"

# for project in ${py310_projects[@]}; do
#   if [ -d $project ]; then
#       pushd $project
#       if [ -e .pre-commit-config.yaml ]; then
#         pre-commit install --install-hooks  
#       fi
#       popd
#   fi
# done

# py39_projects=("managed-airflow" "data-platform")
# micromamba activate "${KERNELS_DIR}/${KERNEL_NAME}-py3.9"

# for project in ${py39_projects[@]}; do
#   if [ -d $project ]; then
#       pushd $project
#       if [ -e .pre-commit-config.yaml ]; then
#         pre-commit install --install-hooks  
#       fi
#       popd
#   fi
# done
