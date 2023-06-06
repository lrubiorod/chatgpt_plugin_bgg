import requests
import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import date
from pydantic import BaseModel
from typing import Optional
from xml_to_json_converter import *

BGG_SUBDOMAINS_IDS = [5499, 5497, 4666, 5498, 4664, 5496, 4665, 4667]
BGG_SUBDOMAINS = ["familygames", "strategygames", "abstracts", "partygames", "wargames", "thematic", "childrensgames",
                  "cgs"]


# Define the FastAPI app
app = FastAPI()


# CORS configuration
def cors_config(app: FastAPI):
    origins = ["https://chat.openai.com"]  # Allow CORS requests from this origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


cors_config(app)


# HTTP request function
def get_url(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise HTTPException(status_code=response.status_code, detail=str(err))
    return response


# Parameters model for /plays/{username}
class PlayParameters(BaseModel):
    start: Optional[date] = None
    end: Optional[date] = None
    page: Optional[int] = None


class CollectionParameters(BaseModel):
    page: Optional[int] = 1
    id: Optional[str] = None
    minrating: Optional[str] = None
    rating: Optional[str] = None
    minbggrating: Optional[str] = None
    bggrating: Optional[str] = None
    minplays: Optional[int] = None
    maxplays: Optional[int] = None


class SearchParameters(BaseModel):
    page: Optional[int] = 1
    q: Optional[str] = None
    designerid: Optional[int] = None
    publisherid: Optional[int] = None
    yearpublished_min: Optional[int] = None
    yearpublished_max: Optional[int] = None
    minage_max: Optional[int] = None
    numvoters_min: Optional[int] = None
    numweights_min: Optional[int] = None
    minplayers_max: Optional[int] = None
    maxplayers_min: Optional[int] = None
    leastplaytime_min: Optional[int] = None
    playtime_max: Optional[int] = None
    avgrating_min: Optional[float] = None
    avgrating_max: Optional[float] = None
    avgweight_min: Optional[float] = None
    avgweight_max: Optional[float] = None
    searchuser: Optional[str] = None
    playerrangetype: Optional[str] = None
    subdomain: Optional[str] = None


allowed_status = ["own", "prevowned", "wishlist", "wanttoplay", "want", "wanttobuy", "preordered", "fortrade"]
MAX_RETRIES = 3


# Routes
@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
async def read_manifest():
    try:
        with open("./manifest.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/logo.png")
async def get_logo():
    try:
        return FileResponse("logo.png", media_type="image/png")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Logo not found")


@app.get(
    "/search/{query}",
    tags=["Games"],
    description=(
        "Retrieves board game data from BoardGameGeek based on the query. "
        "Set 'exact' to true for precise search, or false for a broader one. "
        "The response is a JSON object categorizing items by type, with details such "
        "as 'id', 'name', and 'year published'."
    ),
)
def search_query(query: str, exact: Optional[bool] = True):
    response = get_url(f"https://www.boardgamegeek.com/xmlapi2/search?query={query}&exact={int(exact)}")
    result = search_converter(response.content)

    if exact and result == {"boardgameexpansion": [], "boardgame": []}:
        response = get_url(f"https://www.boardgamegeek.com/xmlapi2/search?query={query}")
        result = search_converter(response.content)

    if not result:
        raise HTTPException(status_code=404, detail="Item not found")

    return result


@app.get(
    "/advanced_search",
    tags=["Search"],
    description=(
        "Generates a BoardGameGeek advanced search URL with filters such as designer, publisher, players, playtime, "
        "and ratings. Valid subdomains include 'familygames', 'strategygames', 'partygames', 'wargames', 'thematic', "
        "'childrensgames', 'cgs', and 'abstracts'."
    ),
)
def advanced_search_query(search_params: SearchParameters = Depends()):
    # Parameters dictionary
    params_dict = {
        "designerid": "include%5Bdesignerid%5D",
        "publisherid": "include%5Bpublisherid%5D",
        "yearpublished_min": "range%5Byearpublished%5D%5Bmin%5D",
        "yearpublished_max": "range%5Byearpublished%5D%5Bmax%5D",
        "minage_max": "range%5Bminage%5D%5Bmax%5D",
        "numvoters_min": "range%5Bnumvoters%5D%5Bmin%5D",
        "numweights_min": "range%5Bnumweights%5D%5Bmin%5D",
        "minplayers_max": "range%5Bminplayers%5D%5Bmax%5D",
        "maxplayers_min": "range%5Bmaxplayers%5D%5Bmin%5D",
        "playerrangetype": "playerrangetype",
        "leastplaytime_min": "range%5Bleastplaytime%5D%5Bmin%5D",
        "playtime_max": "range%5Bplaytime%5D%5Bmax%5D",
        "avgrating_min": "floatrange%5Bavgrating%5D%5Bmin%5D",
        "avgrating_max": "floatrange%5Bavgrating%5D%5Bmax%5D",
        "avgweight_min": "floatrange%5Bavgweight%5D%5Bmin%5D",
        "avgweight_max": "floatrange%5Bavgweight%5D%5Bmax%5D",
        "searchuser": "colfiltertype=owned&searchuser",
    }

    # Build the URL
    url = f"https://boardgamegeek.com/search/boardgame/page/{search_params.page}?sort=rank&advsearch=1&q={search_params.q if search_params.q else ''}"

    # Adding parameters to URL
    for param, url_param in params_dict.items():
        param_value = getattr(search_params, param, None)
        if param_value:
            url += f"&{url_param}={param_value}"

    if search_params.subdomain:
        subdomain = search_params.subdomain
        if subdomain not in BGG_SUBDOMAINS:
            raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of {BGG_SUBDOMAINS}")

        subdomain_index = BGG_SUBDOMAINS.index(subdomain)
        subdomain_id = BGG_SUBDOMAINS_IDS[subdomain_index]

        url += f"&familyids%5B0%5D={subdomain_id}"

    return {"url": url}


@app.get(
    "/user/{username}",
    tags=["Users"],
    description=(
            "This endpoint retrieves detailed information for a specific user from "
            "BoardGameGeek, including the user's name, state, country, and buddies. "
            "Replace 'username' in the URL with the target user's username."
    ),
)
def get_user_info(username: str):
    response = get_url(f"https://www.boardgamegeek.com/xmlapi2/user?name={username}&buddies=1")
    return user_converter(response.content)


@app.get(
    "/hot",
    tags=["Games"],
    description=(
        "Retrieve the 'hottest' board games from BoardGameGeek, "
        "based on visits and favorites. Use the 'limit' parameter to restrict "
        "the number of games. Each game's JSON includes: 'id', 'rank', 'thumbnail', "
        "'name', and 'yearpublished'."
    ),
)
def get_hot_games(limit: int = None):
    response = get_url("https://www.boardgamegeek.com/xmlapi2/hot?type=boardgame")
    return hot_converter(response.content, limit)


@app.get(
    "/thing/{game_id}",
    tags=["Games"],
    description=(
        "Retrieve detailed information and statistics for a specified game using its unique ID."
    ),
)
def get_game_info(game_id: int):
    response = get_url(f"https://www.boardgamegeek.com/xmlapi2/thing?id={game_id}&stats=1")
    return thing_converter(response.content)


@app.get(
    "/plays/{username}",
    tags=["Plays"],
    description=(
        "Generates a URL for user's board game plays from BoardGameGeek. "
        "Games can be sorted 'bydate' (returns game dates) or 'bygame' (returns number of plays). "
        "Optional 'start', 'end', and 'page' parameters narrow results and allow pagination."
    ),
)
def get_user_plays(username: str, sort_type: str = 'bydate', play_params: PlayParameters = Depends()):
    valid_sort_types = ["bygame", "bydate"]
    if sort_type not in valid_sort_types:
        raise HTTPException(status_code=400, detail=f"Invalid sort_type. Must be one of {valid_sort_types}")
    # Build the URL
    url = f"https://boardgamegeek.com/plays/{sort_type}/user/{username}"

    if play_params.start:
        url += f"/start/{play_params.start}"
    if play_params.end:
        url += f"/end/{play_params.end}"
    if play_params.page:
        url += f"/page/{play_params.page}"

    return {"url": url}


@app.get(
    "/rank/{category}",
    tags=["Games"],
    description=(
        "Generates a URL for the top-ranked board games on BoardGameGeek according to different categories: "
        "'global', 'familygames', 'strategygames', 'partygames', 'wargames', 'thematic', 'childrensgames', "
        "'cgs' or 'abstracts'. Optional 'page' parameter allow pagination."
    ),
)
def get_top_ranked_games(category: str, page: int = None):
    valid_categories = BGG_SUBDOMAINS + ['global']
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of {valid_categories}")

    # Build the URL
    if category == "global":
        url = "https://boardgamegeek.com/browse/boardgame"
    else:
        url = f"https://boardgamegeek.com/{category}/browse/boardgame"

    if page:
        url += f"/page/{page}"

    return {"url": url}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5003, log_level="info")
