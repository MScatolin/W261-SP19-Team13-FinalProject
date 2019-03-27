#! /usr/bin/env bash

BUCKET="w261_final-project_team13"
CLUSTER="cluster"
PROJECT="infinite-cache-235422"
JUPYTER_PORT="8123"
PORT="10000"
ZONE="us-central1-a"



# CREATE SOCKS PROXY
gcloud compute ssh ${CLUSTER}-m \
    --project=${PROJECT} \
    --zone=${ZONE}  \
    --ssh-flag="-D" \
    --ssh-flag=${PORT} \
    --ssh-flag="-N"

# DOCUMENTATION
# https://cloud.google.com/solutions/connecting-securely#socks-proxy-over-ssh
