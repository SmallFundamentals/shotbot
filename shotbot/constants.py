from richenum import enum

# Charts
CHART_KIND = enum(
	SCATTER="scatter",
	KDE="kde",
	HEX="hex"
)

SHOT_COLOR = enum(
	MADE="#F44336",
	MISSED="#8BC34A"
)

HEX_GRID_SIZE = 40

# Reddit I/O
BOT_NAME = "shot-bot"
ACCEPTED_VARIATIONS = "%s|%s|%s|%s|%s|%s|%s|%s|%s" % (
	CHART_KIND.SCATTER,
	CHART_KIND.KDE,
	CHART_KIND.HEX,
	CHART_KIND.SCATTER.upper(),
	CHART_KIND.KDE.upper(),
	CHART_KIND.HEX.upper(),
	CHART_KIND.SCATTER.capitalize(),
	CHART_KIND.KDE.capitalize(),
	CHART_KIND.HEX.capitalize()
)

REGEX = enum(
	PLAYER_QUERY_PATTERN = r"\[\[(\w+ \w+)\]\]",
	CHART_KIND_PATTERN = r"(T|t)ype=(%s)" % ACCEPTED_VARIATIONS
)

REDDIT_TEMPLATE = enum(
    COMMENT_TEMPLATE="{linked_comment}\n\n" \
        "---\n\n" \
        "{instructions}\n\n" \
        "---\n\n" \
        "{signature}",
    LINK_TEMPLATE="**[{query_string}]({url})**\n\n",
    USAGE_TEMPLATE="**^Usage:**\n\n" \
        "*^[[<first ^name> ^<last ^name>]]*\n\n"
        "^((optional: *type={scatter|hex}*, defaulted to scatter)^)\n\n"
        "^(Currently limited to 2015-16 season)\n\n",
    SIGNATURE_TEMPLATE="^Credits ^to ^/u/savvastj's " \
        "[^library](https://github.com/savvastj/nbashots)\n\n" \
        "^Questions/Suggestions/Bugs? [^Hit ^me](https://www.reddit.com/message/" \
        "compose/?to=%s)" % BOT_NAME
)

MAX_QUERY_SIZE_PER_COMMENT = 10

# Misc
FILE_EXTENSION = ".png"
ALL_PLAYER_NAMES_KEY = "all-player-names"


