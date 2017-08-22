# disqus-utils
Disqus utilities for managing your Disqus account.
Currently available functionalities:
* archive posts of a Disqus user
* generate HTML page with comments from downloaded data
* remove comments without likes

Pre-requisites:
* Register a new application here: https://disqus.com/api/applications/, specify domain disqus.com
* Verify that API Key, API Secret and Access Token are available

Requirements:
* python 2.7.*
* python-requests 
    * sudo pip install requests

```
usage: disqus_manager.py [-h] --disqus-secret DISQUS_SECRET --disqus-public
                         DISQUS_PUBLIC --disqus-token DISQUS_TOKEN
                         [--user USER] --working-dir WORKING_DIR [--archive]
                         [--limit-days LIMIT_DAYS] [--start START]
                         [--delete-unrated] [--chunk-size CHUNK_SIZE]
                         [--generate-html GENERATE_HTML] [--log LOG]

Maintenance tasks for a disqus account.

optional arguments:
  -h, --help            show this help message and exit
  --disqus-secret DISQUS_SECRET
                        Disqus API secret key
  --disqus-public DISQUS_PUBLIC
                        Disqus API public key
  --disqus-token DISQUS_TOKEN
                        Disqus user access token
  --user USER           Disqus user ID
  --working-dir WORKING_DIR
                        Working directory
  --archive             Downloads and archive all the comments of the given
                        user
  --limit-days LIMIT_DAYS
                        Limit the download to the specified number of days in
                        the past
  --start START         Download comments from this date and time backwards,
                        format must be 2016-12-10T15:24:24
  --delete-unrated      Deletes all the archived comment that do not have an
                        upvote
  --chunk-size CHUNK_SIZE
                        Split the post IDs to delete in chunks of the
                        specified size
  --generate-html GENERATE_HTML
                        Path to the HTML file containing the extracted
                        comments
  --log LOG             Path to the log file



=> Download 7 days of past comments starting from now
> python disqus_manager.py --disqus-secret <API Secret> --disqus-public <API Key> --disqus-token <Access Token> --user <User ID> --working-dir <Path to the working directory> --archive --limit-days 7

=> Download 2 days of past comments starting from 2016-12-09T15:24:24
> python disqus_manager.py --disqus-secret <API Secret> --disqus-public <API Key> --disqus-token <Access Token> --user <User ID> --working-dir <Path to the working directory> --archive --limit-days 7 --start 2016-12-09T15:24:24

=> Generate HTML file
> python disqus_manager.py --disqus-secret <API Secret> --disqus-public <API Key> --disqus-token <Access Token> --user <User ID> --working-dir <Path to the working directory> --generate-html <Path to the HTML ouput file>

```


NOTES: Please keep in mind that disqus allows only 1000 requests in a short time frame. You can check the status of the requests counter in your application page.
Counter resets to 0 every hour

