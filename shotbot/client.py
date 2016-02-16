import difflib

import matplotlib.pyplot as pyplot
import nbashots as nba

from .reddit_bot_core import RedditBotCore

class ShotBot(RedditBotCore):

	# Create our dictionaries
	# This dict provides the color indicating missed or made shots
	colormap = {
		0: 'tomato',
		1: '#1f77b4'
	}

	def __init__(self):
		 RedditBotCore.__init__(self)
		 self.start()
		 self.all_player_names = None

	def _get_all_player_names(self):
		"""
		Memoized function. Returns a list of player names, in the format
		used by stats.nba.com

	    Returns:
	    List<string>, e.g. [u'Curry, Stephen']
	    """
		if not self.all_player_names:
			self.all_player_names = [p for p in
				nba.get_all_player_ids("shots").DISPLAY_LAST_COMMA_FIRST]
		return self.all_player_names

	def _try_get_shotchart_request(self, comment):
		"""
		Given a comment, look for the expected regex pattern and return the
		query, if any.

		Arguments:
		comment -- string, Reddit comment body

	    Returns:
	    Extracted query string, or None
	    """
		match = self.get_query_from_comment(comment, r"\[\[(.*?)\]\]")
		return match and match.group(1)

	def _try_get_player_id(self, query_string):
		"""
		Given a query string, convert it to its expected format and find the
		corresponding player id, if any.

		Arguments:
		query_string -- string, player name expected, but not guaranteed to be
			in "First Last" format

	    Returns:
	    Extracted query string, or None
	    """
		try:
			first_name, last_name = query_string.split(" ")
			expected_name = "%s, %s" % last_name, first_name
			player_name = difflib.get_close_matches(expected_name,
													self._get_all_player_names())
			return nba.get_player_id(player_name)[0]
		except ValueError:
			return None
		except:
		    print "Unexpected error:", sys.exc_info()[0]
		    raise

	def start(self):
		# while True:
		for comment in self.subreddit.get_comments():
			query_string = self._try_get_shotchart_request(comment.body)
			if query_string is not None:
				player_id = self._try_get_player_id(query_string)
				if player_id is not None:
					player_shots_df = nba.Shots(player_id).get_shots()
					# Draw chart
					# Upload to Imgur
					# Comment
				else:

