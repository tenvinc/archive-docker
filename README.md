# archive-docker

Dockerfile to quickly deploy your own instance of [Ragtag Archive](https://archive.ragtag.moe). This configuration launches the [frontend](https://gitlab.com/aonahara/archive-browser), an Elasticsearch database, and an nginx webserver to serve files.

We currently don't provide tools to archive videos, but Ragtag Archive should be compatible with the output from [yt-dlp](https://github.com/yt-dlp/yt-dlp). For more info, see `ARCHIVING.md`.

## Usage

Start it up

```bash
docker-compose up -d
```

Open [http://localhost:3000](http://localhost:3000) in your browser. It should show an error page. This is because the database has not been initialized yet.

Run the following to initialize the indices:

```bash
docker-compose exec archive-browser node /app/doc/create_indices.js http://elastic:9200
```

If you get an error, e.g. `TypeError: Cannot read property 'data' of undefined`, it means Elasticsearch is still initializing. Wait a few minutes and try to run the command again.

Refresh your browser. It should show the standard interface with no videos.

Let's insert some sample data.

```bash
# Download and extract sample video (~78.4M)
docker-compose exec nginx curl -o /usr/share/nginx/html/sample.tar.gz https://storage.googleapis.com/aonahara-misc/ragtag-archive/sample.tar.gz
docker-compose exec nginx ln -s /usr/share/nginx/html /usr/share/nginx/html/gd:0
docker-compose exec nginx tar -xzvf /usr/share/nginx/html/sample.tar.gz -C /usr/share/nginx/html/gd:0/

# Insert video info into database
curl -XPUT -H 'Content-Type: application/json' -d '@examples/S8dmq5YIUoc.db.json' http://localhost:9200/youtube-archive/_doc/S8dmq5YIUoc
```

Refresh your browser. You should now see one video. Note that right now, the `DRIVE_BASE_URL` variable is set to `localhost`. This means the frontend will only work on your computer. On a real deployment, the URL should be set to somewhere accessible from the public internet.

You will also notice that the Download button leads to a 404. This is because the Download button will send users to an `.mkv` file, but the `sample.tar.gz` we downloaded in the previous step does not include an `.mkv` to save space.

## Configuration

Most of the options should be configurable as environment variables in the `docker-compose.yml` file. For more information about all the available options on the `archive-browser` module, refer to the [archive-browser repository](https://gitlab.com/aonahara/archive-browser)
