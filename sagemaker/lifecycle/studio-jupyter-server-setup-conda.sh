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
PRE_COMMIT_HOME=${HOME}/.cache/pre-commit
KERNELS_DIR=${HOME}/.kernels
MICROMAMBA_URL=https://micromamba.snakepit.net/api/micromamba/linux-64/latest

if [ ! -d $HOME/.micromamba ]; then
    mkdir $HOME/.micromamba \
    && pushd $HOME/.micromamba \
    && (curl -Ls $MICROMAMBA_URL | tar -xvj bin/micromamba) \
    && popd
fi

pushd $HOME/ds-toolkit && git pull && popd
cp $HOME/ds-toolkit/sagemaker/lifecycle/bashrc-studio.sh $HOME/.micromamba/bashrc-studio.sh
source $HOME/.micromamba/bashrc-studio.sh

micromamba config append channels conda-forge
micromamba config append channels defaults
micromamba config append envs_dirs $HOME/.conda/envs
micromamba config append envs_dirs $KERNELS_DIR

KERNEL_NAME="smg-re"
PYTHON_VERSIONS=("3.9" "3.10")

for python_version in ${PYTHON_VERSIONS[@]}; do
    ENV_NAME="${KERNEL_NAME}-py${python_version}"
    micromamba create -q -y python=${python_version} \
      -p $KERNELS_DIR/$ENV_NAME \
      ipykernel watchtower urllib3[secure] requests pre-commit nbdime -c conda-forge

    micromamba run -r $KERNELS_DIR/$ENV_NAME \
      python -m ipykernel install --user --name "$ENV_NAME" \
      --display-name "Python (${ENV_NAME})"
done

cd ${HOME}

py310_projects=("ds-projects")

for project in ${py310_projects[@]}; do
  if [ -d $project ]; then
      pushd $project
      if [ -e .pre-commit-config.yaml ]; then
      micromamba run -r "${KERNELS_DIR}/${KERNEL_NAME}-py3.10" \
        pre-commit install --install-hooks  
      fi
      popd
  fi
done

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
