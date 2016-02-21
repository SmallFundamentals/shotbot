from datetime import date

import memcache

memcached_client = memcache.Client(['127.0.0.1:11211'], debug=0)

def generate_key_for_player_id_chart_kind(player_id, chart_kind):
	if player_id:
		key = "[{date}]-{player_id}-{chart_kind}".format(
			date=date.today().isoformat(),
			player_id=player_id,
			chart_kind=chart_kind
		)
		return key
