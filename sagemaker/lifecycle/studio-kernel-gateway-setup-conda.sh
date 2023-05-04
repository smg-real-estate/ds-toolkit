#!/bin/bash

set -eux

PRE_COMMIT_HOME=${HOME}/.cache/pre-commit
KERNELS_DIR=${HOME}/.kernels

pushd $HOME/ds-toolkit && git pull && popd
source $HOME/ds-toolkit/sagemaker/lifecycle/bashrc-studio.sh

micromamba config append channels conda-forge
micromamba config append channels defaults
micromamba config append envs_dirs $HOME/.conda/envs
micromamba config append envs_dirs $KERNELS_DIR

for env in $KERNELS_DIR/*; do
    micromamba run -r $KERNELS_DIR/$env \
      python -m ipykernel install --user --name "$BASENAME" \
      --display-name "Python (${BASENAME})"
done
nohup supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart jupyterlabserver
