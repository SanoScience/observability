#!/usr/bin/env bash
set -eu

pip3 install --upgrade pip --user
pip3 install --upgrade setuptools --user
pip3 install opentelemetry-exporter-otlp-proto-grpc --user
pip3 install psutil --user
