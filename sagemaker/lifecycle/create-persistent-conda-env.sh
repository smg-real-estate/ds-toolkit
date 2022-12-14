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
EC2_HOME=/home/ec2-user
PRE_COMMIT_HOME=${EC2_HOME}/SageMaker/.cache/pre-commit
KERNELS_DIR=$EC2_HOME/SageMaker/.kernels

if [ ! -d $EC2_HOME/SageMaker/micromamba ]; then
    mkdir $EC2_HOME/SageMaker/micromamba && pushd $EC2_HOME/SageMaker/micromamba
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba
    popd
fi

source $EC2_HOME/SageMaker/ds-toolkit/sagemaker/lifecycle/bashrc

KERNEL_NAME="smg-re"
PYTHON_VERSIONS=("3.7" "3.8" "3.9" "3.10")

for python_version in ${PYTHON_VERSIONS[@]}; do
    ENV_NAME="${KERNEL_NAME}-py${python_version}"
    micromamba create -y python=${python_version} \
      -p $KERNELS_DIR/$ENV_NAME \
      ipykernel watchtower urllib3[secure] requests pre-commit nbdime
   
    micromamba activate $KERNELS_DIR/$ENV_NAME
    python -m ipykernel install --user --name "$ENV_NAME" \
    --display-name "Python (${ENV_NAME})"
done

cd ${EC2_HOME}/SageMaker

py37_projects=("ml-homegate-projects")
conda activate "${KERNEL_NAME}-py3.7"

for project in ${py37_projects[@]}; do
  pushd $project
  if [ -e .pre-commit-config.yaml ]; then
    pre-commit install --install-hooks  
  fi
  popd
done

py39_projects=("managed-airflow" "data-platform")
conda activate "${KERNEL_NAME}-py3.9"

for project in ${py39_projects[@]}; do
  pushd $project
  if [ -e .pre-commit-config.yaml ]; then
    pre-commit install --install-hooks  
  fi
  popd
done
