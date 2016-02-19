from datetime import date
import difflib
import sys
import yaml

from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError
import matplotlib.pyplot as pyplot
import nbashots as nba

from .constants import CHART_KIND, FILE_EXTENSION
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
        self.all_player_names = None
        with open('config.yaml', 'r') as f:
            self.config = yaml.load(f)
        self._initialize_imgur_client()
        pyplot.rcParams['figure.figsize'] = (12, 11)

    def _initialize_imgur_client(self):
        self.imgur_client = ImgurClient(self.config['imgur']['client_id'],
                                        self.config['imgur']['client_secret'],
                                        self.config['imgur']['access_token'],
                                        self.config['imgur']['refresh_token'])

    def _get_all_player_names(self):
        """
        Memoized function. Returns a list of player names in canonical form,
        i.e. in the format used by stats.nba.com

        Returns:
        List<string>, e.g. [u'Curry, Stephen']
        """
        if not self.all_player_names:
            self.all_player_names = [p for p in
                nba.get_all_player_ids("shots").DISPLAY_LAST_COMMA_FIRST]
        return self.all_player_names

    def _get_filename_from_player_name(self, player_name, chart_kind):
        """
        Given a player's name in canonical form (e.g. "Curry, Stephen"), convert
        it into a file name

        Returns:
        A filename, e.g. "[2016-02-15]-steph-curry-scatter.png"
        """
        name_part = "-".join([part.strip() for part in player_name.lower().split(",")][::-1])
        date_part = "[%s]" % date.today().isoformat()
        return "-".join([date_part, name_part, chart_kind]) + FILE_EXTENSION

    def _try_get_player_id(self, query_string):
        """
        Given a query string, convert it to its expected format and find the
        corresponding player id, if any.

        Arguments:
        query_string -- string, player name expected, but not guaranteed to be
            in "First Last" format

        Returns:
        Extracted query string, or None, with closest matching canonical name
        """
        try:
            first_name, last_name = query_string.split(" ")
            expected_name = "%s, %s" % (last_name, first_name)
            player_name = difflib.get_close_matches(expected_name,
                                                    self._get_all_player_names())[0]
            return nba.get_player_id(player_name)[0], player_name
        except ValueError:
            return None, None
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

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

    def _save_scatter_chart(self, player_shots_df, player_name):
        """
        Given a DataFrame object, save a scatter shot chart and return its path
        """
        chart_title = "%s 2015-16 Season" % player_name
        filename = self._get_filename_from_player_name(player_name, CHART_KIND.SCATTER)
        nba.shot_chart(player_shots_df.LOC_X, player_shots_df.LOC_Y, title=chart_title)
        print "Saving shotchart - %s" % filename,
        pyplot.savefig(filename, bbox_inches='tight')
        pyplot.clf()
        print "...success!"
        return filename

    def start(self):
        # while True:
        for comment in self.subreddit.get_comments():
            query_string = self._try_get_shotchart_request(comment.body)
            if query_string is not None:
                filename = self.generate(query_string)
                result = self.upload(filename)
                print result
                # Comment

    def generate(self, query_string):
        player_id, player_name = self._try_get_player_id(query_string)
        if player_id is not None:
            player_shots_df = nba.Shots(player_id).get_shots()
            player_shots_df_fg_made = player_shots_df.query('SHOT_MADE_FLAG == 1')
            player_shots_df_fg_missed = player_shots_df.query('SHOT_MADE_FLAG == 0')
            return self._save_scatter_chart(player_shots_df, player_name)
        return None

    def upload(self, path):
        try:
            data = self.imgur_client.upload_from_path(path, anon=True)
            print data
            return data['link']
        except ImgurClientError as e:
            print(e.error_message)
            print(e.status_code)
