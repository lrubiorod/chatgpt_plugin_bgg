from xml.etree import ElementTree

PAGE_SIZE = 100
SEARCH_TAGS = {'boardgame', 'boardgameexpansion'}
LINK_TAGS = ['boardgamecategory', 'boardgamemechanic', 'boardgamefamily', 'boardgamedesigner', 'boardgameartist',
             'boardgamepublisher']
IGNORED_RATING_TAGS = {'stddev', 'median', 'trading', 'wanting', 'wishing', 'numcomments', 'numweights'}


def get_value(element, tag):
    found_element = element.find(tag)
    return found_element.get('value') if found_element is not None else None


def get_text(element, tag):
    found_element = element.find(tag)
    return found_element.text if found_element is not None else 'unknown'


def hot_converter(xml_data, limit):
    root = ElementTree.fromstring(xml_data)
    items = []
    for idx, item in enumerate(root.findall('item')):
        if limit and idx == limit:
            break
        items.append({
            "id": item.get('id'),
            "rank": item.get('rank'),
            "thumbnail": get_value(item, 'thumbnail'),
            "name": get_value(item, 'name'),
            "year_published": get_value(item, 'yearpublished')
        })
    return {"items": items}


def search_converter(xml_data):
    root = ElementTree.fromstring(xml_data)

    items_dict = {search_type: [] for search_type in SEARCH_TAGS}

    for item in root.findall('item'):
        item_type = item.get('type')
        if item_type in items_dict:
            item_info = {
                "id": item.get('id'),
                "name": get_value(item, 'name'),
                "year_published": get_value(item, 'yearpublished')
            }

            items_dict[item_type].append(item_info)

    return items_dict


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
        link_dict = {link_type: [] for link_type in LINK_TAGS}
        for link in item.findall('link'):
            link_type = link.get('type')
            if link_type in link_dict and (link_type != 'boardgamepublisher' or len(link_dict[link_type]) == 0):
                link_dict[link_type].append(link.get('value'))

        # Find ratings
        ratings_dict = {}
        for ratings in item.find('statistics').find('ratings'):
            if ratings.tag == 'ranks':
                ranks = [{k: v for k, v in rank.attrib.items()} for rank in ratings.findall('rank')]
                ratings_dict['ranks'] = ranks
            elif ratings.tag not in IGNORED_RATING_TAGS:
                ratings_dict[ratings.tag] = ratings.get('value')

        # Item dictionary
        item_dict = {
            "type": item.get('type'),
            "id": item.get('id'),
            "thumbnail": get_text(item, 'thumbnail'),
            "name": get_value(item, 'name[@type="primary"]'),
            "description": get_text(item, 'description'),
            "year_published": get_value(item, 'yearpublished'),
            "min_players": get_value(item, 'minplayers'),
            "max_players": get_value(item, 'maxplayers'),
            "playing_time": get_value(item, 'playingtime'),
            "min_play_time": get_value(item, 'minplaytime'),
            "max_play_time": get_value(item, 'maxplaytime'),
            "categories": link_dict['boardgamecategory'],
            "mechanics": link_dict['boardgamemechanic'],
            "families": link_dict['boardgamefamily'],
            "designers": link_dict['boardgamedesigner'],
            "artists": link_dict['boardgameartist'],
            "publishers": link_dict['boardgamepublisher'],
            "suggested_num_players": suggested_num_players,
            "suggested_player_age": suggested_player_age,
            "language_dependence": language_dependence,
            "ratings": ratings_dict
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
            "first_name": get_value(user, 'firstname'),
            "last_name": get_value(user, 'lastname'),
            "avatar_link": get_value(user, 'avatarlink'),
            "year_registered": get_value(user, 'yearregistered'),
            "last_login": get_value(user, 'lastlogin'),
            "state_or_province": get_value(user, 'stateorprovince'),
            "country": get_value(user, 'country'),
            "trade_rating": get_value(user, 'traderating'),
            "buddies": {
                "total": user.find('buddies').get('total'),
                "page": user.find('buddies').get('page'),
                "buddy": buddies_list
            }
        }
    }
    return user_json


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

        item_json = {
            "id": item.get("objectid"),
            "name": item.find('name').text,
            "year_published": get_text(item, 'yearpublished'),
            "pos": index + 1,
            "num_plays": get_text(item, 'numplays'),
        }
        items.append(item_json)

    return {
        "items": {
            "total_items": root.get("totalitems"),
            "pubdate": root.get("pubdate"),
            "item": items
        }
    }

