FROM python:alpine AS builder

RUN apk add build-base libffi-dev openssl-dev ca-certificates
RUN pip3 install --upgrade pip

ADD src /elcaro
RUN pip3 install -r /elcaro/requirements.txt

FROM python:alpine

COPY --from=0 /elcaro /elcaro

COPY init/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 0755 /usr/local/bin/entrypoint.sh

COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages

RUN apk add go-ipfs geth libffi su-exec tini-static openssl docker bash

ENV IPFS_PATH /data/ipfs
ENV GETH_PATH /data/geth

RUN mkdir -p $IPFS_PATH && mkdir -p $GETH_PATH && adduser -D -h $IPFS_PATH -u 1000 -G users elcaro
ENTRYPOINT ["/sbin/tini-static", "--", "/usr/local/bin/entrypoint.sh"]
# ENTRYPOINT ["/sbin/tini-static", "--", "/bin/bash"]
