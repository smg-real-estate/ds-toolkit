#!/bin/bash
set -euxo pipefail
########################## Git setup ###########################################
GIT_USER=$GIT_USER
GIT_EMAIL=$GIT_EMAIL
function git_config() {
  sudo -u ec2-user -E git config --global $1 $2
}
git_config user.email "${GIT_EMAIL}"
git_config user.name "${GIT_USER}"
git_config pull.rebase true
git_config alias.a add
git_config alias.b branch
git_config alias.c commit
git_config alias.cl clone
git_config alias.co checkout
git_config alias.cp cherry-pick
git_config alias.m merge
git_config alias.p push --follow-tags
git_config alias.pu pull
git_config alias.r reset
git_config alias.s status
git_config alias.force-push push --force-with-lease
git_config alias.fp force-push
git_config init.defaultbranch main
################################################################################

##################### script that is run under ec2-user ########################
sudo -n -u ec2-user -i <<'EOF'
set -euxo pipefail
unset SUDO_UID
printenv

HOME=/home/ec2-user

CUSTOM_KERNELS_DIR=$HOME/SageMaker/.kernels
CONFIGS_DIR=$HOME/SageMaker/ds-toolkit/sagemaker/lifecycle

pushd .jupyter
rm -rf jupyter_notebook_config.py jupyter_server_config.py lab nbconfig
ln -sf $CONFIGS_DIR/jupyter_server_config.py
ln -sf $CONFIGS_DIR/jupyter_notebook_config.py
ln -sf $CONFIGS_DIR/lab
ln -sf $CONFIGS_DIR/nbconfig

popd

pushd $CONFIGS_DIR && git pull && popd

echo "source $HOME/SageMaker/ds-toolkit/sagemaker/lifecycle/bashrc" >> $HOME/.bashrc


if [ -f $HOME/.condarc ]; then
  rm $HOME/.condarc
fi
ln -sf $CONFIGS_DIR/.condarc $HOME/.condarc

# skip installing pre-commit
# conda install -n JupyterSystemEnv -c conda-forge pre-commit -y

for env in $CUSTOM_KERNELS_DIR/*; do

  BASENAME=$(basename "$env")
  source activate "$BASENAME"

  python -m ipykernel install --user --name "$BASENAME" \
    --display-name "Python (${BASENAME})"
  conda deactivate
done
# Optionally, uncomment these lines to disable SageMaker-provided Conda functionality.

# echo "c.EnvironmentKernelSpecManager.use_conda_directly = False" >> $HOME/.jupyter/jupyter_notebook_config.py

#
EOF
################################################################################

echo "Restarting the Jupyter server.."
sudo systemctl restart jupyter-server

# OVERVIEW
# This part of the script stops a SageMaker notebook once it's idle for more than 1 hour (default time)
# You can change the idle time for stop using the environment variable below.
# If you want the notebook the stop only if no browsers are open, remove the --ignore-connections flag
#
# Note that this script will fail if either condition is not met
#   1. Ensure the Notebook Instance has internet connectivity to fetch the example config
#   2. Ensure the Notebook Instance execution role permissions to SageMaker:StopNotebookInstance to stop the notebook 
#       and SageMaker:DescribeNotebookInstance to describe the notebook.

PROJECT_URL=$PROJECT_URL
BRANCH=$BRANCH
EC2_HOME=/home/ec2-user
IDLE_TIME=7200
CONDA_ENV_NAME=smg-re-py3.7
CONDA_ENV_PATH=${EC2_HOME}/SageMaker/.kernels/${CONDA_ENV_NAME}
echo "Fetching the autostop script"
wget ${PROJECT_URL}/${BRANCH}/sagemaker/lifecycle/autostop.py \
  -O ${EC2_HOME}/autostop.py

echo "Starting the SageMaker autostop script in cron"
(crontab -l 2>/dev/null; echo "*/5 * * * * ${CONDA_ENV_PATH}/bin/python ${EC2_HOME}/autostop.py --time ${IDLE_TIME} --ignore-connections") | crontab -

crontab -l
