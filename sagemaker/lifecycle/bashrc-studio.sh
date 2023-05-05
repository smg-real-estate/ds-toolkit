# >>> mamba initialize >>>
# !! Contents within this block are managed by 'mamba init' !!
export MAMBA_ROOT_PREFIX="${HOME}/.micromamba";
export MAMBA_EXE="${MAMBA_ROOT_PREFIX}/bin/micromamba";
export TOOLS=$HOME/.tools

export PATH=$TOOLS/bin:$PATH

__mamba_setup="$($MAMBA_EXE shell hook --shell bash --prefix $MAMBA_ROOT_PREFIX 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    if [ -f $MAMBA_ROOT_PREFIX/etc/profile.d/micromamba.sh ]; then
        . $MAMBA_ROOT_PREFIX/etc/profile.d/micromamba.sh
    else
        export  PATH="$MAMBA_ROOT_PREFIX/bin:$PATH"  # extra space after export prevents interference from conda init
    fi
fi
unset __mamba_setup
# <<< mamba initialize <<<
