#!/bin/bash

NODE_NAME=$1
DELAY=$2
JITTER=$3

usage() {
    echo "Usage:"
    echo "  Set Delay:   ./manage_network.sh [container_name] [delay] [jitter]"
    echo "  Clear Delay: ./manage_network.sh [container_name] clear"
    exit 1
}

if [ -z "$NODE_NAME" ] || [ -z "$DELAY" ]; then
    usage
fi

if [ "$DELAY" == "clear" ]; then
    sudo docker run --rm \
      --network container:$NODE_NAME \
      --cap-add=NET_ADMIN \
      nicolaka/netshoot \
      tc qdisc del dev eth0 root
else
    sudo docker run --rm \
      --network container:$NODE_NAME \
      --cap-add=NET_ADMIN \
      nicolaka/netshoot \
      tc qdisc replace dev eth0 root netem delay $DELAY $JITTER
fi