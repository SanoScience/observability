#!/bin/bash

ENV_PATH=$SCRATCH/mee_monitoring/env
COLLECTOR_ENDPOINT=http://195.150.228.106:4318

function setup_conda() {
    module load miniconda3
    LOCK_FILE=$SCRATCH/mee_monitoring/setup_conda.lock

    if [ ! -d $ENV_PATH ]; then
        
        mkdir -p $SCRATCH/.conda
        conda config --add pkgs_dirs $SCRATCH/.conda
        conda env create --prefix $ENV_PATH --file $1
    fi

    if [ ! -f "$LOCK_FILE" ]; then
        
        touch $LOCK_FILE
        chmod 774 $LOCK_FILE
        exec 200>$LOCK_FILE
        flock -x 200

        pip3 install --upgrade pip --user
        pip3 install --upgrade setuptools --user
        pip3 install opentelemetry-exporter-otlp-proto-grpc --user
        pip3 install psutil --user
        pip3 install argparse --user

        flock -u 200
    else
        exec 200>$LOCK_FILE
        flock -x 200

        conda config --set auto_activate_base false
        source activate $ENV_PATH

        flock -u 200
    fi
}

function install_packages() {
    echo 'no install';
    # pip3 install --upgrade pip --user
    # pip3 install --upgrade setuptools --user
    # pip3 install opentelemetry-exporter-otlp-proto-grpc --user
    # pip3 install psutil --user
    # pip3 install argparse --user
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
