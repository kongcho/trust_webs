import requests
import hunspell
from nltk import word_tokenize
from bs4 import BeautifulSoup
from bs4.element import Comment
from spam_lists import SPAMHAUS_DBL

class web(object):

    def __init__(self, url, from_date, to_date):
        self.base_url = "http://web.archive.org"
        self.url = url
        self.all_params = ["perc_correct_words", "perc_alive_links", "perc_nonspam_links"]

        # gets archived pages url
        self.time_urls = self.get_timestamp_urls(from_date, to_date)
        if self.time_urls == 1 or len(self.time_urls) == 0:
            self.success = False
            return
        else:
            self.success = True

        # parse the first possible archived page
        self.parser = "lxml"
        not_successful = True
        for i in range(len(self.time_urls)):
            self.parse_url = self.time_urls[i]
            self.soup = self._get_soup(self.parse_url)
            if self.soup != 1:
                not_successful = False
                break
        if not_successful:
            error_str = "Error: can't parse html for any pages between these dates for {0}"\
                .format(self.url)
            self.error = error_str
            self.success = False
            return

        # get statistics on the first archived page
        self.setup_params(self.parse_url)

    # helper, uses wayback api to get last timestamped page url
    def _get_latest_wburl(self):
        wburl = "https://archive.org/wayback/available".format(self.url)
        r = requests.get(wburl, params={
            "url": self.url
        })
        dic = r.json()["archived_snapshots"]["closest"]
        if dic["available"]:
            return dic["url"]

    def _get_timestamps(self, from_yr, to_year):
        cdxurl = "{0}/cdx/search/cdx".format(self.base_url)
        r = requests.get(cdxurl, params={
            "url": self.url,
            "fl": "timestamp",
            "output": "json",
            "from": from_yr,
            "to": to_year
        })
        if r.status_code != 200:
            error_str = "Error: Archive doesn't exist, HTTP code: {0} for {1}"\
                  .format(r.status_code, self.url)
            print(error_str)
            self.error = error_str
            return 1
        json_obj = r.json()[1:]
        timestamps = [x[0] for x in json_obj]
        if len(timestamps) == 0:
            error_str = "Error: no archived results for this url in between these dates: {0}"\
                .format(self.url)
            print(error_str)
            self.error = error_str
            return 1
        return timestamps

    # collects all wayback archived pages in between dates
    def get_timestamp_urls(self, from_yr, to_year):
        timestamps = self._get_timestamps(from_yr, to_year)
        if timestamps == 1:
            return 1
        url_list = []
        for timestamp in timestamps:
            url_list.append("{0}/web/{1}id_/{2}".format(self.base_url, timestamp, self.url))
        return url_list

    def _get_soup(self, parse_url):
        try:
            r = requests.get(parse_url)
        except Exception as e:
            error_str = "Error: {0}".format(e.message)
            return 1
        if r.status_code != 200:
            error_str = "Error: HTTP code: {0} for {1}".format(r.status_code, parse_url)
            return 1
        soup = BeautifulSoup(r.content, self.parser)
        return soup

    # editted from https://stackoverflow.com/questions/1936466/
    def _is_tag_visible(self, element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    # editted from https://stackoverflow.com/questions/1936466/
    def _text_from_html(self, soup):
        texts = soup.findAll(text=True)
        visible_texts = filter(self._is_tag_visible, texts)
        return u" ".join(t.strip() for t in visible_texts)

    def _get_web_text(self, soup):
        return self._text_from_html(soup)

    def _words_from_text(self, text):
        tokens = word_tokenize(text)
        words = [x for x in tokens if x.isalpha()]
        return words

    # gets list of words from webpage
    def get_web_words(self):
        text = self._get_web_text(self.soup)
        return self._words_from_text(text) if text is not None else None

    def _count_spellcheck(self, words, dict_locations=("./dict/en_US.dic", "./dict/en_US.aff")):
        correct = 0
        incorrect = 0
        loc1, loc2 = dict_locations
        checker = hunspell.HunSpell(loc1, loc2)
        for word in words:
            if checker.spell(word):
                correct += 1
            else:
                incorrect += 1
        return correct, incorrect

    # gets percentage of correctly spelt words as a statistic
    def get_param_spellcheck(self):
        words = self.get_web_words()
        correct, incorrect = self._count_spellcheck(words)
        total = correct + incorrect
        return float(correct)/total if total != 0 else 0

    def _get_linked_urls(self, soup):
        all_links = soup.findAll("a")
        links = []
        for link in all_links:
            if "http" in link:
                links.append(link)
        return links

    def _does_link_exists(self, url):
        r = requests.get(url)
        return True if r.status_code == 200 else False

    def _get_alive_links(self, links):
        alives = []
        for link in links:
            if self._does_link_exists(link):
                alives.append(link)
        return alives

    # gets percentage of links that are alive from webpage as statistic
    def get_param_alive_links(self):
        links = self._get_linked_urls(self.soup)
        good_links = len(self._get_alive_links(links))
        return float(good_links)/len(links) if len(links) != 0 else None

    # gets percentage of links that are not spam
    def get_param_spam_links(self):
        links = self._get_linked_urls(self.soup)
        good_links = self._get_alive_links(links)
        non_spams = 0
        for link in good_links:
            if link not in SPAMHAUS_DBL:
                non_spams += 1
        return float(non_spams)/len(links) if len(links) != 0 else None

    def _create_param(self, key, value):
        self.params[key] = value
        return 0

    # calculates lists of statistics for webpage
    def setup_params(self, url):
        self.params = {}
        self._create_param("perc_correct_words", self.get_param_spellcheck())
        self._create_param("perc_alive_links", self.get_param_alive_links())
        self._create_param("perc_nonspam_links", self.get_param_spam_links())

if __name__ == "__main__":
    url = "gamevance.net"
    w = web(url, 2011, 2011)
    print w.time_urls
    pass
