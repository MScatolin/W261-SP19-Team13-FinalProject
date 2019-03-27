#! /usr/bin/env bash

BUCKET="hw5_w261_msq"
CLUSTER="mingau"
PROJECT="w261-hw5-msq"
JUPYTER_PORT="8123"
PORT="10000"
ZONE='us-central1-a'


# CREATE SOCKS PROXY
gcloud compute ssh ${CLUSTER}-m \
    --project=${PROJECT} \
    --zone=${ZONE}  \
    --ssh-flag="-D" \
    --ssh-flag=${PORT} \
    --ssh-flag="-N"

# DOCUMENTATION
# https://cloud.google.com/solutions/connecting-securely#socks-proxy-over-ssh
