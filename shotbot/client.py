from datetime import date
import difflib
from os import makedirs
import sys
import yaml

from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError
import praw
import matplotlib.pyplot as pyplot
import nbashots as nba

from .constants import ALL_PLAYER_NAMES_KEY, \
    CHART_KIND, \
    FILE_EXTENSION, \
    SHOT_COLOR
from .memcached import memcached_client, generate_key
from .reddit_bot_core import RedditBotCore


class ShotBot(RedditBotCore):

    def __init__(self):
        with open('config.yaml', 'r') as f:
            self.config = yaml.load(f)

        RedditBotCore.__init__(self)
        self.all_player_names = None
        self.memcached_client = memcached_client
        self._initialize_imgur_client()
        self._initialize_matplotlib()

    def _initialize_imgur_client(self):
        self.imgur_client = ImgurClient(self.config['imgur']['client_id'],
                                        self.config['imgur']['client_secret'],
                                        self.config['imgur']['access_token'],
                                        self.config['imgur']['refresh_token'])

    def _initialize_matplotlib(self):
        pyplot.rcParams['figure.figsize'] = (12, 11)
        pyplot.rc('font', family='sans-serif')
        pyplot.rc('font', serif='Helvetica Neue')
        pyplot.rc('text', usetex='false')

    def _get_all_player_names(self):
        """
        Memoized function. Returns a list of player names in canonical form,
        i.e. in the format used by stats.nba.com

        Returns:
        List<string>, e.g. [u'Curry, Stephen']
        """
        all_player_names = self.memcached_client.get(ALL_PLAYER_NAMES_KEY)
        if not all_player_names:
            all_player_names = \
                [p for p in nba.get_all_player_ids("shots").DISPLAY_LAST_COMMA_FIRST]
            self.memcached_client.set(ALL_PLAYER_NAMES_KEY, all_player_names)
        return all_player_names

    def _get_chart_title(self, player_name, chart_kind):
        chart_title = "[%s] %s - %s" % (date.today().isoformat(), player_name, chart_kind)
        return chart_title

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

    def _save_plot(self, filename):
        try:
            makedirs(self.config['save_path'])
        except OSError as e:
            pass

        file_path = self.config['save_path'] + filename
        print "Saving shotchart - %s" % file_path + "...",
        pyplot.savefig(file_path, bbox_inches='tight')
        pyplot.clf()
        print "success!"
        return file_path

    def _save_scatter_chart(self, player_shots_df, player_name):
        """
        Given a DataFrame object, save a scatter shot chart and return its path
        """
        if player_shots_df.size > 0:
            chart_title = self._get_chart_title(player_name, CHART_KIND.SCATTER)
            filename = self._get_filename_from_player_name(player_name, CHART_KIND.SCATTER)
            player_shots_df_fg_made = player_shots_df.query('SHOT_MADE_FLAG == 1')
            player_shots_df_fg_missed = player_shots_df.query('SHOT_MADE_FLAG == 0')
            nba.shot_chart(player_shots_df_fg_missed.LOC_X,
                           player_shots_df_fg_missed.LOC_Y,
                           title=chart_title,
                           color=SHOT_COLOR.MISSED,
                           flip_court=True)
            nba.shot_chart(player_shots_df_fg_made.LOC_X,
                           player_shots_df_fg_made.LOC_Y,
                           title=chart_title,
                           color=SHOT_COLOR.MADE,
                           flip_court=True)
            return self._save_plot(filename)
        print "No data..."
        return None

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

    def start(self):
        # while True:
        for comment in self.subreddit.get_comments():
            if not self.memcached_client.get(comment.id):
                query_string = self._try_get_shotchart_request(comment.body)
                if query_string is not None:
                    print "Found request: '%s'" % query_string
                    player_id, player_name = self._try_get_player_id(query_string)
                    if player_id:
                        print "Best match found: %s - %d" % (player_name, player_id)
                        print "Searching memcached..."
                        shotchart_url_key = generate_key(player_id)
                        result_url = self.memcached_client.get(shotchart_url_key)
                        if result_url is None:
                            print "No cached url..."
                            filepath = self.generate_for_player(player_id, player_name)
                            result_url = self.upload(filepath)
                        else:
                            print "Found cached url - %s: %s" % (shotchart_url_key, result_url)
                        # Only reply if url is available, generation or imgur upload could fail
                        if result_url:
                            # Store imgur url for reuse
                            self.memcached_client.set(shotchart_url_key, result_url)
                            self.reply(comment, result_url, query_string)
                            # Store comment id to prevent duplicate response
                            self.memcached_client.set(comment.id, True)
                    else:
                        print "No ID match for request.\n"
            else:
                print "Comment with ID %s already processed.\n" % comment.id
        # Sleep for a minute

    def generate(self, query_string):
        player_id, player_name = self._try_get_player_id(query_string)
        filepath = self.generate_for_player(player_id, player_name)
        return filepath, player_id, player_name

    def generate_for_player(self, player_id, player_name):
        if player_id is not None:
            player_shots_df = nba.Shots(player_id).get_shots()
            filepath = self._save_scatter_chart(player_shots_df, player_name)
            return filepath
        return None

    def upload(self, path):
        if path:
            try:
                print "Uploading...",
                data = self.imgur_client.upload_from_path(path, anon=True)
                print "success!"
                print data
                return data['link']
            except ImgurClientError as e:
                print "failed!"
                print(e.error_message)
                print(e.status_code)
        return None
