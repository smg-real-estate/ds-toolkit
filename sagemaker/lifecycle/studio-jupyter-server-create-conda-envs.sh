#!/bin/bash

set -euxo pipefail

PRE_COMMIT_HOME=${HOME}/.cache/pre-commit
KERNELS_DIR=${HOME}/.kernels

if [ -f $HOME/ds-toolkit/sagemaker/lifecycle/bashrc-studio.sh ]; then
  ln -sf $HOME/ds-toolkit/sagemaker/lifecycle/bashrc-studio.sh ~/.bash_profile
  source ~/.bash_profile

  micromamba config append channels conda-forge
  micromamba config append channels defaults
  micromamba config append envs_dirs $KERNELS_DIR
  micromamba config append envs_dirs $HOME/.conda/envs

  ################### Create conda environments #######################
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

  ################### Install pre-commit hooks ########################
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

  py39_projects=("managed-airflow" "data-platform")

  for project in ${py39_projects[@]}; do
    if [ -d $project ]; then
        pushd $project
        if [ -e .pre-commit-config.yaml ]; then
          micromamba run -r "${KERNELS_DIR}/${KERNEL_NAME}-py3.9" \
            pre-commit install --install-hooks  
        fi
        popd
    fi
  done
fi
