#!/bin/bash

DIR_PATH="$SCRATCH/mee_monitoring"
ENV_PATH="$DIR_PATH/env"
COLLECTOR_ENDPOINT=http://81.210.121.140:4318
ENV_NAME="monitoring_env"

function is_package_installed {
    pip show "$1" >/dev/null 2>/dev/null
}


function get_conda_env_name() {
    local env_prefix_path=$1
    conda env list | awk -v prefix="$env_prefix_path" '$0 ~ prefix {print $1}'
}

function setup_conda_and_install_pacakges(){

    mkdir -p $SCRATCH/.conda
    conda config --add pkgs_dirs $SCRATCH/.conda

    echo "creating env"

    # conda config --append envs_dirs $ENV_PATH
    # # conda create --prefix="$ENV_PATH/$ENV_NAME" --file $1
    # conda env create --prefix $ENV_PATH --file $1

    # conda config --set auto_activate_base false

    echo "11"
    FILE_PATH="$(pwd)/$1"
    cd $DIR_PATH
    conda clean
    conda env create --name $ENV_NAME --file $FILE_PATH
    cd -
    echo "12"
    conda config --set auto_activate_base false
    echo "13"
    # source activate $ENV_PATH

    conda info --envs

    conda install -p $ENV_PATH  pip

    echo 1
    conda install -p $ENV_PATH  setuptools

    echo 2
    conda config --add channels conda-forge
    conda config --set channel_priority strict

    conda install -p $ENV_PATH opentelemetry-exporter-otlp-proto-grpc

    echo 3
    conda install -p $ENV_PATH psutil

    echo 4
    # conda install -p $ENV_PATH argparse

    # echo 5
    # if is_package_installed opentelemetry-exporter-otlp-proto-grpc; then
    #     echo "opentelemetry-exporter-otlp-proto-grpc is installed"
    # else
    #     pip3 install opentelemetry-exporter-otlp-proto-grpc --user
    # fi

    # if is_package_installed psutil; then
    #     echo "psutil is installed"
    # else
    #     pip3 install psutil --user
    # fi

    # if is_package_installed argparse; then
    #     echo "argparse is installed"
    # else
    #     pip3 install argparse --user
    # fi
}

function setup_env() {
    LOCK_FILE=$DIR_PATH/setup_conda.lock
    echo  $DIR_PATH

    if [ ! -d $DIR_PATH ]; then
        mkdir -p $DIR_PATH
    fi

    module load miniconda3

    exec 200>$LOCK_FILE
    flock -x 200

    if [ ! -d $ENV_PATH ]; then
        echo "setup packages start"
        setup_conda_and_install_pacakges $1
    fi
    # else
    #     source activate $ENV_PATH
    # fi

    flock -u 200
}


function run_monitoring() {
    USER_ARGS=$1
    echo "Environment name: $ENV_NAME"
    rm -f scrap-metrics.py
    wget -q https://raw.githubusercontent.com/SanoScience/observability/develop/scrap-metrics.py
    conda run -n $ENV_PATH python3 -u scrap-metrics.py --collector $COLLECTOR_ENDPOINT $USER_ARGS &>scrapping_logs.txt
}

function param_or_empty() {
    [[ $# -gt 0 ]] && echo $1 || echo 'EMPTY';
}
