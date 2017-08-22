# -*- coding: utf-8 -*-
'''
Created on Dec 9, 2016

@author: s1m0n4
@copyright: 2016 s1m0n4
'''
import re
import os
import json
import utils
import StringIO

class Generator(object):
    '''
    Generates HTML formatted string containing all the comments
    '''

    def __init__(self, comments_dir, output_file, logger):
        '''
        Constructor
        '''
        self.comments_dir = comments_dir
        self.output_file = output_file
        self.logger = logger
        directory = os.path.dirname(output_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.author = None
        self.icon = None

    def generate(self):
        cfiles = filter(lambda x: x.endswith(".json"), os.listdir(self.comments_dir))
        sfiles = sorted(cfiles, key=lambda x: int(x.split('.')[1]))
        self.logger.info("processing files\n%s" % '\n'.join(cfile for cfile in sfiles))
        i = 0
        j = 0
        for cfile in sfiles:
            i += 1
            j = 0
            self.logger.debug("read %s" % os.path.join(self.comments_dir, cfile))
            text = utils.read_file(os.path.join(self.comments_dir, cfile))
            data = json.loads(text)
            str_buffer = StringIO.StringIO()
            try:
                for comment in data:
                    j += 1
                    if not self.author:
                        self.author = comment["author"]["username"]
                        self.logger.debug("Author: %s" % self.author)
                        self.icon = comment["author"]["avatar"]["permalink"]
                        self.logger.debug("Icon: %s" % self.author)
                        utils.write_file(self.output_file, self.__head__())

                    contents = self.__format_comment__(comment.get("createdAt", ""),
                                                       comment["id"],
                                                       comment.get("message", ""),
                                                       comment.get("thread", {}).get("link", ""),
                                                       comment.get("thread", {}).get("title", ""),
                                                       comment.get("likes", 0),
                                                       comment.get("dislikes", 0))
                    str_buffer.write(contents.encode('utf-8').strip())
                    
                    self.logger.info("comment %s [%d/%d] in file [%d/%d]" % (comment["id"], j, len(data), i, len(cfiles)))
                utils.write_file(self.output_file, str_buffer.getvalue(), 'a')
                str_buffer.close()
            finally:
                if str_buffer:
                    str_buffer.close()
        utils.write_file(self.output_file, self.__foot__(), 'a')

    def __head__(self) :
        return u'''<html>
    <head>
    <title>Commenti di %s</title>
     <meta name="generator" content="comments">
     <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
     <meta name="robots" content="index, follow">
     <meta name="keywords" content="commenti, liberi, lettori, commenti giornali online, community">
     <meta name="description" content="%s">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="html5.css">
    <!-- All in one Favicon 4.3 -->
    <link rel="shortcut icon" href="%s" />
    <link rel="icon" href="%s" type="image/gif"/>
    <link rel="apple-touch-icon" href="%s" />
    <style>
     .col1 { width: 50%%; display: inline-block; color:#444; }
     .col2 { width: 20%%; display: inline-block; color:#444; }
     .col3 { width: 5%%; text-align: right; display: inline-block; color:#444; }
    </style>
    
    </head>
    <body>
    ''' % (self.author, self.author, self.icon, self.icon, self.icon)
    
    def __foot__(self):
        return '</body></html>'

    def __format_comment__(self, comment_date, comment_id, comment_html, thread_link, thread_title, likes, dislikes) :
        w = 4
        result = '\n<div style="margin-left:%dpx; margin-right:-%dx; width:80%%;">' % (w, w)
        url_tag =  "<a href='%s#comment-%s'>" % (thread_link, comment_id)

        result += "<h4 style='margin-bottom:0.1em;'>%s %s +%d -%d</a></h4>" % (url_tag, thread_title, likes, dislikes)
        result += "<p style='margin-top:0.1em; font-size:60%%'>%s</p>" % comment_date
    
        result += comment_html
        result += "<hr></div>\n"
        return result