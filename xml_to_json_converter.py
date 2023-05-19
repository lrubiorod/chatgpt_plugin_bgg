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
                    "username": player.attrib["username"],
                    "userid": player.attrib["userid"],
                    "name": player.attrib["name"],
                    "score": player.attrib["score"],
                    "win": player.attrib["win"]
                })

        plays.append({
            "id": play.attrib["id"],
            "date": play.attrib["date"],
            "location": play.attrib["location"],
            "item": {
                "name": item.attrib["name"],
                "objecttype": item.attrib["objecttype"],
                "objectid": item.attrib["objectid"],
            },
            "players": players,
        })

    return {
        "username": root.attrib["username"],
        "userid": root.attrib["userid"],
        "total": root.attrib["total"],
        "page": root.attrib["page"],
        "plays": plays
    }
