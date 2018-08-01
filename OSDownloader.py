import argparse
import os
import sys
import time
import datetime
import json
import urllib.request as request
import gzip
from xmlrpc.client import ServerProxy


class OpenSub(object):

    def __init__(self, path):
        self.TAGS = ['bluray', 'cam', 'dvb', 'dvd', 'hd-dvd', 'hdtv', 'ppv', 'telecine', 'telesync', 'tv', 'vhs', 'vod',
                     'web-dl', 'webrip', 'workprint']
        self.OPENSUBTITLES_SERVER = 'https://api.opensubtitles.org:443/xml-rpc'
        self.USER_AGENT = 'TemporaryUserAgent' # needs to be changed from time to time to the recent temporary UA
        self.xmlrpc = ServerProxy(self.OPENSUBTITLES_SERVER,
                                  allow_none=True)
        self.language = 'eng'
        self.token = None
        self.mv_name = None
        self.path = path
        try:
            with open("opensubtitles_userpass.txt", 'r') as f:
                f = f.read()
                user = f.split('\n')[0].split('=')[1]
                password = f.split('\n')[1].split('=')[1]
            self.user = user
            self.passw = password
        except FileNotFoundError:
            print("Please fill OpenSubtitles credentials in opensubtitles_userpass.txt")
        if self.login(self.user, self.passw):
            print("[OpenSubtitles] Login Successful")
        else:
            print("[OpenSubtitles] Login Failed")

    def _get_from_data_or_none(self, key):
        '''Return the key recieved from data if the status is 200,
        otherwise return None.
        '''
        status = self.data.get('status').split()[0]
        return self.data.get(key) if '200' == status else None

    def login(self, username, password):
        '''Returns token is login is ok, otherwise None.
        '''
        self.data = self.xmlrpc.LogIn(username, password,
                                      self.language, self.USER_AGENT)
        token = self._get_from_data_or_none('token')
        if token:
            self.token = token
        return token

    def logout(self):
        '''Returns True if logout is ok, otherwise None.
        '''
        data = self.xmlrpc.LogOut(self.token)
        return '200' in data.get('status')

    def search_subtitles(self, params):
        '''Returns a list with the subtitles info.
        '''
        self.data = self.xmlrpc.SearchSubtitles(self.token, params)
        return self._get_from_data_or_none('data')

    def download_subtitles(self, payload):
        """
        :return:
        """
        print("Attempting to download subtitles...")
        search_result = self.search_subtitles([payload])
        if search_result:
            dllink = self.analyse_result(search_result, payload)
            gzfile = request.urlopen(dllink)
            try:
                with gzip.open(gzfile, 'rb') as f:
                    with open(self.path + "\\" + self.mv_name + '.srt', 'wb') as sub_file:
                        sub_file.write(f.read())
                        print("[OpenSubtitles] Subtitles downloaded for: " + self.mv_name)
                        # Update stats
                        with open("metadata.json", "r") as jsonFile:
                            data = json.load(jsonFile)
                        data['num_of_movies_in_db'] = int(data['num_of_movies_in_db']) + 1
                        data['latest_movie_added']['name'] = self.mv_name
                        data['latest_movie_added']['time'] = str(datetime.datetime.now())
                        with open("metadata.json", "w") as jsonFile:
                            json.dump(data, jsonFile, indent=4)
                        # End Update
                        return os.path.join(self.path, self.mv_name + ".srt")
            except PermissionError:
                print("[OpenSubtitles] Permission Error: when creating subtitles for {}".format(self.mv_name))

    def analyse_result(self, result, payload):
        """
        :param result: Search result to find appropriate subtitles
        :return: Download Link of best match for subtitles
        """
        score = 0
        dllink = None
        for record in result:
            if record.get("MovieName").lower() == payload['query'].lower() and record.get("SubLanguageID") == 'eng':
                self.mv_name = record.get("MovieName")
                dllink = record.get('SubDownloadLink')
                break
            if record.get('Score', 0) > score and record.get("SubLanguageID") == 'eng':
                self.mv_name = record.get("MovieName")
                score = record.get('Score', 0)
                dllink = record.get('SubDownloadLink')

        return dllink

    def create_payload(self, mv_name):
        """
        :param lang: Subtitle Language
        :param mv_name: Movie name to search
        :return: Payload containing data about file
        """
        payload = {}
        payload['query'] = mv_name
        payload['SubLanguageID'] = self.language
        payload['SubFormat'] = 'srt'
        return payload

    def search_and_download(self, mv_name):
        movie_db = [os.path.splitext(name)[0] for name in os.listdir(self.path)]
        for local in movie_db:
            if mv_name.lower() == local.lower():
                return os.path.join(self.path, mv_name + ".srt")
        try:
            return self.download_subtitles(self.create_payload(mv_name))
        except:
            print("[OpenSubtitles] Could not download subtitles for " + mv_name)

    def download_top_1000(self):
        with open(os.path.join(os.getcwd(), "top1000.txt"), "r") as f:
            f = f.read()
            i = 1
            for mv_name in f.split("\n"):
                try:
                    self.search_and_download(mv_name)
                except:
                    e = sys.exc_info()[0]
                    print("ERROR: " + str(e))
                    print("Error: subtitles not downloaded for: " + mv_name)
                i = i + 1
                if i % 39 == 0:
                    time.sleep(11)


def down_sub(path, mv_name='', top_flag=False):
    """Driver function to find subtitles with OpenSubtitle
    """
    downloader_os = OpenSub(path)  # OpenSubtitles
    if top_flag:
        downloader_os.download_top_1000()
    else:
        try:
            downloader_os.search_and_download(mv_name)
        except:
            print("Error: subtitles not downloaded for: " + mv_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path',
                        help='Path to the subtitles DB directory',
                        dest="path",
                        metavar="PATH",
                        default=os.getcwd(),
                        type=str,
                        required="True")
    parser.add_argument('-s', '--search',
                        help='Search and download the subtitles of a specific movie',
                        dest="mv_name",
                        type=str,
                        default='',
                        metavar="MOVIE_NAME")
    parser.add_argument('-t', '--top1000',
                        help='Download top 1000 subtitles of all time from OpenSubtitles (~20 minutes)',
                        dest="top_flag",
                        action="store_true")
    args = parser.parse_args()
    path = args.path
    mv_name = args.mv_name
    top_flag = args.top_flag

    if os.path.isdir(path):
        down_sub(path, mv_name, top_flag)
    else:
        print("usage: PATH should be a directory")


if __name__ == "__main__":
    main()
