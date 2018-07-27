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

from parse import web
import csv
import scipy.cluster.vq as vq
import numpy as np

import matplotlib.pyplot as plt

class trusts(object):

    def __init__(self, websites_dir="./data/domains.csv"):
        self.all_webs = self.get_websites(websites_dir)
        self.incompleted_webs = [x for x in self.all_webs]
        self.trusts = []
        self.untrusts = []

    def _get_unique_arr(self, arr):
        unique = []
        [unique.append(i) for i in arr if i not in unique]
        return unique

    # gets list of websites to analyse through from file
    def get_websites(self, filename, col_no=1, skip_rows=2):
        websites = []
        with open(filename, "r") as f:
            for _ in range(skip_rows):
                next(f)
            r = csv.reader(f, delimiter=",", skipinitialspace=True)
            for row in r:
                websites.append(row[col_no])
        return self._get_unique_arr(websites)

    def _is_gov_web(self, website):
        return True if ".gov" in website else False

    # first pass of websites, for assumes all ".gov" are trustworthy
    def check_first(self, websites):
        trusts = []
        untrusts = []
        for website in websites:
            first_bools = [self._is_gov_web(website)]
            if all(first_bools):
                trusts.append(website)
                websites.remove(website)
        return trusts, untrusts

    # parses the wayback webpages for given urls
    def setup_webs(self, urls):
        webs = [web(url) for url in urls]
        return webs

    # assumes website is untrustworthy if it doesn't have an archive
    def check_archive_exists(self):
        unsuccesses = []
        successes = []
        for i, web in enumerate(self.parsed_webs):
            if not web.success:
                self.untrusts.append(web.url)
                unsuccesses.append(i)
            else:
                successes.append(i)
        self.parsed_webs = [self.parsed_webs[i] for i in successes]
        self.incompleted_webs = [self.incompleted_webs[i] for i in unsuccesses]
        return 0

    def _format_params(self, webs):
        whole_arr = []
        for web in webs:
            param_arr = []
            for key in web.all_params:
                if key in web.params and web.params[key] is not None:
                    param_arr.append(web.params[key])
                else:
                    param_arr.append(0.0)
            whole_arr.append(param_arr)
        return whole_arr

    def _convert_binary_to_bool(self, arr):
        bools = []
        for i in arr:
            if i == 0:
                bools.append(True)
            else:
                bools.append(False)
        return bools

    def _calculate_k_means(self, webs):
        arr = np.array(self._format_params(webs))
        centroids, label = vq.kmeans2(arr, 2, minit='points')

        # plt.scatter(arr[:,0], arr[:,1])
        # plt.scatter(centroids[:,0],centroids[:,1], marker='o', s = 500, linewidths=2, c='none')
        # plt.scatter(centroids[:,0],centroids[:,1], marker='x', s = 500, linewidths=2)
        # plt.show()

        bools = self._convert_binary_to_bool(label)

        return centroids, bools

    # uses params for each website and k-means to cluster the websites into 2 different categories
    def check_params(self, webs):
        centroids, bools = self._calculate_k_means(webs)

        # assume most websites are trustworthy from the list
        if np.sum(bools) > (len(webs)-np.sum(bools)):
            idxes = bools
            bools = np.logical_not(bools)
        else:
            idxes = np.logical_not(bools)

        webs = np.array(webs)
        unpack_trusts = [web.url for web in webs[idxes]]
        unpack_untrusts = [web.url for web in webs[bools]]
        self.trusts = np.concatenate([self.trusts, unpack_trusts])
        self.untrusts = np.concatenate([self.untrusts, unpack_untrusts])

    # main function that goes through different checks to filter
    def get_trusts(self):
        self.trusts, self.untrusts = self.check_first(self.incompleted_webs)
        self.parsed_webs = self.setup_webs(self.incompleted_webs)
        self.check_archive_exists()
        self.check_params(self.parsed_webs)
        return 0

    def _arr_to_csv(self, arr, fout):
        with open(fout, "wb") as f:
            w = csv.writer(f, delimiter=",", lineterminator="\n")
            for row in arr:
                w.writerow([row])
        return 0

    # prints out results of legit and fake websites to files
    def print_trusts_to_file(self, fout_legit, fout_fake):
        trusts_no = len(self.trusts)
        untrusts_no = len(self.untrusts)
        print("total number of websites:\t{0}".format(len(self.all_webs)))
        print("number of legit websites:\t{0}".format(trusts_no))
        print("number of fake websites:\t{0}".format(untrusts_no))
        print("percentage of legit websites:\t{0:.2f}"\
              .format(float(trusts_no)/(trusts_no+untrusts_no)))

        self._arr_to_csv(np.concatenate([["legit"], self.trusts]), fout_legit)
        self._arr_to_csv(np.concatenate([["fake"], self.untrusts]), fout_fake)
        return 0

if __name__ == "__main__":
    run = trusts()
    run.get_trusts()
    run.print_trusts_to_file("./legit.csv", "./fakes.csv")
