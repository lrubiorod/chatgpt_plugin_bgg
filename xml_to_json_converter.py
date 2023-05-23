from xml.etree import ElementTree

PAGE_SIZE = 100


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


def extract_result_votes(results):
    return {result.get('value'): int(result.get('numvotes')) for result in results.findall('result')}


def thing_converter(xml_data):
    root = ElementTree.fromstring(xml_data)
    items = []

    for item in root.findall('item'):
        # Find poll results
        suggested_num_players = {}
        suggested_player_age = None
        language_dependence = None
        for poll in item.findall('poll'):
            if poll.get('name') == 'suggested_numplayers':
                for results in poll.findall('results'):
                    num_players = results.get('numplayers')
                    result_votes = extract_result_votes(results)
                    suggested_num_players[num_players] = max(result_votes, key=result_votes.get)
            else:
                results = poll.find('results')
                result_votes = extract_result_votes(results)
                if poll.get('name') == 'suggested_playerage':
                    suggested_player_age = max(result_votes, key=result_votes.get)
                elif poll.get('name') == 'language_dependence':
                    language_dependence = max(result_votes, key=result_votes.get)

        # Find links
        link_dict = {link_type: [] for link_type in ['boardgamecategory', 'boardgamemechanic', 'boardgamefamily', 'boardgamedesigner', 'boardgameartist', 'boardgamepublisher']}
        for link in item.findall('link'):
            link_type = link.get('type')
            if link_type in link_dict and (link_type != 'boardgamepublisher' or len(link_dict[link_type]) == 0):
                link_dict[link_type].append(link.get('value'))

        # Find ratings
        ratings_dict = {}
        ignored_tags = {'stddev', 'median', 'trading', 'wanting', 'wishing', 'numcomments', 'numweights'}
        for ratings in item.find('statistics').find('ratings'):
            if ratings.tag == 'ranks':
                ranks = [{k: v for k, v in rank.attrib.items()} for rank in ratings.findall('rank')]
                ratings_dict['ranks'] = ranks
            elif ratings.tag not in ignored_tags:
                ratings_dict[ratings.tag] = ratings.get('value')

        # Item dictionary
        item_dict = {
            "type": item.get('type'),
            "id": item.get('id'),
            "thumbnail": item.find('thumbnail').text,
            "name": item.find('name[@type="primary"]').get('value'),
            "description": item.find('description').text,
            "year_published": item.find('yearpublished').get('value'),
            "min_players": item.find('minplayers').get('value'),
            "max_players": item.find('maxplayers').get('value'),
            "playing_time": item.find('playingtime').get('value'),
            "min_playtime": item.find('minplaytime').get('value'),
            "max_playtime": item.find('maxplaytime').get('value'),
            "min_age": item.find('minage').get('value'),
            "poll": {
                "suggested_num_players": suggested_num_players,
                "suggested_player_age": suggested_player_age,
                "language_dependence": language_dependence
            },
            "link": link_dict,
            "statistics": {
                "ratings": ratings_dict
            }
        }

        items.append(item_dict)

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


def collection_converter(xml_data, page):
    root = ElementTree.fromstring(xml_data)

    # Check if the XML root is a <message> element
    if root.tag == 'message':
        return {"message": root.text.strip()}

    # If not, continue with the previous conversion process
    items = []

    # Calculate start and end indices for pagination
    start_index = (page - 1) * PAGE_SIZE
    end_index = start_index + PAGE_SIZE

    for index, item in enumerate(root.findall('item')):
        # Check if this item is in the desired page range
        if index >= end_index:
            break
        if index < start_index:
            continue

        # Safely get the yearpublished text or default to 'unknown'
        year_published_elem = item.find('yearpublished')
        year_published = year_published_elem.text if year_published_elem is not None else 'unknown'

        # Safely get the numplays text or default to 'unknown'
        num_plays_elem = item.find('numplays')
        num_plays = num_plays_elem.text if num_plays_elem is not None else 'unknown'

        item_json = {
            "id": item.get("objectid"),
            "name": item.find('name').text,
            "year_published": year_published,
            "pos": index + 1,
            "num_plays": num_plays,
        }
        items.append(item_json)

    return {
        "items": {
            "total_items": root.get("totalitems"),
            "pubdate": root.get("pubdate"),
            "item": items
        }
    }

