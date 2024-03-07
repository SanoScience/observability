#!/bin/bash

DIR_PATH="$SCRATCH/mee_monitoring"
ENV_PATH=$DIR_PATH/env
COLLECTOR_ENDPOINT=http://81.210.121.140:4318

function is_package_installed {
    pip show "$1" >/dev/null 2>/dev/null
}


function setup_conda_and_install_pacakges(){
    module load miniconda3

    if [ ! -d $ENV_PATH ]; then
        mkdir -p $SCRATCH/.conda
        conda config --add pkgs_dirs $SCRATCH/.conda
        conda env create --prefix $ENV_PATH --file $1
    fi

    conda config --set auto_activate_base false
    source activate $ENV_PATH

    pip3 install --upgrade pip --user
    pip3 install --upgrade setuptools --user


    if is_package_installed opentelemetry-exporter-otlp-proto-grpc; then
        echo "opentelemetry-exporter-otlp-proto-grpc is installed"
    else
        echo  "installing opentelemetry-exporter-otlp-proto-grpc"
        pip3 install opentelemetry-exporter-otlp-proto-grpc --user
    fi

    if is_package_installed psutilss; then
        echo "psutil is installed"
    else
        echo  "installing psutil"
        # pip3 install psutil --user
    fi

    if is_package_installed argparse; then
        echo "argparse is installed"
    else
        echo  "installing argparse"
        pip3 install argparse --user
    fi
}

function setup_env() {
    LOCK_FILE=$DIR_PATH/setup_conda.lock
    echo  $DIR_PATH
    if [ ! -d $DIR_PATH ]; then
        echo "zrobione"
        mkdir -p $DIR_PATH
    fi

    if [ ! -f "$LOCK_FILE" ]; then
        
        touch $LOCK_FILE
        chmod 774 $LOCK_FILE
        exec 200>$LOCK_FILE
        flock -x 200

        setup_conda_and_install_pacakges

        flock -u 200
    else
        exec 200>$LOCK_FILE
        flock -x 200

        setup_conda_and_install_pacakges

        flock -u 200
    fi
}


function run_monitoring() {
    USER_ARGS=$1
    rm -f scrap-metrics.py
    wget -q https://raw.githubusercontent.com/SanoScience/observability/develop/scrap-metrics.py
    python3 -u scrap-metrics.py --collector $COLLECTOR_ENDPOINT $USER_ARGS &>scrapping_logs.txt
}

function param_or_empty() {
    [[ $# -gt 0 ]] && echo $1 || echo 'EMPTY';
}
