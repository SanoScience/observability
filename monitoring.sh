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


    FILE_PATH="$(pwd)/$1"
    cd $DIR_PATH
    conda env create --name $ENV_NAME --file $FILE_PATH
    cd -
    conda config --set auto_activate_base false

    conda info --envs

    conda install -n $ENV_NAME  pip

    conda install -n $ENV_NAME  setuptools

    # conda config --add channels conda-forge
    # conda config --set channel_priority strict

    conda install -c conda-forge -n $ENV_NAME opentelemetry-exporter-otlp-proto-grpc

    conda install -n $ENV_NAME psutil

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

    flock -u 200
}


function run_monitoring() {
    USER_ARGS=$1
    echo "Environment name: $ENV_NAME"
    rm -f scrap-metrics.py
    wget -q https://raw.githubusercontent.com/SanoScience/observability/develop/scrap-metrics.py
    echo "Scrap metrics starts"
    # cat scrap-metrics.py
    touch scrapping_logs.txt
    echo "Test log entry" &>scrapping_logs.txt
    conda activate $ENV_NAME
    conda run -n $ENV_NAME python -u scrap-metrics.py --collector $COLLECTOR_ENDPOINT $USER_ARGS &>scrapping_logs.txt
}

function param_or_empty() {
    [[ $# -gt 0 ]] && echo $1 || echo 'EMPTY';
}
