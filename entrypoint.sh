#!/bin/bash
set -e

# Wait for elastic server to be up
until curl -s http://elastic:9200 > /dev/null; 
  do echo 'Waiting for elastic...'
  sleep 5
done

echo 'Elastic server is up!'

res=$(eval curl -X GET "http://elastic:9200/_cat/indices")

echo "Finish curl"

if [[ -z $res ]]; then
  echo "Creating indices now..."
  node /app/doc/create_indices.js http://elastic:9200
else
  echo "Indices already created"
fi

echo "Starting main application..."
exec "$@"

