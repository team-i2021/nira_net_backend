import asyncio
import aiohttp
import sanic
import json
import logging

logging.basicConfig(filename="backend.log", format="%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s", level="INFO")

from sanic import response, Request
from sanic_ext import Extend

from motor import motor_asyncio

config = json.load(open("config.json", "r"))

app = sanic.Sanic(__name__)
app.config.CORS_ORIGINS = config["cors_origins"]
Extend(app)

APIEndpoint = "https://discord.com/api"

vclimit_channel_collection: motor_asyncio.AsyncIOMotorCollection = motor_asyncio.AsyncIOMotorClient(config["mongo_uri"])[config["mongo_db"]]["vclimit_channel"]

_session: aiohttp.ClientSession | None = None

@app.route("/")
async def index_api(request: Request):
    return response.json(body={"message": "Hello, nirand!"})

@app.post("/revoke")
async def revoke_api(request: Request):
    url = f"{APIEndpoint}/oauth2/token/revoke"
    data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "token": request.json["token"]
    }
    session = await get_session()
    async with session.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data) as resp:
        return response.json(body=await resp.json())

@app.post("/gettoken")
async def get_token_api(request: Request):
    url = f"{APIEndpoint}/oauth2/token"
    data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "grant_type": "authorization_code",
        "code": request.json["auth_code"],
        "redirect_uri": request.json["redirect_uri"],
        "scope": "identify guilds"
    }
    session = await get_session()
    async with session.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data) as resp:
        return response.json(body=await resp.json())

@app.post("/refreshtoken")
async def refresh_token_api(request: Request):
    url = f"{APIEndpoint}/oauth2/token"
    data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": request.json["refresh_token"],
        "redirect_uri": request.json["redirect_uri"],
        "scope": "identify guilds"
    }
    session = await get_session()
    async with session.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data) as resp:
        return response.json(body=await resp.json())

@app.post("/getuser")
async def get_user_api(request: Request):
    url = f"{APIEndpoint}/users/@me"
    headers = {"Authorization": "Bearer " + request.json["access_token"]}
    session = await get_session()
    async with session.get(url, headers=headers) as resp:
        return response.json(body=await resp.json())

@app.post("/getguilds")
async def get_guilds_api(request: Request):
    url = f"{APIEndpoint}/users/@me/guilds"
    c_headers = {"Authorization": "Bearer " + request.json["access_token"]}
    b_headers = {"Authorization": "Bot " + config["bot_token"]}
    session = await get_session()
    async with session.get(url, headers=c_headers) as resp1:
        guilds1 = await resp1.json()
    async with session.get(url, headers=b_headers) as resp2:
        guilds2 = await resp2.json()
    guilds = [i for i in guilds1 if any(j["id"] == i["id"] for j in guilds2)]
    return response.json(body=guilds)

@app.post("/getchannels")
async def get_channels_api(request: Request):
    return response.json(body={"message": "Deprecated endpoint"})

    guild_id = request.json["guild_id"]
    url = f"{APIEndpoint}/guilds/{guild_id}/channels"
    headers = {"Authorization": "Bot " + config["bot_token"]}
    session = await get_session()
    async with session.get(url, headers=headers) as resp:
        print(url)
        return response.json(body=await resp.json())

@app.post("/getvcs")
async def get_vcs_api(request: Request):
    guild_id = request.json["guild_id"]
    url = f"{APIEndpoint}/guilds/{guild_id}/channels"
    headers = {"Authorization": "Bot " + config["bot_token"]}
    session = await get_session()
    async with session.get(url, headers=headers) as resp:
        channels = await resp.json()
        vcs = [i for i in channels if i["type"] == 2]
        # {"guild_id": guild_id, channel_id: True}
        vcc = await vclimit_channel_collection.find_one({"guild_id": int(guild_id)})
        if vcc is None:
            vcc = {}
            asyncio.ensure_future(vclimit_channel_collection.insert_one({"guild_id": int(guild_id)}))
        else:
            vcc["_id"] = str(vcc["_id"])
        return response.json(body={"channels": vcs, "configs": vcc})

@app.post("/getmember")
async def get_member_api(request: Request):
    guild_id = request.json["guild_id"]
    user_id = request.json["user_id"]
    url = f"{APIEndpoint}/guilds/{guild_id}/members/{user_id}"
    headers = {"Authorization": "Bot " + config["bot_token"]}
    session = await get_session()
    async with session.get(url, headers=headers) as resp:
        return response.json(body=await resp.json())

@app.post("/getowner")
async def get_owner_api(request: Request):
    guild_id = request.json["guild_id"]
    url = f"{APIEndpoint}/guilds/{guild_id}"
    headers = {"Authorization": "Bot " + config["bot_token"]}
    session = await get_session()
    async with session.get(url, headers=headers) as resp:
        return response.json(body={"owner_id": (await resp.json())["owner_id"]})

@app.post("/canmanage")
async def can_manage_api(request: Request):
    guild_id = request.json["guild_id"]
    role_ids = request.json["role_ids"]
    url = f"{APIEndpoint}/guilds/{guild_id}/roles"
    headers = {"Authorization": "Bot " + config["bot_token"]}
    session = await get_session()
    async with session.get(url, headers=headers) as resp:
        roles = await resp.json()
    for m_roles in role_ids:
        # rolesの中にm_rolesが含まれており、かつそのm_rolesのpermissionsに0x20が含まれているか
        if any(m_roles == i["id"] and i["permissions"] & 0x20 == 0x20 for i in roles):
            return response.json(body={"can_manage": True})
    return response.json(body={"can_manage": False})

@app.post("/setvclimit")
async def set_vc_limit_api(request: Request):
    guild_id = int(request.json["guild_id"])
    channel_id = request.json["channel_id"]
    enable = request.json["enable"]
    if enable:
        await vclimit_channel_collection.update_one({"guild_id": guild_id}, {"$set": {channel_id: True}}, upsert=True)
    else:
        await vclimit_channel_collection.update_one({"guild_id": guild_id}, {"$unset": {channel_id: True}}, upsert=True)
    return response.json(body={"message": "OK", "setting": enable})

@app.listener("before_server_start")
async def before_server_start(app, loop):
    global _session
    _session = aiohttp.ClientSession(loop=loop)

async def get_session():
    global _session
    if _session is None:
        _session = aiohttp.ClientSession()
    return _session

if __name__ == "__main__":
    app.run(host=config["host"], port=config["port"])
