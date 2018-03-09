# -*- coding: utf-8 -*-
#!/usr/bin/env python
'''
Created on Mar 9, 2018

@author: s1m0n4
@copyright: 2018 s1m0n4
'''
import argparse
import logging
import os
import sys
import requests
import json
from datetime import datetime, timedelta
import utils


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Contains utilities to manage discussions. Moderator privileges required.")
    parser.add_argument("--config", type=str, required=True, help="Path to the config file containing Disqus API secret/public keys")
    parser.add_argument('--limit-days', type=int, default=1, help="Limit the queries to the specified number of days in the past")
    parser.add_argument("--log", type=str, help="Path to the log file")
    parser.add_argument('--close-bar', action='store_true', help="Close threads with link compliant with format 'http://hookii.org/bar-%y-%m%d/' (ex:/bar-18-0309/) from past dates")
    
    options = parser.parse_args()
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s: %(message)s', datefmt='%y%m%d%H%M%S')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    if options.log:
        fhandler = logging.FileHandler(options.log)
        fhandler.setFormatter(formatter)
        fhandler.setLevel(logging.DEBUG)
        logger.addHandler(fhandler)
    logging.captureWarnings(True)
    api_url = "https://disqus.com/api/3.0/"
    try:
        error = 0
        closed = 0
        
        logger.info("Verify config")
        config_text = utils.read_file(options.config)
        if not config_text:
            logger.error("Failed to read the required config file: %s" % options.config)
            exit(1)
        config = json.loads(config_text)
        utils.verify_required_setting(config, ["disqus-secret", "disqus-public", "disqus-access-token", "forum"], logger)
        
        if options.limit_days > 500:
            logger.warning("Cannot support %d days. Limiting days in the past to 500" % options.limit_days)
            
        params = {"api_key": config["disqus-public"],
                  "api_secret": config["disqus-secret"],
                  "forum": config["forum"],
                  "access_token": config["disqus-access-token"]}

        if options.close_bar:
            relpaths = []
            today = datetime.now()
            stop = options.limit_days + 1 if options.limit_days <= 500 else 501
            for i in xrange(1, stop):
                day = today - timedelta(days = i)
                relpaths.append("bar-%s/" % day.strftime("%y-%m%d"))
            
            for relpath in relpaths:
                params.update({"thread": "link:http://hookii.org/%s" % relpath, "include": "open", "limit": 1, "forum": config["forum"]})
                logger.info("GET threads/list (%s)" % relpath)
                response = requests.get("%sthreads/list.json" % api_url, params=params)
                response.raise_for_status()
                data = response.json()
                if len(data.get("response", [])) == 0:
                    continue
                tid = data["response"][0]["id"]
                logger.info("POST close http://hookii.org/%s thread=%s" % (relpath, tid))
                params.pop("include", None)
                params.pop("limit", None)
                params.pop("forum", None)
                params.update({"thread": "%s" % tid})
                response = requests.post("%sthreads/close.json" % api_url, params=params)
                if response.ok:
                    closed += 1
                else:
                    logger.error("Failed with status code %d" % response.status_code)
                    error += 1
            logger.info("Closed %d discussions. Errors=%d" % (closed, error))
          

        logger.info("Done")
            
    except Exception as ex:
        logger.exception(ex)
    
    
    exit(0)