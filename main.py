"""Simple script to download images from the SPC Mesoanalysis Archive.

Output will be saved in a .zip file with the name of the requested sector.
Uses tqdm to output a progress bar.
"""
from __future__ import print_function

import numpy as np
import os, subprocess, sys
import time
from datetime import datetime, timedelta
import argparse
import shutil
from multiprocessing import Pool
from functools import wraps
import logging

from parms import variables

WGET = shutil.which('wget')
if WGET is None:
    raise ValueError("wget couldn't be located on the file system.")

script_path = os.path.dirname(os.path.realpath(__file__))
download_dir = "%s/downloads" % (script_path)
base_url = "https://www.spc.noaa.gov/exper/mesoanalysis"

# Set up the log file
logging.basicConfig(filename='%s/logs/info.log' % (script_path),
                format='%(levelname)s %(asctime)s :: %(message)s',
                datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger()
log.setLevel(logging.INFO)

def timeit(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        ts = time.time()
        result = f(*args, **kwargs)
        te = time.time()
        log.info('Function: %s took: %2.4f sec' % (f.__name__, te-ts))
        log.info("************************")
        return result
    return wrap

def execute(arg):
    process = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE,
              stderr=subprocess.PIPE)
    process.communicate()
    return process

def unpack(func):
    @wraps(func)
    def wrapper(arg_tuple):
        return func(*arg_tuple)
    return wrapper

@unpack
def execute_download(full_name, url):
    arg = "%s -O %s %s" % (WGET, full_name, url)
    log.info(url)
    execute(arg)
    time.sleep(0.25)

def query_files(start, end, sector):
    n_hours = int((end-start).seconds/3600.) + 1
    n_vars = len(variables) + 2
    n_images = int(n_hours * n_vars)

    downloads = {}
    for i in range(0, n_hours):

        # Not sure why there are four different date formats on that page...
        datestring0 = datetime.strftime(start, "%Y%m%d")
        datestring1 = datetime.strftime(start, "%Y%m%d_%H00")
        datestring2 = datetime.strftime(start, "%y%m%d_%H00")
        datestring3 = datetime.strftime(start, "%y%m%d%H")

        ########################################################################
        # Radar and surface observations (different naming convection)
        ########################################################################
        url1 = "%s/s%s/rgnlrad/rad_%s.gif" % (base_url, sector, datestring1)
        url2 = "%s/s%s/bigsfc/sfc_%s.gif" % (base_url, sector, datestring2)

        # Regional radar
        data_dir = "%s/%s/%s/rgnlrad/" % (download_dir, sector, datestring0)
        if not os.path.exists(data_dir): os.makedirs(data_dir)
        filename = "%s/rad_%s.gif" % (data_dir, datestring1)
        downloads[filename] = url1

        # Surface analysis
        data_dir = "%s/%s/%s/bigsfc/" % (download_dir, sector, datestring0)
        if not os.path.exists(data_dir): os.makedirs(data_dir)
        filename = "%s/sfc_%s.gif" % (data_dir, datestring1)
        downloads[filename] = url2

        ########################################################################
        # Additional variables
        ########################################################################
        for var in variables.keys():
            url = "%s/s%s/%s/%s_%s.gif" % (base_url, sector, var, var,
                                           datestring3)

            name = variables[var]
            data_dir = "%s/%s/%s/%s" % (download_dir, sector, datestring0, name)

            if not os.path.exists(data_dir): os.makedirs(data_dir)
            filename = "%s/%s_%s.gif" % (data_dir, var, datestring1)

            downloads[filename] = url

        start += timedelta(hours=1)

    return downloads

@timeit
def get_files(start, end, sector=None):
    if sector is None: sector = '20'
    downloads = query_files(start, end, sector)
    my_pool = Pool(np.clip(1, len(downloads), 6))
    my_pool.map(execute_download, zip(downloads.keys(), downloads.values()))
    my_pool.close()
    my_pool.terminate()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(dest='start_time', help='Initial hour for data retrieval. Form is    \
                    YYYY-MM-DD/HH')
    ap.add_argument(dest='end_time', help='Last hour for data retrieval. Form is         \
                    YYYY-MM-DD/HH')
    ap.add_argument('-s', dest='sector', help='Sector to download')
    args = ap.parse_args()

    now = datetime.utcnow()
    last_available = datetime(2020, 5, 24, 0)

    # Convert the user-requested start and end times to datetime objects
    start = datetime.strptime(args.start_time, "%Y-%m-%d/%H")
    end = datetime.strptime(args.end_time, "%Y-%m-%d/%H")

    if start >= last_available:
        get_files(start, end, sector=args.sector)
    else:
        print("Requested time is out of SPC-archive bounds. Last available \
              time is: %s" % (datetime.strftime(last_available, "%Y-%m-%d/%H")))

if __name__ == "__main__":
    main()
