import requests
import json
import time
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from urllib.parse import urlencode
from datetime import date
from pydantic import BaseModel
from typing import Optional
from xml_to_json_converter import *

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
    "/collection/{username}/{status}",
    tags=["Games"],
    description=(
        "Retrieves a BoardGameGeek user's collection based on status (own, prevowned, wishlist, etc.). "
        "Filter options include item id, personal and BGG ratings, and number of plays. "
        "Pagination is supported via the 'page' parameter, showing up to 100 items per page."
    ),
)
def get_user_collection(username: str, status: str, collection_params: CollectionParameters = Depends()):
    if status not in allowed_status:
        raise HTTPException(status_code=400, detail=f"Status must be one of {allowed_status}")

    # Build the URL
    url_params = {
        "username": username,
        status: 1
    }

    for key, value in collection_params.dict().items():
        if value is not None:
            url_params[key] = value

    url = f"https://www.boardgamegeek.com/xmlapi2/collection?{urlencode(url_params)}"

    for _ in range(MAX_RETRIES):
        response = get_url(url)
        result = collection_converter(response.content, collection_params.page)

        # If the result is not a "message" retry
        if "message" not in result:
            return result

        time.sleep(2)

    # If after all retries, we still get a message, return it
    return result


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5003, log_level="info")
