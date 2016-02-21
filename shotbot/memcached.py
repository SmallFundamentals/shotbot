from datetime import date

import memcache

memcached_client = memcache.Client(['127.0.0.1:11211'], debug=0)

def generate_key(player_id):
	if player_id:
		key = "[{date}]{player_id}".format(
			date=date.today().isoformat(),
			player_id=player_id
		)
		return key
