import argparse
import os
import random
import shutil
import time

import pandas as pd
from tqdm import tqdm

import config as conf
import helper
from TikTokApi.tiktok import TikTokApi
from objs import video_obj, combination_obj

api = TikTokApi.get_instance(use_test_endpoints=True)
# api = TikTokApi.get_instance(custom_verifyFp=verify_FP,generate_static_did=True)

def get_video_info(list_video_objects, tag):
    most_view_count = 0
    over_min_view_download = 0

    video_info_df = helper.load_description_data()

    new_rows = []
    existed_rows = []
    for item in tqdm(list_video_objects, desc=f"Getting info for #{tag}: ", position=0, leave=True):
        if (item.get('author') is None) or (item.get('video') is None):
            continue

        video_info = video_obj(item)
        video_info.local_download_path = f"{conf.base_dir}/downloads/{video_info.id}.mp4"

        if video_info.id in video_info_df.index:
            existed_rows.append(video_info.create_datapoint())
        else:
            new_rows.append(video_info.create_datapoint())

        if video_info.views > most_view_count:
            most_view_count = video_info.views

        over_min_view_download += 1

    if len(new_rows) > 0:
        video_info_df = video_info_df.append(pd.DataFrame(new_rows).set_index('id'))

    if len(existed_rows) > 0:
        video_info_df.update(pd.DataFrame(existed_rows).set_index('id'))

    helper.save_description_data(video_info_df)

def download_videos(list_video_objects, tag):
    over_min_view_download = 0
    most_view_count = 0
    for item in tqdm(list_video_objects, desc=f"Downloading videos for #{tag}: ", position=0, leave=True):
        download_sub_dir = f"{conf.base_dir}/downloads"
        if not os.path.exists(download_sub_dir):
            os.mkdir(download_sub_dir)

        if item.get('author') is None or item.get('video') is None:
            continue

        video_info = video_obj(item)
        video_info.local_download_path = f"{download_sub_dir}/{video_info.id}.mp4"
        # if video_info.views >= 100:
        if video_info.views >= conf.min_views_for_download:
            download_success = video_info.download()

            if not download_success:
                if os.path.exists(conf.download_failed_path):
                    video_download_failed_df = pd.read_csv(conf.download_failed_path, sep=";", header=None,
                                                           encoding='utf-8', engine='python')
                else:
                    video_download_failed_df = pd.DataFrame()

                video_download_failed_df = video_download_failed_df.append([video_info.make_line_for_save()])
                video_download_failed_df.to_csv(conf.download_failed_path, sep=";", header=None, index=None,
                                                encoding='utf-8')
            over_min_view_download += 1

        if video_info.views > most_view_count:
            most_view_count = video_info.views
    print(
        f"Found {over_min_view_download} video over {conf.min_views_for_download}M views for Hashtag #{tag}\nMost view count is {most_view_count}")

# def download_video_from_url(url, save_path):
#     download_success = True
#     try:
#         # """
#         donwloader_web_id = ''.join(random.choice(string.digits) for _ in range(19))
#         downloader = TikTokDownloader(url, donwloader_web_id)
#         downloader.download(save_path)
#         """
#         # Below is if the method used if you have the full tiktok object
#         tiktokData = api.get_Video_By_TikTok(self.item , custom_did=random_did)
#
#         with open(self.local_download_path, "wb") as out:
#             out.write(tiktokData)
#         """
#     except Exception as e:
#         print(f"Can't download {url} => {e}")
#         download_success = False
#
#     return download_success


# MODE 1 -------------------------------------------------------------
def get_trending(ntop=400):
    print(f"Getting {ntop} trending video infomations. Please wait...")
    verify_FP_trend, random_did_trend = helper.create_random_verify_FP_random_did()
    trending = api.trending(count=ntop, custom_verifyFp=verify_FP_trend, custom_did=random_did_trend)
    print(f"===== Found {len(trending)} trending posts")
    get_video_info(trending, 'trending')


# MODE 2 -------------------------------------------------------------
def discover_hashtags(count_per_hashtag=2000, use_specifc_hashtags=False):
    if use_specifc_hashtags:
        print(f"Loading hashtags from file specific_tags.txt")
        hashtags = helper.load_tags_from_file()
    else:
        print(f"Analysting hashtags from database")
        hashtags = helper.load_tags()

    for tag in hashtags:
        try:
            videos = api.byHashtag(tag, count=count_per_hashtag)
            print(f"===== Found {len(videos)} #{tag} posts")
            get_video_info(videos, tag)
        except Exception as e:
            print(f"Error on hashtag {tag}: {e}")
        time.sleep(5)


