#! /usr/bin/env bash

BUCKET="w261_final-project_team13"
CLUSTER="cluster"
PROJECT="infinite-cache-235422"
JUPYTER_PORT="8123"
PORT="10000"
ZONE="us-central1-a"


# USE SOCKS PROXY
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --proxy-server="socks5://localhost:${PORT}" \
  --user-data-dir=/tmp/${CLUSTER}-m


# DOCUMENTATION
# https://cloud.google.com/solutions/connecting-securely#socks-proxy-over-ssh
