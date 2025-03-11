FROM python:alpine AS builder

RUN apk add build-base libffi-dev openssl-dev ca-certificates
RUN pip3 install --upgrade pip

ADD src /elcaro
ADD contracts /elcaro/contracts

RUN pip3 install --upgrade pip
RUN pip3 install -r /elcaro/requirements.txt

FROM python:alpine

COPY --from=0 /elcaro /elcaro
COPY init/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 0755 /usr/local/bin/entrypoint.sh

COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages

RUN apk add go-ipfs geth libffi su-exec tini-static

ENV IPFS_PATH /data/ipfs
ENV GETH_PATH /data/geth
ENV EXECUTOR_PATH /data/executor

RUN mkdir -p $IPFS_PATH $GETH_PATH $EXECUTOR_PATH
RUN adduser -D -h $IPFS_PATH -u 1000 -G users elcaro

ENTRYPOINT ["/sbin/tini-static", "--", "/usr/local/bin/entrypoint.sh"]
# ENTRYPOINT ["/sbin/tini-static", "--", "/bin/sh"]
