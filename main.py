from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from xml.etree import ElementTree
import requests
import json


app = FastAPI()

origins = [
    "https://chat.openai.com",  # Allow CORS requests from this origin.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/user/{username}")
def get_user_info(username: str):
    response = requests.get(f"https://www.boardgamegeek.com/xmlapi2/user?name={username}&buddies=1")
    return response.content


@app.get("/hot")
def get_hot_games(limit: int = None):
    response = requests.get("https://www.boardgamegeek.com/xmlapi2/hot?type=boardgame")
    root = ElementTree.fromstring(response.content)
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


@app.get("/collection/{username}")
def get_user_collection(username: str):
    response = requests.get(
        f"https://www.boardgamegeek.com/xmlapi2/collection?username={username}&subtype=boardgame&excludesubtype=boardgameexpansion")
    return response.content


@app.get("/plays/{username}/{date1}/{date2}")
def get_user_plays(username: str, date1: str, date2: str):
    response = requests.get(
        f"https://www.boardgamegeek.com/xmlapi2/plays?username={username}&mindate={date1}&maxdate={date2}")
    return response.content


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5003, log_level="info")
