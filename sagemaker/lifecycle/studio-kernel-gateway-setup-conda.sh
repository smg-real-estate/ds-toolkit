#!/bin/bash

set -eux
ln -sf /root /home/sagemaker-user

PRE_COMMIT_HOME=${HOME}/.cache/pre-commit
KERNELS_DIR=${HOME}/.kernels

if [ -f $HOME/ds-toolkit/sagemaker/lifecycle/bashrc-studio.sh ]; then
  cat $HOME/ds-toolkit/sagemaker/lifecycle/bashrc-studio.sh > ~/.bash_profile
  chmod 666 ~/.bash_profile
  source ~/.bash_profile

    for env in $KERNELS_DIR/*; do
        basename=$(basename $env)
        python_version=$(micromamba run -p $env python -V)
        micromamba run -p $env \
          python -m ipykernel install --user --name "$basename" \
          --display-name "${python_version}"
    done
fi