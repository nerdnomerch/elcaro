# elcaro oracle

## clone repository

```bash
➜ git clone git@github.com:aarlt/elcaro.git
➜ cd elcaro
```

## build dockered node

```bash
➜  cd node
➜  docker build .
Step 1/11 : FROM python:alpine AS builder
 ---> bcf3965d8456
Step 2/11 : RUN apk add build-base libffi-dev
...
Successfully built fd8a7e1f2cc1
```
Here `fd8a7e1f2cc1` is the `${IMAGE_ID}`.

## start dockered node

```bash
➜ docker run --rm -it ${IMAGE_ID}
```