# MODE 3 -------------------------------------------------------------
def restore_conbine_videos(comb_ids_for_restore):
    if len(comb_ids_for_restore) == 0:
        if os.path.exists(f"{conf.base_dir}/comb_ids_for_restore.txt"):
            with open(f"{conf.base_dir}/comb_ids_for_restore.txt", 'r', encoding='utf-8') as restore_f:
                comb_ids = restore_f.readlines()
                comb_ids = [id.replace('\n', '') for id in comb_ids]
                restore_f.close()

        if len(comb_ids) == 0:
            print(f"Not found any combination ids for restore.")
            return
    else:
        comb_ids = comb_ids_for_restore.copy()

    output_dir = f"{conf.base_dir}/combinations"
    videos_info = helper.load_description_data()

    for comb_id in tqdm(comb_ids, desc=f"Restoring combinations: ", position=0, leave=True):
        comb_path = f"{output_dir}/{comb_id}"

        if not os.path.exists(comb_path):
            print(f"{comb_path} not found")
            continue

        report_path = f"{comb_path}/report_{comb_id}.csv"

        try:
            report_data = pd.read_csv(report_path, sep=";", encoding='utf-8')
            # report_data = report_data.loc[report_data['is_edited'] == 0,:]
            report_data = report_data[report_data['claimed'] < 1]
        except Exception as e:
            print(f"Restore {comb_id} error: {e}")
            continue

        restoring_combination_df = pd.DataFrame(columns=list(videos_info.columns))
        for video_id in list(report_data['video_id']):
            restoring_combination_df = restoring_combination_df.append(videos_info.loc[video_id])

        comb = combination_obj(restoring_combination_df, all_comb_dir=output_dir, id=comb_id, restore=True)
        comb.create_description()
        comb.concatenate_media()

        print(f"Finish restoring combination {comb_id}")


# MODE 4 -------------------------------------------------------------
def conbine_videos(min_duration=900, no_claimed=True, min_views=100, by_author = False):
    # videos_info = pd.read_csv(video_description_path, sep=";", header=None, encoding='utf-8', engine='python')

    # videos_info = load_description_data()

    videos_info, labels = helper.cluster_videos()

    # original_music_condition = videos_info[5].str.lower().str.contains("original")
    if no_claimed:
        no_claim_condition = (videos_info['claimed'] < 1)
    else:
        no_claim_condition = (videos_info['claimed'] <= 1)

    has_never_uploaded_condition = (videos_info['uploaded'] == 0)
    # existed_path_condition = videos_info['local_download_path'].apply(lambda x: os.path.isfile(x))

    over_min_condition = (videos_info['views'] >= min_views)
    videos_info = videos_info[
                has_never_uploaded_condition &
                no_claim_condition &
                over_min_condition]

    conditional_video_infos = [videos_info[videos_info['label'] == label] for label in labels]

    for comb_df in conditional_video_infos:
        combination_df = pd.DataFrame(columns=comb_df.columns)

        while len(comb_df) > 0:
            if sum(comb_df['duration']) <= min_duration:
                comb = combination_obj(comb_df, conf.combination_dir)
                comb.create_description()
                # comb.concatenate_media()
                comb_df.drop(comb_df.index, inplace=True)
                print(f"Break {conf.combination_dir}")
                break
            else:
                rand_id = random.randint(0, len(comb_df) - 1)
                rand_row = comb_df.iloc[rand_id, :]
                combination_df = combination_df.append(rand_row)
                comb_df.drop(comb_df.index[rand_id], inplace=True)

            if sum(combination_df['duration']) >= min_duration:
                # combination_df.sort_values(by=[2])
                comb = combination_obj(combination_df, conf.combination_dir)
                comb.create_description()
                # comb.concatenate_media()
                combination_df = pd.DataFrame(columns=comb_df.columns)


