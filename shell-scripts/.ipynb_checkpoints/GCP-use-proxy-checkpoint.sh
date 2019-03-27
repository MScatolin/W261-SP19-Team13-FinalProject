#! /usr/bin/env bash

BUCKET="hw5_w261_msq"
CLUSTER="mingau"
PROJECT="w261-hw5-msq"
JUPYTER_PORT="8123"
PORT="10000"
ZONE='us-central1-a'


# USE SOCKS PROXY
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --proxy-server="socks5://localhost:${PORT}" \
  --user-data-dir=/tmp/${CLUSTER}-m


# DOCUMENTATION
# https://cloud.google.com/solutions/connecting-securely#socks-proxy-over-ssh
