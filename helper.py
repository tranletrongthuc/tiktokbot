import config as conf
from PIL import Image, ImageFont, ImageDraw
import pandas as pd
import collections
import os
import random

def ignore_non_unicode(text):
    return str(text.encode("ascii", "ignore"), 'utf-8')

def create_side_poster(text, ratio, save_path):
    side_poster = Image.open(f"{conf.source_dir}/side_poster.png")
    fontpath = f"{conf.source_dir}/Lovelo-LineBold.ttf"
    max_width = 550

    font_size = 70
    font = ImageFont.truetype(fontpath, font_size, encoding='utf-8')
    left_side_text_size = font.getsize(text)

    while left_side_text_size[0] > max_width:
        font_size -= 1
        font = ImageFont.truetype(fontpath, font_size, encoding='utf-8')
        left_side_text_size = font.getsize(text)

    draw = ImageDraw.Draw(side_poster)
    draw.text(
        (
            (side_poster.width - left_side_text_size[0]) / 2,
            (side_poster.height - left_side_text_size[1]) / 2
        ),
        text, font=font, fill="#ab2408")
    side_poster = side_poster.rotate(ratio, expand=True)
    side_poster.save(save_path)

def load_tags():
    hashtags_text = "tiktok|foryoupage|fyp|foryou|viral|love|funny|memes|followme|cute|fun|music|happy|\
                    fashion|follow|comedy|bestvideo|tiktok4fun|thisis4u|loveyoutiktok|featurethis|featureme|\
                    prank|15svines|trending|1mincomedy|blooper|1minaudition|dancechallenge|badboydance|\
                    danceinpublic|dancekpop|dancecover|danceid|dancemoves|dancetutorial|punchdance|dancer|\
                    dancevideo|dancemom|dancelove|beautyls|beautyhacks|beautytips|beautyfull|unlockbeauty|\
                    sleepingbeauty|naturalbeauty|hudabeauty|beautyofnature|beautytt|beautyblogger|\
                    beauty4charity|beautybeast|beautychallenge|homebeautyhacks|danceforbeauty|showyourbeauty"
    extended_hashtags = hashtags_text.split("|")

    tags = [h.strip() for h in extended_hashtags]

    try:
        loaded_hashtags = []
        videos_info = load_description_data()
        # videos_info = pd.read_csv(conf.video_description_path, sep=";", header=None, encoding='utf-8', engine='python')
        lines = list(videos_info['tags'])
        for line in lines:
            loaded_hashtags.extend([t for t in line.split("|") if t != ''])
        tags.extend(loaded_hashtags)
    except:
        pass

    # Get top 20 most common hashtags
    tags = [tag[0] for tag in collections.Counter(tags).most_common(20)]
    return tags

def load_tags_from_file(tags_file_path=f"{conf.base_dir}/specific_tags.txt"):
    tags = []
    if os.path.exists(tags_file_path):
        with open(tags_file_path, 'r', encoding='utf-8') as load_tags_f:
            tags = load_tags_f.readlines()
            tags = [tag.replace('\n', '') for tag in tags]
        tags = list(set(tags))
    return tags

def load_description_data():
    data = pd.read_csv(conf.video_description_path, sep=";", encoding='utf-8', engine='python')
    data = data.set_index('id')
    return data

def save_description_data(video_description_data):
    video_description_data.reset_index().to_csv(conf.video_description_path, sep=";", index=None, encoding='utf-8')
def create_random_verify_FP_random_did():
    verify_FP = f"verify_" \
                f"{''.join(random.choice(conf.all_letters) for _ in range(8))}_" \
                f"{''.join(random.choice(conf.all_letters) for _ in range(8))}_" \
                f"{''.join(random.choice(conf.all_letters) for _ in range(4))}_" \
                f"{''.join(random.choice(conf.all_letters) for _ in range(4))}_" \
                f"{''.join(random.choice(conf.all_letters) for _ in range(4))}_" \
                f"{''.join(random.choice(conf.all_letters) for _ in range(12))}"
    random_did = str(random.randint(10000, 999999999))

    return verify_FP, random_did

def cluster_videos():
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    print(f"***Clustering video data***")
    video_data = load_description_data()

    X = video_data[['views','hearts','comments','shares','duration']]
    X = StandardScaler().fit_transform(X)

    kmeans = KMeans(n_clusters=10)
    kmeans.fit(X)
    labels = kmeans.predict(X)
    video_data['label'] = list(labels)
    # print(video_data.groupby('label').sum('duration'))
    return video_data, list(set(labels))

