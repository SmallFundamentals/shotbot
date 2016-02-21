from richenum import enum


CHART_KIND = enum(
	SCATTER="scatter",
	KDE="kde",
	HEX="hex"
)

SHOT_COLOR = enum(
	MADE="#F44336",
	MISSED="#8BC34A"
)

FILE_EXTENSION = ".png"
ALL_PLAYER_NAMES_KEY = "all-player-names"