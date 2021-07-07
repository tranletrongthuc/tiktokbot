import platform
import random
import string
import nest_asyncio

nest_asyncio.apply()

time_str_format = '%d-%m-%YT%H:%M:%S'

tt_webid = ''.join(random.choice(string.digits) for _ in range(19))

all_letters = f"{string.ascii_letters}{string.digits}"

is_windows = (True if platform.system().lower() == 'windows' else False)

if is_windows:
    base_dir = "./downloaded"
else:
    base_dir = "/content/drive/MyDrive/tk100mil/storage"
source_dir = f"{base_dir}/source"
combination_dir = f"{base_dir}/combinations"
video_description_path = f"{base_dir}/video_descriptions.csv"
specific_tags_path = f"{base_dir}/specific_tags.txt"
download_failed_path = f"{base_dir}/download_failed.csv"

min_views_for_download = 50

description_datapoint = {
    'id': '#',
    'author': '#',
    'author_name': '#',
    'tk_id': '#',
    'views': 0,
    'hearts': 0,
    'comments': 0,
    'shares': 0,
    'created_date': '#',
    'tags': '#',
    'duration': 0,
    'music': '#',
    'music_url': '#',
    'post_url': '#',
    'local_download_path': '#',
    'local_edit_path': '#',
    'claimed': 0,
    'uploaded': 0,
    'last_update': '#',
    'is_downloaded': 0
}
