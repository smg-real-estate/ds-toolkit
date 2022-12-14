#!/bin/bash

set -euxo pipefail

# PARAMETERS
EC2_HOME=/home/ec2-user
IDLE_TIME=7200
PATH_TO_AUTOSTOP_SCRIPT=${EC2_HOME}/autostop.py
CONDA_ENV_NAME=ds-smg-real-estate
CONDA_ENV_PATH=${EC2_HOME}/anaconda3/envs/${CONDA_ENV_NAME}
PRE_COMMIT_HOME=${EC2_HOME}/SageMaker/.cache/pre-commit
GIT_USER=$GIT_USER
GIT_EMAIL=$GIT_EMAIL

# OVERVIEW
# This part of the script creates separate conda env and install minimum amount of dependencies
sudo -u ec2-user -i <<EOF

echo "Creating conda env: ${CONDA_ENV_NAME}"
conda create --yes -n ${CONDA_ENV_NAME} pip ipykernel watchtower urllib3[secure] requests python=3.7.12 pre-commit nbdime
conda activate ${CONDA_ENV_NAME}
cd ${EC2_HOME}/SageMaker
projects=("ml-homegate-projects")
for project in \$projects; do
  pushd \$project
  if [ -e .pre-commit-config.yaml ]; then
    pre-commit install --install-hooks  
  fi
  git config --global user.email "${GIT_EMAIL}"
  git config --global user.name "${GIT_USER}"
  popd
done
EOF

# OVERVIEW
# This part of the script stops a SageMaker notebook once it's idle for more than 1 hour (default time)
# You can change the idle time for stop using the environment variable below.
# If you want the notebook the stop only if no browsers are open, remove the --ignore-connections flag
#
# Note that this script will fail if either condition is not met
#   1. Ensure the Notebook Instance has internet connectivity to fetch the example config
#   2. Ensure the Notebook Instance execution role permissions to SageMaker:StopNotebookInstance to stop the notebook 
#       and SageMaker:DescribeNotebookInstance to describe the notebook.

echo "Fetching the autostop script"
wget https://raw.githubusercontent.com/smg-real-estate/ds-toolkit/main/sagemaker/lifecycle/autostop.py -O ${PATH_TO_AUTOSTOP_SCRIPT}

echo "Starting the SageMaker autostop script in cron"
(crontab -l 2>/dev/null; echo "*/5 * * * * ${CONDA_ENV_PATH}/bin/python ${PATH_TO_AUTOSTOP_SCRIPT} --time ${IDLE_TIME} --ignore-connections") | crontab -

crontab -l
