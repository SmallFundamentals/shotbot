import re

import praw

class RedditBotCore(object):

    USER_AGENT = "Web:NBAShotcharts:0.1.0 (by /u/smallfundamentals)"
    SUBREDDIT = "nba"
    TEST_SUBREDDIT = "anarmadillo"
    LINK_TEMPLATE = "**[{0}]({1})**\n\n"

    def __init__(self):
        self.r = praw.Reddit(self.USER_AGENT)
        self.r.login(disable_warning=True)
        self.subreddit = self.r.get_subreddit(self.TEST_SUBREDDIT)

    def get_query_from_comment(self, comment, pattern):
        match_list = re.findall(pattern, comment)
        return match_list

    def reply(self, comment, result_list):
        reply_links = []
        for result in result_list:
            query_string, url = result
            link = self.LINK_TEMPLATE.format(query_string, url)
            reply_links.append(link)
        reply_body = ("{0}\n\n---\n\n^^I ^^currently ^^only "
            "^^do ^^charts ^^for ^^the ^^current ^^season. ^^Use "
            "^^[[<first ^^name> ^^<last ^^name>]]\n\n^^Questions/"
            "Suggestions/Bugs? [^^Hit ^^me](https://www.reddit.com/message/"
            "compose/?to=shot-bot)").format(''.join(reply_links))
        try:
            comment.reply(reply_body)
        except praw.errors.ClientException as e:
            # Log this
            pass
        except praw.errors.APIException as e:
            # Log this
            pass
