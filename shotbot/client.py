from datetime import date
import difflib
from os import makedirs
import sys
import time
import yaml

from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError
import praw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pyplot
import nbashots as nba

from .constants import ALL_PLAYER_NAMES_KEY, \
    CHART_KIND, \
    FILE_EXTENSION, \
    HEX_GRID_SIZE, \
    MAX_QUERY_SIZE_PER_COMMENT, \
    REGEX, \
    SHOT_COLOR, \
    SLEEP_TIME_SECONDS
from .memcached import memcached_client, generate_key_for_player_id_chart_kind
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
        self.cmap=pyplot.cm.YlOrRd

    def _format_name(self, player_name):
        """
        Given a string representation of a player's name
        in the form "<last name>, <first name>", return it in
        its normal form, i.e. "<first name> <last name>"

        Returns:
        Formatted name
        """
        return " ".join(player_name.split(", ")[::-1])

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
        chart_title = "[%s] %s - %s" \
            % (date.today().isoformat(), player_name, chart_kind)
        return chart_title

    def _get_filename_from_player_name(self, player_name, chart_kind):
        """
        Given a player's name in canonical form (e.g. "Curry, Stephen"), convert
        it into a file name

        Returns:
        A filename, e.g. "[2016-02-15]-steph-curry-scatter.png"
        """
        name_part = "-".join([part.strip() \
            for part in player_name.lower().split(",")][::-1])
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

    def _create_chart(self, player_shots_df, player_name, chart_kind):
        if chart_kind == CHART_KIND.SCATTER:
            return self._create_and_save_scatter_chart(player_shots_df, player_name)
        elif chart_kind == CHART_KIND.KDE:
            # TODO: Implement
            return None
        elif chart_kind == CHART_KIND.HEX:
            return self._create_and_save_hex_chart(player_shots_df, player_name)
        else:
            raise Exception("Unexpected chart kind: %s" % chart_kind)

    def _create_and_save_scatter_chart(self, player_shots_df, player_name):
        """
        Given a DataFrame object, save a scatter shot chart and return its path
        """
        if player_shots_df.SHOT_MADE_FLAG.count() > 0:
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

    def _create_and_save_hex_chart(self, player_shots_df, player_name):
        """
        Given a DataFrame object, save a hex shot chart and return its path
        """
        if player_shots_df.SHOT_MADE_FLAG.count() > 0:
            chart_title = self._get_chart_title(player_name, CHART_KIND.HEX)
            filename = self._get_filename_from_player_name(player_name, CHART_KIND.HEX)
            nba.shot_chart(player_shots_df.LOC_X,
                           player_shots_df.LOC_Y,
                           C=player_shots_df.SHOT_MADE_FLAG,
                           title=chart_title,
                           kind=CHART_KIND.HEX,
                           cmap=self.cmap,
                           gridsize=HEX_GRID_SIZE,
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
            closest_matches = difflib.get_close_matches(expected_name,
                                                        self._get_all_player_names())
            if closest_matches:
                player_name = closest_matches[0]
                return nba.get_player_id(player_name)[0], player_name
            return None, None
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
        match_list = self.get_query_from_comment(comment, REGEX.PLAYER_QUERY_PATTERN)
        chart_kind = self.get_query_from_comment(comment, REGEX.CHART_KIND_PATTERN)
        # chart_kind[0] = (<T or t>, <chart type>). Don't care about first element
        # TODO: kinda crappy, see if there's a better way
        chart_kind = chart_kind[0][1] if len(chart_kind) > 0 else CHART_KIND.SCATTER
        return match_list, chart_kind.lower()

    def start(self):
        while True:
            print "Iteration begin.\n ----- "
            for comment in self.subreddit.get_comments():
                if not self.memcached_client.get(comment.id):
                    query_list, chart_kind = self._try_get_shotchart_request(comment.body)
                    result_list = []
                    for i in xrange(min(len(query_list), MAX_QUERY_SIZE_PER_COMMENT)):
                        query_string = query_list[i]
                        if query_string is not None:
                            print "REQUEST FOUND: '%s'" % query_string
                            player_id, player_name = self._try_get_player_id(query_string)
                            if player_id:
                                print "Best match found: %s - %d" % (player_name, player_id)
                                print "Searching memcached...",
                                shotchart_url_key = generate_key_for_player_id_chart_kind(player_id, chart_kind)
                                result_url = self.memcached_client.get(shotchart_url_key)
                                if result_url is None:
                                    print "no cached url..."
                                    filepath = self.generate_for_player(player_id, player_name, chart_kind)
                                    result_url = self.upload(filepath)
                                else:
                                    print "found cached url: %s: %s" % (shotchart_url_key, result_url)
                                # Only reply if url is available, generation or imgur upload could fail
                                if result_url:
                                    # Store imgur url for reuse
                                    self.memcached_client.set(shotchart_url_key, result_url)
                                    result_list.append((self._format_name(player_name), result_url))
                            else:
                                print "No ID match for request.\n"
                    # Don't reply if there's no result! Duh
                    if result_list:
                        self.reply(comment, result_list)
                    # Store comment id to prevent duplicate response
                    self.memcached_client.set(comment.id, True)
                else:
                    print "Comment with ID %s already processed.\n" % comment.id
            print "Iteration complete. Sleeping...\n ----- \n"
            time.sleep(SLEEP_TIME_SECONDS)

    def generate(self, query_string, chart_kind=CHART_KIND.SCATTER):
        player_id, player_name = self._try_get_player_id(query_string)
        filepath = self.generate_for_player(player_id, player_name, chart_kind)
        return filepath, player_id, player_name

    def generate_for_player(self, player_id, player_name,
                            chart_kind=CHART_KIND.SCATTER):
        if player_id is not None:
            # Errors out on Ubuntu
            try:
                player_shots_df = nba.Shots(player_id).get_shots()
                filepath = self._create_chart(player_shots_df, player_name, chart_kind)
                return filepath
            except ValueError:
                print "No data..."
        return None

    def upload(self, path):
        if path:
            try:
                print "Uploading...",
                data = self.imgur_client.upload_from_path(path, anon=True)
                print "success!"
                print "Imgur API response: ",
                print data
                return data['link']
            except ImgurClientError as e:
                print "failed!"
                print(e.error_message)
                print(e.status_code)
        return None
