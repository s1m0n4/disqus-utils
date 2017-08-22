# -*- coding: utf-8 -*-
'''
Created on Dec 2, 2016

@author: s1m0n4
@copyright: 2016 s1m0n4
'''
import argparse
import logging
import os
import sys
import requests
import json
import utils
from datetime import datetime, timedelta
import time
import disqus_html


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Maintenance tasks for a disqus account.")
    parser.add_argument("--disqus-secret", type=str, required=True, help="Disqus API secret key")
    parser.add_argument("--disqus-public", type=str, required=True, help="Disqus API public key")
    parser.add_argument("--disqus-token", type=str, required=True, help="Disqus user access token")
    parser.add_argument("--user", type=str, help="Disqus user ID")
    parser.add_argument("--working-dir", type=str, required=True, help="Working directory")
    parser.add_argument('--archive', action='store_true', help="Downloads and archive all the comments of the given user")
    parser.add_argument('--limit-days', type=int, default=-1, help="Limit the download to the specified number of days in the past")
    parser.add_argument("--start", type=str, help="Download comments  from this date and time backwards, format must be 2016-12-10T15:24:24")
    parser.add_argument("--delete-unrated", action="store_true", help="Deletes all the archived comment that do not have an upvote")
    parser.add_argument("--chunk-size", type=int, default=50, help="Split the post IDs to delete in chunks of the specified size")
    parser.add_argument("--generate-html", type=str, help="Path to the HTML file containing the extracted comments")
    parser.add_argument("--log", type=str, help="Path to the log file")
    
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
        hasnext = True
        error = 0
        timelimit = None
        
        if options.archive:
            if not options.user:
                logger.error("please provide argument --user")
                exit(1)
            params = {"user:username": options.user,
                      "api_key": options.disqus_public,
                      "api_secret": options.disqus_secret,
                      "access_token": options.disqus_token,
                      "limit": 100,
                      "related": "thread"}

            if options.start:
                params["since"] = datetime.strptime(options.start, "%Y-%m-%dT%H:%M:%S")
                
            if options.limit_days > 0:
                timelimit = datetime.now()
                timelimit -= timedelta(days = options.limit_days)
            
            logger.info("retrieve comments from %s until %s" % ("now " if not options.start else options.start, "infinity" if options.limit_days <=0 else timelimit.strftime("%Y-%m-%dT%H:%M:%S")))
                
            i = 0
            while hasnext:
                if error > 10:
                    logger.error("reached max number of errors. abort")
                    break
                i += 1
                try:
                    logger.info("users/listPosts.json (%d)" % i)
                    response = requests.get("%susers/listPosts.json" % api_url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    if data["cursor"]["hasNext"]:
                        logger.info("next=true [%s]" % data["cursor"]["next"])
                        params["cursor"] = data["cursor"]["next"]
                        hasnext = True
                    else:
                        logger.info("next=false")
                        params.pop("cursor", None)
                        hasnext = False
                    
                    if len(data.get("response", [])) == 0:
                        logger.debug("empty data in response. abort")
                        break
                    
                    if timelimit:
                        returned_time = datetime.strptime(data["response"][len(data["response"])-1]["createdAt"], "%Y-%m-%dT%H:%M:%S")
                        if returned_time < timelimit:
                            logger.info("reached time limit [%s], last comment date and time is %s" % (timelimit.strftime("%Y-%m-%dT%H:%M:%S"), data["response"][len(data["response"])-1]["createdAt"]))
                            hasnext = False
                    
                    logger.debug("write")
                    utils.write_file(os.path.join(options.working_dir, "%s.%d.json" % (options.user, i)), json.dumps(data["response"]))
                    
                except Exception as apiex:
                    logger.exception(apiex)
                    error +=1
        
        if options.generate_html:
            generator = disqus_html.Generator(options.working_dir, options.generate_html, logger)
            generator.generate()

        if options.delete_unrated:
            flist = os.listdir(options.working_dir)
            todelete = []
            for ofile in flist:
                opath = os.path.join(options.working_dir, ofile)
                if opath == options.log:
                    continue
                logger.debug("read %s" % opath)
                contents = utils.read_file(opath)
                posts = json.loads(contents)
                todelete.extend([x["id"] for x in posts if x["likes"] == 0])
            logger.info("%d posts will be deleted" % len(todelete))
            params = {"api_key": options.disqus_public,
                      "api_secret": options.disqus_secret,
                      "access_token": options.disqus_token}
            for j in xrange(0, len(todelete), options.chunk_size):
                try:
                    failed = []
                    params["post"] = todelete[j : j + options.chunk_size]
                    logger.info("delete posts %s" % repr( params["post"]))
                    response = requests.post("%sposts/remove.json" % api_url, params=params)
                    response.raise_for_status()
                    resdata = response.json()
                    logger.debug("OK" if resdata["code"] == 0 else "NOK")
                    if len(resdata.get("response", [])) < len(params["post"]):
                        logger.warning("some posts could not be deleted:")
                        logger.debug(json.dumps(resdata.get("response", [])))
                except Exception as apiex:
                    logger.exception(apiex)
            
        logger.info("done")
            
    except Exception as ex:
        logger.exception(ex)
    
    exit(0)
    
    