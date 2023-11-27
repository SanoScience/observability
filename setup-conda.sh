#!/bin/bash

ENV_PATH=$PLG_GROUPS_STORAGE/plggisw/Monitoring/env

function setup_conda() {
    module load miniconda3

    if [ ! -d $ENV_PATH ]; then
        mkdir -p $SCRATCH/.conda
        conda config --add pkgs_dirs $SCRATCH/.conda
        conda env create --prefix $ENV_PATH --file $1
    fi
    
    conda config --set auto_activate_base false
    source activate $ENV_PATH
}
