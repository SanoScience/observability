#!/usr/bin/env bash
COLLECTOR_ENDPOINT=http://195.150.228.106:4318

set -eu

pip3 install --upgrade pip --user
pip3 install --upgrade setuptools --user
pip3 install opentelemetry-exporter-otlp-proto-grpc --user
pip3 install psutil --user

rm -f scrap-metrics.py
wget https://gitlab.com/lwronski/observability/-/raw/main/scrap-metrics.py
python3 -u scrap-metrics.py $COLLECTOR_ENDPOINT &>scrapping_logs.txt
