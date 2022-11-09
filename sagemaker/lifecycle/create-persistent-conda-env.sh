#!/bin/bash

set -euxo pipefail

EC2_HOME=/home/ec2-user
CONDA_ENV_NAME=ds-smg-real-estate
CONDA_ENV_PATH=${EC2_HOME}/anaconda3/envs/${CONDA_ENV_NAME}
PRE_COMMIT_HOME=${EC2_HOME}/SageMaker/.cache/pre-commit
# OVERVIEW
# This script installs a custom, persistent installation of conda on the Notebook Instance's EBS volume, and ensures
# that these custom environments are available as kernels in Jupyter.
# 
# The on-create script downloads and installs a custom conda installation to the EBS volume via Miniconda. Any relevant
# packages can be installed here.
#   1. ipykernel is installed to ensure that the custom environment can be used as a Jupyter kernel   
#   2. Ensure the Notebook Instance has internet connectivity to download the Miniconda installer


sudo -u ec2-user -i <<'EOF'
unset SUDO_UID

# Install a separate conda installation via Miniconda
WORKING_DIR=/home/ec2-user/SageMaker/custom-miniconda
mkdir -p "$WORKING_DIR"
wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh -O "$WORKING_DIR/miniconda.sh"
bash "$WORKING_DIR/miniconda.sh" -b -u -p "$WORKING_DIR/miniconda" 
rm -rf "$WORKING_DIR/miniconda.sh"


# Create a custom conda environment
source "$WORKING_DIR/miniconda/bin/activate"
KERNEL_NAME="smg-real-estate"
PYTHON_VERSIONS=("3.7" "3.8" "3.9")

for python_version in \$PYTHON_VERSIONS; do
    conda create -y -n "${KERNEL_NAME}-py\${python_version}" python=\${python_version} \
      ipykernel watchtower urllib3[secure] requests pre-commit nbdime
    conda activate "${KERNEL_NAME}-py\${python_version}"
    python -m ipykernel install --user --name "${KERNEL_NAME}-py\${python_version}" \
      --display-name "Python (\${python_version}) (${KERNEL_NAME})"
done

cd ${EC2_HOME}/SageMaker
py37_projects=("ml-homegate-projects")
conda activate "${KERNEL_NAME}-py37"
for project in \$py37_projects; do
  pushd \$project
  if [ -e .pre-commit-config.yaml ]; then
    pre-commit install --install-hooks  
  fi
  popd
done
py39_projects=("managed-airflow" "data-platform")
conda activate "${KERNEL_NAME}-py39"
for project in \$py39_projects; do
  pushd \$project
  if [ -e .pre-commit-config.yaml ]; then
    pre-commit install --install-hooks  
  fi
  popd
done
EOF
