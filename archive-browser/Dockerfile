ARG NODE_VERSION=22

FROM node:${NODE_VERSION} AS builder

# Clone repository
RUN apt install -y git
RUN git clone https://github.com/ragtag-archive/archive-browser.git /app
WORKDIR /app
RUN yarn
RUN yarn build

FROM node:${NODE_VERSION}
COPY --from=builder /app /app
WORKDIR /app
CMD yarn start
