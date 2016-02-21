import re

import praw

from .constants import REDDIT_TEMPLATE

class RedditBotCore(object):

    USER_AGENT = "Web:NBAShotcharts:0.1.0 (by /u/smallfundamentals)"
    SUBREDDIT = "nba"
    TEST_SUBREDDIT = "anarmadillo"

    def __init__(self):
        self.r = praw.Reddit(self.USER_AGENT)
        self.r.login(disable_warning=True)
        self.subreddit = self.r.get_subreddit(self.TEST_SUBREDDIT)

    def _get_linked_comment_text(self, result_list):
        reply_links = []
        for result in result_list:
            query_string, url = result
            link = REDDIT_TEMPLATE.LINK_TEMPLATE.format(
                query_string=query_string,
                url=url
            )
            reply_links.append(link)
        return ''.join(reply_links)

    def _get_instructions(self):
        return REDDIT_TEMPLATE.USAGE_TEMPLATE

    def _get_signature(self):
        return REDDIT_TEMPLATE.SIGNATURE_TEMPLATE

    def get_query_from_comment(self, comment, pattern):
        match_list = re.findall(pattern, comment)
        return match_list

    def reply(self, comment, result_list):
        linked_comment = self._get_linked_comment_text(result_list)
        instructions = self._get_instructions()
        signature = self._get_signature()
        reply_body = REDDIT_TEMPLATE.COMMENT_TEMPLATE.format(
            linked_comment=linked_comment,
            instructions=instructions,
            signature=signature
        )
        try:
            print "Replying to comment %d..." % comment.id
            comment.reply(reply_body)
            print " success!\n"
        except praw.errors.ClientException as e:
            print " ClientException!\n"
            # Log this
            pass
        except praw.errors.APIException as e:
            print " APIException!\n"
            # Log this
            pass
