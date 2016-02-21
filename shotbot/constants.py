from richenum import enum


CHART_KIND = enum(
	SCATTER="scatter",
	KDE="kde",
	HEX="hex"
)

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

SHOT_COLOR = enum(
	MADE="#F44336",
	MISSED="#8BC34A"
)

FILE_EXTENSION = ".png"
ALL_PLAYER_NAMES_KEY = "all-player-names"
MAX_QUERY_SIZE_PER_COMMENT = 10
HEX_GRID_SIZE = 40
