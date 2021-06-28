# Archiving videos

Ragtag Archive is mostly compatible with output from [yt-dlp](https://github.com/yt-dlp/yt-dlp), with a few modifications.

For example, following command will get most of the work done:

```
yt-dlp \
  --write-info-json \
  --get-comments \
  --keep-video \
  --remux-video mkv \
  --write-thumbnail \
  --sub-langs all \
  --sub-format "srv3/json" \
  --write-subs \
  -o "%(id)s/%(id)s.%(ext)s" \
  https://youtu.be/S8dmq5YIUoc
```

For live chat, rename `.live_chat.json` to `.chat.json`. Then, generate a document for Elasticsearch, following the format in the `examples/` folder. Most of the fields are taken from the `.info.json` file, except for a few.

- `archived_timestamp` is the date and time when the video was downloaded from YouTube.
- `timestamps` is an optional field, you can get the exact upload/stream timestamps from the YouTube API.
- `drive_base` is for when you want to put the files in different folders. e.g. if `drive_base` is `test`, and the environment variable `DRIVE_BASE_URL` is `http://localhost:8080`, then the archive will access files from e.g. `http://localhost:8080/gd:test/S8dmq5YIUoc/S8dmq5YIUoc.chat.json`.

If you don't care about multiple folders, just set `drive_base` to any arbitrary value.

Once the files are in place in your webserver, insert the document into Elasticsearch just like in the example in `README.md`.
