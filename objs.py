import helper
import datetime
import time
from pathlib import Path
import config as conf
import pandas as pd
import random
import string
import os
import moviepy.editor as mp
from moviepy.video import fx
from tqdm import tqdm
from datetime import timedelta
import  collections
import shutil
from TikTokApi.tiktok import TikTokApi
from tiktokdownloader import TikTokDownloader


class video_obj():
    def __init__(self, video_item_data, local_download_path="", edited_path=""):
        self.item = video_item_data
        self.author = helper.ignore_non_unicode(video_item_data['author']['uniqueId'])
        self.author_name = f"[{helper.ignore_non_unicode(video_item_data['author']['nickname'])}]"
        self.tk_id = video_item_data['video']['id']
        self.id = f"@{self.author}_{self.tk_id}"
        self.views = round(video_item_data['stats']['playCount'] / 1000000, 1)
        self.hearts = round(video_item_data['stats']['diggCount'] / 1000000, 1)
        self.comments = round(video_item_data['stats']['commentCount'] / 1000, 1)
        self.shares = round(video_item_data['stats']['shareCount'] / 1000, 1)
        self.created_date = datetime.datetime.fromtimestamp(video_item_data['createTime']).strftime(conf.time_str_format)
        self.tags = [str(word.replace('#', '').encode("ascii", "ignore"), 'utf-8') for word in
                     video_item_data['desc'].split(' ') if word.startswith('#')]
        self.tags = (self.author + '|' + ('|'.join(self.tags))).strip()
        self.duration = video_item_data['video']['duration']
        self.music = helper.ignore_non_unicode(video_item_data['music']['title'])
        self.music_url = video_item_data['music']['playUrl']
        self.post_url = f"https://tiktok.com/@{self.author}/video/{self.tk_id}"
        self.local_download_path = local_download_path
        self.edited_path = edited_path
        self.claimed = 0
        self.uploaded = 0
        self.last_update = time.strftime(conf.time_str_format)
        # self.is_downloaded = self.check_download()
        self.is_downloaded = 0

    def create_datapoint(self):
        datapoint = conf.description_datapoint.copy()
        datapoint['author'] = self.author
        datapoint['author_name'] = self.author_name
        datapoint['tk_id'] = self.tk_id
        datapoint['id'] = self.id
        datapoint['views'] = self.views
        datapoint['hearts'] = self.hearts
        datapoint['comments'] = self.comments
        datapoint['shares'] = self.shares
        datapoint['created_date'] = self.created_date
        datapoint['tags'] = self.tags
        datapoint['duration'] = self.duration
        datapoint['music'] = self.music
        datapoint['music_url'] = self.music_url
        datapoint['post_url'] = self.post_url
        datapoint['local_download_path'] = self.local_download_path
        datapoint['local_edit_path'] = self.edited_path
        datapoint['claimed'] = self.claimed
        datapoint['uploaded'] = self.uploaded
        datapoint['last_update'] = self.last_update
        datapoint['is_downloaded'] = self.is_downloaded
        return datapoint

    # def check_download(self):
    #     # video_info_data = pd.read_csv(self.total_video_info_path, sep=";", header=None, encoding='utf-8', engine='python')
    #     video_info_data = helper.load_description_data()
    #     if self.id in video_info_data.index:
    #         return 1
    #     else:
    #         return 0

    def make_line_for_save(self):
        return [self.id, self.author, self.views, self.tags, self.duration, self.music, self.post_url,
                self.local_download_path, self.claimed, self.uploaded, self.last_update]

    def download(self):

        download_success = False
        try:
            donwloader_web_id = ''.join(random.choice(string.digits) for _ in range(19))
            downloader = TikTokDownloader(self.post_url, donwloader_web_id)
            downloader.download(self.local_download_path)
            download_success = True
        except Exception as e:
            print(f"{self.id} - Can't download. Trying...")

            try:
                tk_api = TikTokApi.get_instance(use_test_endpoints=True)
                verify_FP_comb, random_did_comb = helper.create_random_verify_FP_random_did()
                downloaded_video_bytes = tk_api.get_Video_By_Url(self.post_url, custom_verifyFp=verify_FP_comb, custom_did=random_did_comb)

                with open(self.local_download_path, "wb") as out_file:  # open for [w]riting as [b]inary
                    out_file.write(downloaded_video_bytes)

                download_success = True
                print(f"{self.id} - Downloading successed")
            except Exception as e:
                print(f"{self.id} - [Last] Can't download.")

        if download_success:
            video_info_df = helper.load_description_data()
            try:
                video_info_df.update(pd.DataFrame([self.create_datapoint()]).set_index('id'))
                # columns_to_update = list(conf.description_datapoint.keys())[1:15]
                # values_to_update = list(self.create_datapoint().values())[1:15]
                # video_info_df.loc[self.id, columns_to_update] = values_to_update
            except:
                # self.is_downloaded = 1
                video_info_df = video_info_df.append(pd.DataFrame([self.create_datapoint()]).set_index('id'))
            helper.save_description_data(video_info_df)
        return download_success

