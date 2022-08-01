from django.apps import AppConfig
import platform
import random
import string
import os
import nest_asyncio
nest_asyncio.apply()

class Tk100MConfig(AppConfig):
    name = 'tk100m'

    time_str_format = '%d-%m-%YT%H:%M:%S'

    tt_webid = ''.join(random.choice(string.digits) for _ in range(19))

    all_letters = f"{string.ascii_letters}{string.digits}"

    is_windows = (True if platform.system().lower() == 'windows' else False)

    storage_dir = f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}/tibo/storage"
    # if is_windows:
    #     storage_dir = "./downloaded"
    # else:
    #     storage_dir = "/content/drive/MyDrive/tk100mil/storage"
    source_dir = f"{storage_dir}/source"
    combination_dir = f"{storage_dir}/combinations"
    video_description_path = f"{storage_dir}/video_descriptions.csv"
    specific_tags_path = f"{storage_dir}/specific_tags.txt"
    download_failed_path = f"{storage_dir}/download_failed.csv"

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
        'cover_url': '#',
        'local_download_path': '#',
        'local_edit_path': '#',
        'claimed': 0,
        'uploaded': 0,
        'last_update': '#',
        'is_downloaded': 0
    }

    mongodb_connection_string = {
        'local':'mongodb://localhost:27017',
        'atlas':"mongodb://thuc:thuc1010@tkcluster.kz7gb.mongodb.net"
    }