# MODE 5 -------------------------------------------------------------
def update_info(report_only = True):
    report_dir = f'{conf.base_dir}/reports'

    # backup old video_infos file
    if not os.path.exists(f"{conf.base_dir}/history"):
        os.mkdir(f"{conf.base_dir}/history")
    shutil.copyfile(conf.video_description_path,
                    f"{conf.base_dir}/history/video_descriptions_{time.strftime('%d_%m_%Y_%H_%M_%S')}.csv")

    video_description_data = helper.load_description_data()

    if not report_only:
        for url in tqdm(list(video_description_data['post_url']), desc=f"Updating existing video data info: ", position=0,
                        leave=True):
            try:
                verify_FP_, random_did_ = helper.create_random_verify_FP_random_did()
                video_item = api.getTikTokByUrl(url, custom_verifyFp=verify_FP_, custom_did=random_did_)
                if video_item['statusCode'] != 0:
                    continue
            except Exception as e:
                print(e)
                time.sleep(5)
                continue

            video = video_obj(video_item['itemInfo']['itemStruct'])

            try:
                columns_to_update = list(conf.description_datapoint.keys())[1:14]
                values_to_update = list(video.create_datapoint().values())[1:14]
                video_description_data.loc[video.id, columns_to_update] = values_to_update
                video_description_data.loc[video.id, 'last_update'] = time.strftime(conf.time_str_format)
            except Exception as e:
                print(e)

            # if video.id not in [v['id'] for v in existing_videos]:
            #     existing_videos.append(video.create_datapoint())

            time.sleep(0.1)

    # update date from reports
    report_data = pd.DataFrame()
    for report_path in os.listdir(report_dir):
        report_data = report_data.append(
            pd.read_csv(f"{report_dir}/{report_path}", sep=";", encoding='utf-8', engine='python'))
    report_data = report_data.reset_index().drop("index", axis=1)

    for row in report_data.values:
        video_description_data.loc[row[0], ['claimed', 'last_update']] = [row[2],time.strftime(conf.time_str_format)]
        video_description_data.loc[row[0], 'uploaded'] += 1

    video_description_data = video_description_data[video_description_data['tk_id'].notnull()]
    helper.save_description_data(video_description_data)
    print("Description data has been updated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-md', '--mode', type=int, help='running mode', default=-1)
    parser.add_argument('-ntop', '--ntoptrending', type=int, help='[mode_1] Top n videos trending', default=200000)
    parser.add_argument('-nbytag', '--nbytags', type=int, help='[mode_2] Get n video each hashtag', default=2000)
    parser.add_argument('-spec', '--specifchashtags', help='[mode_2] Use specific hashtags from file specific_tags.txt',
                        action="store_true")
    parser.add_argument('-info', '--getinfoonly', help='[mode_2] Get video infos only without downloading',
                        action="store_true")
    parser.add_argument('-ids', '--listids', type=str, help='[mode_3] List comb_ids for restore with sep is "," ',
                        default='')
    parser.add_argument('-min_v', '--minviews', type=int,
                        help='[mode_4] Min views in million for each video in combination', default=50)
    parser.add_argument('-min_d', '--minduration', type=int,
                        help='[mode_4] Min duration in seconds for each combination', default=900)
    parser.add_argument('-nocla', '--noclaimed', help='[mode_4] Min duration in seconds for each combination',
                        action="store_true")
    parser.add_argument('-rp', '--reportonly', help='[mode_5] Only update data from report, else update all records from Tiktok',
                        action="store_true")
    args = parser.parse_args()

    if args.mode == 0:
        md_info = f"""
            -md 1 ==> Get trending videos \n
            -md 2 ==> Get videos by Top20 common hashtags from db OR specific ones from file {conf.base_dir}/specific_tags.txt \n
            -md 3 ==> Restore and continue creating combinations from file {conf.base_dir}/comb_ids_for_restore.txt \n
            -md 4 ==> Combine videos \n
            -md 5 ==> Update video from combined videos

            parser.add_argument('-md', '--mode', type=int, help='running mode', default=-1)
            parser.add_argument('-ntop', '--ntoptrending', type=int, help='[mode_1] Top n videos trending', default=200000)
            parser.add_argument('-nbytag', '--nbytags', type=int, help='[mode_2] Get n video each hashtag', default=2000)
            parser.add_argument('-spec', '--specifchashtags', help='[mode_2] Use specific hashtags from file specific_tags.txt', action="store_true")
            parser.add_argument('-info', '--getinfoonly', help='[mode_2] Get video infos only without downloading', action="store_true")
            parser.add_argument('-ids', '--listids', type=str, help='[mode_3] List comb_ids for restore with sep is "," ', default='')
            parser.add_argument('-min_v', '--minviews', type=int, help='[mode_4] Min views in million for each video in combination', default=50)
            parser.add_argument('-min_d', '--minduration', type=int, help='[mode_4] Min duration in seconds for each combination', default=900)
            parser.add_argument('-nocla', '--noclaimed', help='[mode_4] Min duration in seconds for each combination', action="store_true")
            parser.add_argument('-rp', '--reportonly', help='[mode_5] Only update data from report, else update all records from Tiktok', action="store_true")
            """
        print(md_info)
    elif args.mode == 1:
        get_trending(args.ntoptrending)
    elif args.mode == 2:
        discover_hashtags(count_per_hashtag=args.nbytags, use_specifc_hashtags=args.specifchashtags)
    elif args.mode == 3:
        if args.listids == '':
            comb_ids = []
        else:
            comb_ids = args.listids.split(",")
        restore_conbine_videos(comb_ids)
    elif args.mode == 4:
        conbine_videos(args.minduration, no_claimed=args.noclaimed, min_views=args.minviews)
    elif args.mode == 5:
        update_info(args.reportonly)
    else:
        print("Please choose mode. run -h for more detail")
