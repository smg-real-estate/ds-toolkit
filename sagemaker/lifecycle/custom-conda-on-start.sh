#!/bin/bash
set -euxo pipefail
# OVERVIEW
# This script installs a custom, persistent installation of conda on the Notebook Instance's EBS volume, and ensures
# that these custom environments are available as kernels in Jupyter.
# 
# The on-start script uses the custom conda environment created in the on-create script and uses the ipykernel package

# to add that as a kernel in Jupyter.

#

# For another example, see:
# https://docs.aws.amazon.com/sagemaker/latest/dg/nbi-add-external.html#nbi-isolated-environment
WORKING_DIR=/home/ec2-user/SageMaker/custom-miniconda
PATH=$WORKING_DIR/miniconda/bin:$PATH
GIT_USER=$GIT_USER
GIT_EMAIL=$GIT_EMAIL
sudo -u ec2-user -i <<'EOF'
unset SUDO_UID

git config --global user.email "${GIT_EMAIL}"
git config --global user.name "${GIT_USER}"
git config --global pull.rebase true

WORKING_DIR=/home/ec2-user/SageMaker/custom-miniconda
PATH=$WORKING_DIR/miniconda/bin:$PATH
source "$WORKING_DIR/miniconda/bin/activate"

for env in $WORKING_DIR/miniconda/envs/*; do

BASENAME=$(basename "$env")
source activate "$BASENAME"

python -m ipykernel install --user --name "$BASENAME" --display-name "Python (${BASENAME})"
done
# Optionally, uncomment these lines to disable SageMaker-provided Conda functionality.

# echo "c.EnvironmentKernelSpecManager.use_conda_directly = False" >> /home/ec2-user/.jupyter/jupyter_notebook_config.py

# rm /home/ec2-user/.condarc
EOF
echo "Restarting the Jupyter server.."
systemctl restart jupyter-server

# OVERVIEW
# This part of the script stops a SageMaker notebook once it's idle for more than 1 hour (default time)
# You can change the idle time for stop using the environment variable below.
# If you want the notebook the stop only if no browsers are open, remove the --ignore-connections flag
#
# Note that this script will fail if either condition is not met
#   1. Ensure the Notebook Instance has internet connectivity to fetch the example config
#   2. Ensure the Notebook Instance execution role permissions to SageMaker:StopNotebookInstance to stop the notebook 
#       and SageMaker:DescribeNotebookInstance to describe the notebook.

EC2_HOME=/home/ec2-user
IDLE_TIME=7200
CONDA_ENV_NAME=smg-re-py3.7
CONDA_ENV_PATH=${WORKING_DIR}/miniconda/envs/${CONDA_ENV_NAME}
echo "Fetching the autostop script"
wget https://raw.githubusercontent.com/smg-real-estate/ds-toolkit/main/sagemaker/lifecycle/autostop.py \
  -O ${EC2_HOME}/autostop.py

echo "Starting the SageMaker autostop script in cron"
(crontab -l 2>/dev/null; echo "*/5 * * * * ${CONDA_ENV_PATH}/bin/python ${EC2_HOME}/autostop.py --time ${IDLE_TIME} --ignore-connections") | crontab -

crontab -l