class combination_obj():
    def __init__(self, info_df, all_comb_dir, id=None, restore=False):
        self.id = ''.join(random.choices(string.ascii_lowercase, k=15)) if id == None else id
        self.info_df = info_df if restore else self.sort_df(info_df)
        self.report_df = None
        self.author_col = 'author'
        self.post_info_col = ['author', 'author_name', 'views', 'hearts', 'comments', 'shares', 'tags', 'duration',
                              'claimed', 'uploaded']
        self.tag_col = 'tags'
        self.path_col = 'local_download_path'
        self.authors = ""
        self.tags = ""
        self.file_paths = []
        self.comb_dir = f"{all_comb_dir}/{self.id}"
        self.src_videos_dir = f"{self.comb_dir}/src"
        self.edited_videos_dir = f"{self.comb_dir}/edited"
        self.snapshot_dir = f"{self.comb_dir}/snapshot"
        self.concatenated_media_path = f"{self.comb_dir}/{self.id}.mp3"
        self.report_path = f"{self.comb_dir}/report_{self.id}.csv"
        self.intro_path = f"{self.comb_dir}/intro_{self.id}.mp4"
        self.total_duration = 0
        self.video_timeline = []
        self.created_time = time.strftime(conf.time_str_format)
        self.is_restored = restore
        if not restore:
            self.make_combination_files()
        self.extract_info()
        self.load_videos_from_src()

    def sort_df(self, input_df):
        temp_df = input_df.sort_values(by=['views'], ascending=False)
        top5_most_viewed_rows = temp_df.iloc[:5, :]
        top10_most_viewed_rows = (temp_df.iloc[5:10, :]).sample(frac=1)
        random_rows = (temp_df.iloc[10:, :]).sample(frac=1)
        postprocessing_result = pd.concat([top5_most_viewed_rows, top10_most_viewed_rows, random_rows])
        return postprocessing_result

    def extract_info(self):
        self.authors = list(self.info_df[self.author_col])
        self.tags = '|'.join(list(self.info_df[self.tag_col])).replace('tik', '').replace('tok', '')
        self.tags = self.tags.split("|")
        self.file_paths = [path.replace("./downloaded", conf.base_dir)
                               .replace("/content/drive/MyDrive/tk100mil/storage", conf.base_dir)
                               .replace("\\", "/")
                           for path in list(self.info_df[self.path_col])]

    def create_report(self):
        report_infos = [[row[0], timeline[2:], row[16], row[17], 0] for timeline, row in
                        zip(self.video_timeline, list(self.info_df.reset_index().values))]
        report_df = pd.DataFrame(data=report_infos,
                                 columns=['video_id', 'timeline', 'claimed', 'uploaded', 'is_edited'])
        report_df.index += 1
        report_df.index.rename('priority', inplace=True)
        report_df.to_csv(self.report_path, sep=';', encoding='utf-8')

        self.report_df = report_df

    def load_report(self):
        self.report_df = pd.read_csv(self.report_path, sep=";", encoding='utf-8')

    def save_report(self):
        self.report_df.to_csv(self.report_path, sep=";", index=None, encoding='utf-8')

    def update_report(self, video_name, column_name, column_value):
        self.report_df.loc[self.report_df['video_id'] == video_name, column_name] = column_value
        self.save_report()

    def make_combination_files(self):
        if not os.path.exists(conf.combination_dir):
            os.mkdir(conf.combination_dir)
        if not os.path.exists(self.comb_dir):
            os.mkdir(self.comb_dir)
        if not os.path.exists(self.src_videos_dir):
            os.mkdir(self.src_videos_dir)
        if not os.path.exists(self.edited_videos_dir):
            os.mkdir(self.edited_videos_dir)
        if not os.path.exists(self.snapshot_dir):
            os.mkdir(self.snapshot_dir)

        tk_api = TikTokApi.get_instance(use_test_endpoints=True)
        download_failed_list = []

        print(f"Downloading {len(self.info_df)} in about {timedelta(seconds=2*len(self.info_df))}....")
        for video_id, row in self.info_df.iterrows():
            verify_FP_comb, random_did_comb = helper.create_random_verify_FP_random_did()
            video_info = tk_api.getTikTokByUrl(row[12], custom_verifyFp=verify_FP_comb, custom_did=random_did_comb)
            if video_info['statusCode'] == 0:
                video_item = video_obj(video_item_data=video_info['itemInfo']['itemStruct'])
                video_item.local_download_path = f"{self.src_videos_dir}/{video_item.id}.mp4"
                time.sleep(1)
                download_success = video_item.download()
                if not download_success:
                    download_failed_list.append(video_id)
                else:
                    self.info_df.loc[video_item.id, 'local_download_path'] = video_item.local_download_path
                time.sleep(1)
            else:
                download_failed_list.append(video_id)

        # Save failed list to file
        self.info_df.loc[download_failed_list,'post_url'].to_csv(self.report_path.replace('report','failed'), sep=";", index=None, encoding='utf-8')

        self.info_df = self.info_df.drop(download_failed_list)

        print(f"Create new Combination files in {self.src_videos_dir}")

    def load_videos_from_src(self):
        if not os.path.exists(self.intro_path):
            self.create_intro_video()
        self.intro_video = mp.VideoFileClip(self.intro_path).resize(width=1080, height=1080)
        # self.endscreen_video = mp.VideoFileClip(f"{source_dir}/Squared_EndScreen.mp4").resize(width=1080, height=1080).crossfadein(1)
        self.transfer_screen_video = mp.VideoFileClip(f"{conf.source_dir}/Squared_TransferScreen.mp4").resize(width=1080,
                                                                                                         height=1080).crossfadein(
            0.2)
        self.backgrounf_video = mp.VideoFileClip(f"{conf.source_dir}/Squared_BluredBackground.mp4").resize(width=1080,
                                                                                                      height=1080)
        self.countdown_video = mp.VideoFileClip(f"{conf.source_dir}/countdown_60s.mp4")

    def create_intro_video(self):
        intro_background_video = mp.VideoFileClip(f"{conf.source_dir}/intro_background.mp4").resize(width=1080, height=1080)
        snapshot_video_height = 275
        snapshot_video_width = 154

        expected_paths = []

        file_paths = self.file_paths.copy()
        amount_of_batchs = 0
        if len(self.file_paths)/6 >= 6:
            amount_of_batchs = 6
        elif 3 <= len(self.file_paths)/6 < 6:
            amount_of_batchs = 3

        amount_of_videos_each_batch = 6

        for _ in range(amount_of_batchs):
            if len(file_paths) >= amount_of_videos_each_batch:
                batch = random.sample(file_paths, k=amount_of_videos_each_batch)
            else:
                batch = file_paths.copy()

            expected_paths.append(batch)
            file_paths = list(set(file_paths) - set(batch))

        batches = []
        batch_id = 1
        for batch in tqdm(expected_paths, desc=f"Creating intro video for {self.id}: ", position=0, leave=True):

            snapshot_video_path = f"{self.snapshot_dir}/intro_batch_{batch_id}.mp4"
            if not os.path.exists(snapshot_video_path):
                snapshot_videos = []
                for video_path in batch:
                    video = mp.VideoFileClip(video_path)
                    snapshot_video_start = random.randint(0, int(0.3 * video.duration))
                    snapshot_video_duration = 1
                    snapshot_video = video.subclip(snapshot_video_start,
                                                   snapshot_video_start + snapshot_video_duration).resize(
                        height=snapshot_video_height)
                    snapshot_video = fx.all.crop(snapshot_video, width=snapshot_video_width,
                                                 height=snapshot_video_height, x_center=snapshot_video_width / 2,
                                                 y_center=snapshot_video_height / 2)
                    snapshot_videos.append(snapshot_video)

                concanated_snapshot_videos = mp.concatenate_videoclips(snapshot_videos, method='compose').volumex(0)
                concanated_snapshot_videos.write_videofile(snapshot_video_path, fps=30, logger=None)
            else:
                concanated_snapshot_videos = mp.VideoFileClip(snapshot_video_path).resize(
                    height=snapshot_video_height).volumex(0)
                concanated_snapshot_videos = fx.all.crop(concanated_snapshot_videos, width=snapshot_video_width,
                                                         height=snapshot_video_height,
                                                         x_center=snapshot_video_width / 2,
                                                         y_center=snapshot_video_height / 2)

            batches.append(concanated_snapshot_videos)
            batch_id += 1

        if amount_of_batchs == 6:
            lst_line_1 = [batches[0].crossfadein(0.5), batches[1].crossfadein(1), batches[2].crossfadein(1.5)]
            lst_line_2 = [batches[3].crossfadein(1.5), batches[4].crossfadein(2), batches[5].crossfadein(2.5)]
            line_1 = mp.clips_array([lst_line_1])
            line_2 = mp.clips_array([lst_line_2])
            mp.CompositeVideoClip([intro_background_video, line_1.set_position(("right", "top")),
                                   line_2.set_position(("left", "bottom"))]).write_videofile(self.intro_path, fps=30,
                                                                                         logger=None)
        elif amount_of_batchs == 3:
            lst_line_2 = [batches[0].crossfadein(0.5), batches[1].crossfadein(1), batches[2].crossfadein(1.5)]
            line_2 = mp.clips_array([lst_line_2])
            mp.CompositeVideoClip([intro_background_video, line_2.set_position(("left", "bottom"))]).write_videofile(self.intro_path, fps=30,
                                                                                             logger=None)
        elif amount_of_batchs == 0:
            shutil.copyfile(f"{conf.source_dir}/intro_background.mp4", self.intro_path)

    def create_single_video(self, video_index, video_path, next_video_path=None):
        video_name = Path(video_path).name.replace(".mp4", "")

        # Update Doing processing to report BEFORE creating video
        self.update_report(video_name, 'is_edited', 0.5)

        video = mp.VideoFileClip(video_path).resize(height=1080).crossfadein(0.5)

        # Create 2 side posters
        left_side_text = f"{self.info_df.loc[video_name]['author_name'].replace('[','').replace(']','')}"
        right_side_text = f"{self.info_df.loc[video_name]['views']}M VIEWS"
        left_side_poster_path = f"{self.src_videos_dir}/{video_name}_left.png"
        right_side_poster_path = f"{self.src_videos_dir}/{video_name}_right.png"
        helper.create_side_poster(left_side_text, 90, left_side_poster_path)
        helper.create_side_poster(right_side_text, 270, right_side_poster_path)
        left_side_poster = mp.ImageClip(left_side_poster_path).set_duration(video.duration).crossfadein(2)
        right_side_poster = mp.ImageClip(right_side_poster_path).set_duration(video.duration).crossfadein(2)

        # Create Next video intro
        if next_video_path is not None:
            next_clip_thumb_path = f'{self.snapshot_dir}/thumb_{Path(next_video_path).name.replace(".mp4", "")}.png'

            next_clip = mp.VideoFileClip(next_video_path)
            next_clip_start = random.uniform(0, int(0.2 * next_clip.duration))
            next_clip_end = random.uniform(int(0.3 * next_clip.duration), int(0.5 * next_clip.duration))
            next_clip_duration = float(next_clip_end - next_clip_start)

            # next_clip_end = next_clip_start + next_clip_duration
            next_clip = next_clip.subclip(next_clip_start, next_clip_end)
            next_clip.save_frame(next_clip_thumb_path, t=1)  # Save thumb image before resize
            next_clip = next_clip.resize(width=125)

            # create the freeze video add the end
            next_clip_freeze = mp.ImageClip(next_clip_thumb_path).set_duration(
                video.duration - next_clip_duration).resize(width=125)
            next_clip = mp.concatenate_videoclips([next_clip, next_clip_freeze], method='compose')
            next_clip = next_clip.set_position((40, 30))
            next_clip = next_clip.volumex(0)

            countdown_timer = self.countdown_video.subclip(self.countdown_video.duration - video.duration,
                                                           self.countdown_video.duration).resize(width=200)

            corner_video = mp.CompositeVideoClip([countdown_timer, next_clip]).crossfadein(2)
            edited_video = mp.clips_array([[left_side_poster, video, right_side_poster, corner_video]])

            # Add Transfer screen if current video is not the last one
            edited_video = mp.concatenate_videoclips([edited_video, self.transfer_screen_video], method='compose')
        else:
            edited_video = mp.clips_array([[left_side_poster, video, right_side_poster]])

        edited_video = mp.CompositeVideoClip(
            [self.backgrounf_video.subclip(0, edited_video.duration),
             edited_video.resize(width=1080).set_position(("center", "center"))])

        # Fit square frame
        edited_video.write_videofile(f"{self.edited_videos_dir}/{video_index + 1}_{video_name}.mp4", fps=30,
                                     logger=None)

        # Update Finish processing to report AFTER creating video
        self.update_report(video_name,"is_edited",1 )

        return edited_video

    def concatenate_media(self):
        video_index = 0

        for video_path in tqdm(self.file_paths, desc=f"Start CONCATENATING videos for {self.id}: ", position=0, leave=True):
            video_name = Path(video_path).name

            self.load_report()

            if self.report_df.loc[self.report_df['video_id'] == video_name.replace(".mp4", ""), "is_edited"].values[0] == 0:
                # create new video
                if video_index < (len(self.file_paths) - 1):
                    edited_video = self.create_single_video(video_index, video_path, self.file_paths[video_index + 1])
                else:
                    edited_video = self.create_single_video(video_index, video_path)
            else:
                print(f"{video_index + 1}_{video_name} has existed")
                # load existed video
                # edited_video = mp.VideoFileClip(f"{self.edited_videos_dir}/{video_index + 1}_{video_name}")

            # videos.append(edited_video)
            video_index += 1

        # Add End Screen
        # videos.append(self.endscreen_video)
        # mp.concatenate_videoclips(videos, method='compose').write_videofile(self.concatenated_media_path.replace("mp3", "mp4"), fps=30, logger=None)

    def create_description(self):
        top5_videos = self.info_df.sort_values(by=['views']).tail(5)
        head_ = '#' + ' #'.join(list(top5_videos[self.author_col]))

        video_intro = f"{timedelta(seconds=0)} - Intro\n"

        intro_duration = 10
        timeline = intro_duration
        self.video_timeline.append(f"{timedelta(seconds=int(timeline))}")

        for video_path in tqdm(self.file_paths, desc=f"Getting video timeline for {self.id}: ", position=0, leave=True):
            # video = mp.VideoFileClip(video_path.replace("/content/drive/MyDrive/tk100mil/storage", base_dir ))
            video = mp.VideoFileClip(video_path)
            transfer_duration = 1
            timeline += round(float(video.duration + transfer_duration), 0)
            self.video_timeline.append(f"{timedelta(seconds=int(timeline))}")

        body_ = video_intro + '\n'.join([f"{timeline} - {row[0]} - {row[1].replace('[','').replace(']','')} ({row[2]}M views)"
                                         for timeline, row in zip(self.video_timeline, list(self.info_df[self.post_info_col].values))])

        fotter_ = []
        # get tags from top5 videos
        fotter_.extend(list(top5_videos['author']))
        fotter_.extend(list(top5_videos['author_name']))
        # get top 10 most common tags from videos
        fotter_.extend(list(list(dict(collections.Counter(self.tags).most_common(5)).keys())))
        fotter_ = ','.join(list(set(fotter_)))
        fotter_ = fotter_.replace("[","").replace("]","")
        description = f"{head_}\n\n{body_}\n\n{fotter_}"

        with open(os.path.join(self.comb_dir, f"description_{self.id}.txt"), 'w', encoding='utf-8') as des_f:
            des_f.write(description)

        # # create report file
        # if not self.is_restored:
        #     self.create_report()
        return description

