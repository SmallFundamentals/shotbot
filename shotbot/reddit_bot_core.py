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