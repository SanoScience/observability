#!/usr/bin/env bash
COLLECTOR_ENDPOINT=http://195.150.228.106:4318
USER_ARGS=$1

set -eu

rm -f scrap-metrics.py
wget https://gitlab.com/lwronski/observability/-/raw/main/scrap-metrics.py
python3 -u scrap-metrics.py --collector $COLLECTOR_ENDPOINT $USER_ARGS &>scrapping_logs.txt
