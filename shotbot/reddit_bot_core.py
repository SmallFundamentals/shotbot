import re

import praw

class RedditBotCore(object):

    USER_AGENT = "Web:NBAShotcharts:0.1.0 (by /u/smallfundamentals)"
    SUBREDDIT = "nba"
    TEST_SUBREDDIT = "anarmadillo"

    def __init__(self):
        self.r = praw.Reddit(self.USER_AGENT)
        self.r.login(disable_warning=True)
        self.subreddit = self.r.get_subreddit(self.TEST_SUBREDDIT)

    def get_query_from_comment(self, comment, pattern):
        match = re.search(pattern, comment)
        return match

    def reply(self, comment, url, query_string):
        reply_text = ("**[{0}]({1})**\n\n---\n\n^^I ^^currently ^^only "
            "^^do ^^charts ^^for ^^the ^^current ^^season. ^^Use "
            "^^[[<first ^^name> ^^<last ^^name>]]\n\n^^Questions/"
            "Suggestions/Bugs? [^^Hit ^^me](https://www.reddit.com/message/"
            "compose/?to=shot-bot)").format(query_string, url)
        comment.reply(reply_text)
        # TODO: add comment to list of replied