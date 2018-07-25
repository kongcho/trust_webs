"""
Write a script in R that would check if these domains are archived in wayback machine (http://archive.org/web/), and whether or not it has results in 2010 and 2011. A few of these sites might be spam sites, so I would recommend running the code via a university/library computer and not your personal machine.

Provide a way of checking systematically if these are legit sites (e.g. accuweather is legit) or fake sites.

first past filters
- all ".gov" are good

manual ways
- % correctly spelt words
- % legit links
- % spam words dict
  - free etc
- % links that leads to ads
"""

import csv

import urllib
import json
import requests

class web(object):

    def __init__(self, url):
        self.base_url = "http://web.archive.org"
        self.url = url
        self.time_urls = self.get_timestamp_urls(2010, 2011)

    def _get_latest_wburl(self):
        wburl = "https://archive.org/wayback/available?url={0}".format(self.url)
        f = urllib.urlopen(wburl)
        json_obj = json.load(f)
        dic = json_obj["archived_snapshots"]["closest"]
        if dic["available"]:
            return dic["url"]

    def _get_timestamps(self, from_yr, to_year):
        cdxurl = "{0}/cdx/search/cdx?url={1}&from={2}&to={3}&fl=timestamp"\
                 .format(self.base_url, self.url, from_yr, to_year)
        req = urllib.urlopen(cdxurl)
        str_list = req.read()
        timestamps = str_list.strip().split("\n")
        if len(timestamps) == 0:
            print "Error: no archived results for this url in between these dats"
            return 1
        return timestamps

    def get_timestamp_urls(self, from_yr, to_year):
        timestamps = self._get_timestamps(from_yr, to_year)
        if timestamps == 1:
            return 1
        url_list = []
        for timestamp in timestamps:
            url_list.append("{0}/web/{1}/{2}".format(self.base_url, timestamp, self.url))
        return url_list

# gets list of websites to analyse through from file
def get_websites(filename, col_no=1, skip_rows=2):
    websites = []
    with open(filename, "r") as f:
        for _ in range(skip_rows):
            next(f)
        r = csv.reader(f, delimiter=",", skipinitialspace=True)
        for row in reader:
            websites.append(row[col_no])
    return websites

if __name__ == "__main__":
    url = "facdn.com"
    webs = web(url)
    print webs.time_urls
