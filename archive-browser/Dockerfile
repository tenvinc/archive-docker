FROM node:14 AS builder

# Clone repository
RUN apt install -y git
RUN git clone https://gitlab.com/aonahara/archive-browser.git /app
WORKDIR /app
RUN yarn
RUN yarn build

FROM node:14
COPY --from=builder /app /app
WORKDIR /app
CMD yarn start
