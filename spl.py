#!/usr/bin/python -u
# -*- coding: utf-8 -*-
#
#  Splunk API 経由でサーチを実行し、結果を CSV で保存する。
#

import logging
import logging.config
import os
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser
from argparse import ArgumentParser
from splunkutils.search import main

LOG_FORMAT = '%(asctime)s %(levelname)-7s %(module)s:%(lineno)s:%(funcName)s - %(message)s'
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
DEFAULT_CONF = 'spl.conf'

def load_config(conf_path):
    try:
        logging.config.fileConfig(conf_path)
    except KeyError:
        logging.basicConfig(level='INFO', format=LOG_FORMAT, datefmt=DATE_FORMAT)
    logging.debug('%s has been loaded', conf_path)
    conf = ConfigParser()
    conf.read(conf_path)
    return conf

if __name__ == '__main__':
    parser = ArgumentParser('Reputation Checker')
    parser.add_argument('-c', dest='conf',
        help='Path to config file', default=DEFAULT_CONF)
    parser.add_argument('--earliest', dest='earliest', default=None,
        help='ISO8601 format. e.g. 2018-10-10T12:00:00')
    parser.add_argument('--latest', dest='latest', default=None,
        help='ISO8601 format. e.g. 2018-10-10T13:00:00')
    args = parser.parse_args()
    conf = load_config(args.conf)

    host = conf.get('splunk', 'host')
    port = conf.getint('splunk', 'port')
    username = conf.get('splunk', 'username')
    password = conf.get('splunk', 'password')
    app = conf.get('splunk', 'app')

    data_dir = conf.get('loadtrend', 'data_dir')
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    # See also RULES_SPLUNK in splunk_utils/__init__.py
    flags = {
        '--user': username,
        '--password': password,
        '--host': host,
        '--port': port,
        '--app': app,
        '--output_mode': 'csv',
    }
    if args.earliest:
        flags.update({'--earliest_time': args.earliest})
    if args.latest:
        flags.update({'--latest_time': args.latest})

    for section in conf.sections():
        if not section.startswith('query:'):
            continue
        query_id = section.split(':', 1)[1]
        search_query = conf.get(section, 'search')
        logging.info("Loaded search query %s: %s", query_id, search_query)

        search_args = ["{}={}".format(k, v) for k, v in flags.items()]
        search_args.append(search_query)
        main(search_args, data_dir=data_dir, query_id=query_id)

