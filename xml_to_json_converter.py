from xml.etree import ElementTree


def hot_converter(xml_data, limit):
    root = ElementTree.fromstring(xml_data)
    items = []
    for idx, item in enumerate(root.findall('item')):
        if limit and idx == limit:
            break
        items.append({
            "id": item.get('id'),
            "rank": item.get('rank'),
            "thumbnail": item.find('thumbnail').get('value'),
            "name": item.find('name').get('value'),
            "yearpublished": item.find('yearpublished').get('value')
        })
    return {"items": items}


def user_converter(xml_data):
    root = ElementTree.fromstring(xml_data)
    user = root
    buddies_list = []
    for buddy in user.find('buddies'):
        buddies_list.append({
            "id": buddy.get('id'),
            "name": buddy.get('name'),
        })
    user_json = {
        "user": {
            "id": user.get('id'),
            "name": user.get('name'),
            "first_name": user.find('firstname').get('value'),
            "last_name": user.find('lastname').get('value'),
            "avatar_link": user.find('avatarlink').get('value'),
            "year_registered": user.find('yearregistered').get('value'),
            "last_login": user.find('lastlogin').get('value'),
            "state_or_province": user.find('stateorprovince').get('value'),
            "country": user.find('country').get('value'),
            "trade_rating": user.find('traderating').get('value'),
            "buddies": {
                "total": user.find('buddies').get('total'),
                "page": user.find('buddies').get('page'),
                "buddy": buddies_list
            }
        }
    }
    return user_json


def play_converter(xml_data, limit, with_players):
    root = ElementTree.fromstring(xml_data)
    plays = []

    for idx, play in enumerate(root.findall('play')):
        if limit and idx == limit:
            break
        item = play.find('item')
        players = []

        if with_players:
            for player in play.findall('players/player'):
                players.append({
                    "username": player.get("username"),
                    "userid": player.get("userid"),
                    "name": player.get("name"),
                    "score": player.get("score"),
                    "win": player.get("win")
                })

        plays.append({
            "id": play.get("id"),
            "date": play.get("date"),
            "location": play.get("location"),
            "item": {
                "name": item.get("name"),
                "objecttype": item.get("objecttype"),
                "objectid": item.get("objectid"),
            },
            "players": players if with_players else None,
        })

    return {
        "username": root.get("username"),
        "userid": root.get("userid"),
        "total": root.get("total"),
        "page": root.get("page"),
        "plays": plays
    }
