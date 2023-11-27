#!/bin/bash

ENV_PATH=$PLG_GROUPS_STORAGE/plggisw/Monitoring/env
COLLECTOR_ENDPOINT=http://195.150.228.106:4318

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

function install_packages() {
    pip3 install --upgrade pip --user
    pip3 install --upgrade setuptools --user
    pip3 install opentelemetry-exporter-otlp-proto-grpc --user
    pip3 install psutil --user
    pip3 install argparse --user
}

function run_monitoring() {
    USER_ARGS=$1
    rm -f scrap-metrics.py
    wget -q https://gitlab.com/lwronski/observability/-/raw/main/scrap-metrics.py
    python3 -u scrap-metrics.py --collector $COLLECTOR_ENDPOINT $USER_ARGS &>scrapping_logs.txt
}
