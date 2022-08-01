from argparse import ArgumentParser
import os
from urllib.parse import parse_qsl, urlparse
import requests
from fake_useragent import UserAgent


class TikTokDownloader:
    HEADERS = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'User-Agent': UserAgent().random,
        'Accept': '*/*',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Dest': 'video',
        'Referer': 'https://www.tiktok.com/',
        'Accept-Language': 'en-US,en;q=0.9,bs;q=0.8,sr;q=0.7,hr;q=0.6',
        'sec-gpc': '1',
        'Range': 'bytes=0-',
    }

    def __init__(self, url: str, web_id: str):
        self.__url = url
        self.__cookies = {
            'tt_webid': web_id,
            'tt_webid_v2': web_id
        }

    def __get_video_url(self) -> str:
        response = requests.get(self.__url, cookies=self.__cookies, headers=TikTokDownloader.HEADERS)
        return response.text.split('"playAddr":"')[1].split('"')[0].replace(r'\u0026', '&')

    def download(self, file_path: str):
        video_url = self.__get_video_url()
        url = urlparse(video_url)

        params = tuple(parse_qsl(url.query))
        request = requests.Request(method='GET',
                                   url='{}://{}{}'.format(url.scheme,
                                                          url.netloc, url.path),
                                   cookies=self.__cookies,
                                   headers=TikTokDownloader.HEADERS,
                                   params=params)
        prepared_request = request.prepare()
        session = requests.Session()
        response = session.send(request=prepared_request)
        response.raise_for_status()
        # if os.path.exists(file_path):
        #     choice = input('File already exists. Overwrite? (Y/N): ')
        #     if choice.lower() != 'y':
        #         return
        with open(os.path.abspath(file_path), 'wb') as output_file:
            output_file.write(response.content)

"""
if __name__ == "__main__":
    # https://github.com/nemanjastokuca/tiktok-downloader
    parser = ArgumentParser()
    parser.add_argument('--web-id', help='Value of tt_webid or tt_webid_v2 cookie (they are the same).')
    parser.add_argument('-o', '--output', default='download.mp4', help='Full output path.')
    parser.add_argument('url', help='Video url (https://www.tiktok.com/@username/video/1234567890123456789 or https://vm.tiktok.com/a1b2c3/).')
    args = parser.parse_args()
    
    downloader = TikTokDownloader(args.url, args.web_id)
    downloader.download(args.output)
"""