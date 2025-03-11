#!/bin/sh

if [ ! -f  /data/ipfs/datastore_spec ]; then
    mkdir -p /data/ipfs
    mkdir -p /data/geth
    mkdir -p /data/executor/request
    mkdir -p /data/executor/response
    touch /data/ipfs/ipfs.log /data/geth/geth.log /data/executor/executor.log
    /usr/bin/ipfs init > /dev/null
fi

/usr/bin/ipfs daemon --migrate=true > /data/ipfs/ipfs.log 2>&1 &
IPFS=$!

/usr/bin/geth --datadir /data/geth --ws --wsport 8545 --goerli --syncmode light > /data/geth/geth.log 2>&1 &
GETH=$!

sleep 5

python3 /elcaro/executor.py &
EXECUTOR=$!

python3 /elcaro/main.py $@

kill ${IPFS}
kill ${GETH}
kill ${EXECUTOR}

while [ -e /proc/${IPFS} ]; do sleep 1; done
while [ -e /proc/${GETH} ]; do sleep 1; done
while [ -e /proc/${EXECUTOR} ]; do sleep 1; done
