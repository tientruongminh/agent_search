FROM node:24-alpine

WORKDIR /workspace/apps/web

COPY package.json package-lock.json* ./

RUN npm install

EXPOSE 3000

