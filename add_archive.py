import os
import re
import json
import traceback
import requests
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

channels_processed = []

def parse_youtube_json(youtube_json):
    """
    Parses youtube .info.json file into suitable db file (.db.json) for archive-browser
    """

    def epoch_to_archive_browser_timestamp(epoch, decimal_seconds=False):
        dt = datetime.fromtimestamp(epoch, timezone.utc)
        if decimal_seconds:
            return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def yt_date_to_archive_browser_date(date_str):
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        return date_obj.strftime("%Y-%m-%d")

    db_json_dict = {
        "video_id": youtube_json["id"],
        "channel_name": youtube_json["channel"],
        "channel_id": youtube_json["channel_id"],
        "upload_date": yt_date_to_archive_browser_date(youtube_json["upload_date"]),
        "title": youtube_json["title"],
        "description": youtube_json["description"],
        "duration": youtube_json["duration"],
        "width": youtube_json["width"],
        "height": youtube_json["height"],
        "fps": youtube_json["fps"],
        "format_id": youtube_json["format_id"],
        "view_count": youtube_json["view_count"],
        "like_count": youtube_json["like_count"],
        "dislike_count": 0,
        "archived_timestamp": epoch_to_archive_browser_timestamp(
            youtube_json["epoch"], decimal_seconds=True
        ),
        "timestamps": {
            "actualStartTime": epoch_to_archive_browser_timestamp(
                youtube_json["release_timestamp"]
            ),
            "publishedAt": epoch_to_archive_browser_timestamp(
                youtube_json["release_timestamp"]
            ),
            "scheduledStartTime": epoch_to_archive_browser_timestamp(
                youtube_json["timestamp"]
            ),
            "actualEndTime": epoch_to_archive_browser_timestamp(
                youtube_json["release_timestamp"] + youtube_json["duration"]
            ),
        },
    }

    return db_json_dict


def add_file_list(db_json_dict, files):
    accepted_exts = ["mkv", "mp4", "webm", "m4a", "chat.json", "webp", "info.json"]
    pattern = r"\.({})$".format("|".join(map(re.escape, accepted_exts)))
    regex = re.compile(pattern)
    matching_files = [filename for filename in files if regex.search(filename)]

    db_json_file_list = []
    for filepath in matching_files:
        file_metadata = {
            "name": os.path.basename(filepath),
            "size": os.path.getsize(filepath),
        }
        db_json_file_list.append(file_metadata)
    db_json_dict["files"] = db_json_file_list
    return db_json_dict


def add_drive_base(db_json_dict):
    global drive_base
    db_json_dict["drive_base"] = drive_base
    return db_json_dict


def add_to_archive_browser(name, db_json_dict):
    import requests

    db_uri = f'http://localhost:9200/youtube-archive/_doc/{name}'
    data = json.dumps(db_json_dict, indent=None).encode()
    headers = {
        'Content-Type': 'application/json',
    }
    request_timeout = 5
    response = requests.put(db_uri, headers=headers, data=data, timeout=request_timeout)
    
    print(f"Update request sent to {db_uri}")
    if response.status_code == 200 or response.status_code == 201:
        print("Request success")
    else:
        print(f"Request failed with status code: {response.status_code}")

def add_channel_profile(profile_pic_path):
    script_dir = script_dir = Path(__file__).parent.resolve()
    compose_file_path = os.path.join(script_dir, 'docker-compose.yml')
    path_obj = Path(profile_pic_path)
    nginx_pic_path = Path(os.path.join(os.sep, 'usr', 'share', 'nginx', 'html', path_obj.parent.name, path_obj.name))
    
    mkdir_command = f"docker compose -f {compose_file_path} exec nginx mkdir -p {nginx_pic_path.parent.resolve()}"
    result = subprocess.run(mkdir_command.split(' '), capture_output=True, check=True)
    cp_command = f'docker compose -f {compose_file_path} cp {profile_pic_path} nginx:{nginx_pic_path.resolve()}'
    result = subprocess.run(cp_command.split(' '), capture_output=True, check=True)
    print(f"Added channel metadata for {path_obj.parent.name}")

def main():
    global archive_dir
    for root, _, files in os.walk(archive_dir):
        youtube_json_files = [file for file in files if ".info.json" in file]

        if len(youtube_json_files) == 0:
            continue

        dir_path = root
        folder_name = os.path.basename(dir_path)

        # by default take the first matching file to *.info.json
        youtube_json = {}
        try:
            with open(os.path.join(dir_path, youtube_json_files[0])) as fp:
                youtube_json = json.load(fp)
                db_json_dict = parse_youtube_json(youtube_json)
                db_json_dict = add_file_list(
                    db_json_dict, [os.path.join(root, f) for f in files]
                )
                db_json_dict = add_drive_base(db_json_dict)

                global gen_debug_files_flag
                if gen_debug_files_flag:
                    directory = "debug"
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    with open(os.path.join(directory, f"test-{folder_name}.db.json"), "w") as db_json_file:
                        json.dump(db_json_dict, db_json_file, ensure_ascii=False, indent=2)

                if db_json_dict['channel_id'] not in channels_processed:
                    channels_processed.append(db_json_dict['channel_id'])
                add_to_archive_browser(folder_name, db_json_dict)

        except KeyError as ke:
            print(traceback.format_exc())
            print(f"Unable to parse youtube json file. Skipping {folder_name}...")
            continue
    
    global skip_channel_upload
    if not skip_channel_upload:
        for channel in channels_processed:
            image_path = os.path.join(archive_dir, channel, 'profile.jpg')
            if not os.path.exists(image_path):
                continue
            add_channel_profile(image_path)

if __name__ == "__main__":
    global archive_dir, drive_base, gen_debug_files_flag, skip_channel_upload
    parser = argparse.ArgumentParser() 
    parser.add_argument('--drive_base', type=str, default='archive', help="Base drive name to add all files under in archive browser")
    parser.add_argument('--archive_dir', type=str, required=True, help='Archive directory to process')
    parser.add_argument('--gen_debug_files', type=bool, default=False, help='Flag whether to generate debug files')
    parser.add_argument('--skip_channel_upload', type=bool, default=False, help='Flag whether to skip uploading channel metadata')
    
    args = parser.parse_args()
    archive_dir = args.archive_dir
    drive_base = args.drive_base
    gen_debug_files_flag = args.gen_debug_files
    skip_channel_upload = args.skip_channel_upload
    main()


