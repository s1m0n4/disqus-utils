# -*- coding: utf-8 -*-
#!/usr/bin/env python
'''
Created on Feb 14, 2018


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
import disqus_html
import utils
from Queue import PriorityQueue
import json


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Provides statistics on latest comments.")
    parser.add_argument("--disqus-secret", type=str, required=True, help="Disqus API secret key")
    parser.add_argument("--disqus-public", type=str, required=True, help="Disqus API public key")
    parser.add_argument("--working-dir", type=str, required=True, help="Working directory")
    parser.add_argument('--archive', action='store_true', help="Downloads and archive all the comments within the specified period")
    parser.add_argument('--limit-days', type=int, default=1, help="Limit the download to the specified number of days in the past")
    parser.add_argument("--start", type=str, help="Download comments from this date and time backwards, format must be 2016-12-10T15:24:24. Defaults to now.")
    parser.add_argument("--top", type=int, default=10, help="Specifies the number of most updated comments to link in the output")
    parser.add_argument("--forum", type=str, default="hookii", help="Specifies which forum to crawl for comments")
    parser.add_argument("--chunk-size", type=int, default=100, help="Split the post IDs to delete in chunks of the specified size")
    parser.add_argument("--generate-html", type=str, required=True, help="Path to the HTML file containing the extracted comments")
    parser.add_argument("--log", type=str, help="Path to the log file")
    parser.add_argument("--mailto", nargs="+", help="E-mail recipients for most-liked comments")
    parser.add_argument("--mailsmtp", type=str, help="The SMTP server to use")
    parser.add_argument("--mailuser", type=str, help="E-mail user for sending e-mails")
    parser.add_argument("--mailpwd", type=str, help="E-mail password for sending e-mails")
    
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

        params = {"api_key": options.disqus_public,
                  "api_secret": options.disqus_secret,
                  "forum": [options.forum],
                  "limit": 100,
                  "related": "thread"}

        
        params["end"] = datetime.strptime(options.start, "%Y-%m-%dT%H:%M:%S") if options.start else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            
        timelimit = datetime.now()
        timelimit -= timedelta(days = options.limit_days)
        params["start"] = timelimit.strftime("%Y-%m-%dT%H:%M:%S")
        logger.info("retrieve comments from %s until %s" % (params["start"], params["end"]))
        
        i = 0
        most_liked = PriorityQueue(maxsize = options.top)
        while hasnext:
            if error > 10:
                logger.error("reached max number of errors. abort")
                break
            i += 1
            try:
                logger.info("GET posts/list (%d)" % i)
                response = requests.get("%sposts/list" % api_url, params=params)
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
                
                logger.info("sort comments and fill most liked queue")
                sorted_comments = sorted(data["response"], key=lambda x: x["likes"], reverse=True)[0:options.top]
                if most_liked.empty():
                    for x in xrange(len(sorted_comments)):
                        most_liked.put((sorted_comments[x]["likes"], sorted_comments[x]))
                else:
                    for x in xrange(len(sorted_comments)):
                        last = most_liked.get()[1]
                        if sorted_comments[x]["likes"] > last["likes"]:
                            logger.info("popped comment with %d likes, inserted comment with %d likes" % (last["likes"], sorted_comments[x]["likes"], ))
                            most_liked.put((sorted_comments[x]["likes"], sorted_comments[x]))
                        else:
                            most_liked.put((last["likes"], last))
                
                
                if options.archive:
                    logger.debug("write")
                    utils.write_file(os.path.join(options.working_dir, "%s.%s.%s.%d.json" % (options.forum, params["start"], params["end"], i)), json.dumps(data["response"]))
                
            except Exception as apiex:
                logger.exception(apiex)
                error +=1

        most_liked_list = []
        for x in xrange(options.top):
            most_liked_list.append(most_liked.get()[1])
        
        logger.info("generate HTML file %s" % options.generate_html)      
        generator = disqus_html.Generator(options.working_dir, options.generate_html, logger)
        generator.write_comments(list(reversed(most_liked_list)), add_footer=True)

        if options.mailto:
            logger.info("send e-mail to %s" % repr(options.mailto))
            text = "Attached you can find the %d most liked comments on %s that were posted from %s until %s" % (options.top, options.forum, params["start"], params["end"])
            utils.send_email("hookiibot@gmail.com",
                             options.mailto,
                             "%d most liked comments on %s" % (options.top, options.forum),
                             text,
                             options.mailsmtp,
                             [options.generate_html],
                             user = options.mailuser,
                             password = options.mailpwd)  
        
        logger.info("done")
            
    except Exception as ex:
        logger.exception(ex)
    
    exit(0)
    