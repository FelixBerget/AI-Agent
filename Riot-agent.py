import anthropic
from dotenv import load_dotenv
import requests
import os
import json
from datetime import datetime
load_dotenv()
client = anthropic.Anthropic()
riot_key = os.getenv("RIOT_API_KEY")
messages1 = []
messages2 = []
messages3 = []

tools=[
      {"name":"find_riot_account","description":"Find account in the RIOT games API by tagline and game name",        
        "input_schema":{
        "type": "object",
        "properties": {
            "server":{"type":"string","description":"The server this player is on, it is either americas, europe or asia, do not use like euw1 or kr"},
            "game_name": {"type": "string", "description": "The username/gamename for the account you are looking for"},
            "tag_line": {"type": "string", "description": "The tagnline for the account you are looking for"}

        },
            "required":["server","game_name","tag_line"]
        }},
        {"name":"find_masteries","description":"Find the top champions in masteries by account id",        
        "input_schema":{
        "type": "object",
        "properties": {
            "server":{"type":"string","description":"The server this player is on, this one it is set up with like euw1 or kr, do not use like europe"},
            "encryptedPUUID": {"type": "string", "description": "The id of the player that we want the masteries of"},

        },
            "required":["server","encryptedPUUID"]
        }},
            {"name":"find_match_history","description":"Find match history of an account",        
        "input_schema":{
        "type": "object",
        "properties": {
            "server":{"type":"string","description":"The server this player is on, this one it is set up with like europe or asia"},
            "puuid": {"type": "string", "description": "The id of the player that we want the match history of"},
            "count": {"count":"number","description":"the amount of games we want"}

        },
            "required":["server","puuid","count"]
        }},
            {"name":"find_match_by_id","description":"Find a match by the id, and give stats from it",        
        "input_schema":{
        "type": "object",
        "properties": {
            "server":{"type":"string","description":"The server this player is on, this one it is set up with with like europe or asia"},
            "match_id": {"type": "string", "description": "The id of the match you want"},

        },
            "required":["server","match_id"]
        }},
                {"name":"find_recent_matches","description":"Find the latest matches on an account by using its id max 10 games",        
        "input_schema":{
        "type": "object",
        "properties": {
            "server":{"type":"string","description":"The server this player is on, it is either americas, europe or asia, do not use like euw1 or kr"},
            "game_name": {"type": "string", "description": "The username/gamename for the account you are looking for"},
            "tag_line": {"type": "string", "description": "The tagnline for the account you are looking for"},
            "count": {"type":"integer","description":"The amount of games we are looking for"}

        },
            "required":["server","game_name","tag_line","count"]
        }}

]

def run_individual_agent_stats(user_text,messages):
    messages.append({"role":"user","content":user_text})
    message = client.messages.create(
        system="You get leauge of legends data from the API and then prerprocess it so that it is understandable, but does not take up that much tokens for later discussions, be sure to make a rather comprehensive setup max 7 games",
        tools=tools,
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=messages
    )
    messages.append({"role":"assistant","content":message.content})
    while message.stop_reason == "tool_use":
        tool_results = []
        for i in message.content:
            if i.type == "tool_use":
                result = tool_functions[i.name](**i.input)
                tool_results.append({
                    "type":"tool_result",
                    "tool_use_id":i.id,
                    "content":json.dumps(result)
                })
        messages.append({"role":"user","content":tool_results})
        message = client.messages.create(
            system="You get leauge of legends data from the API and then prerprocess it so that it is understandable, but does not take up that much tokens for later discussions, be sure to make a rather comprehensive setup max 5 games",
            tools=tools,
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=messages
        )
        messages.append({"role": "assistant", "content": message.content})
        
    for block in message.content:
        if block.type == "text":
            return block.text
    return "*Says nothing*"


def run_individual_agent_pundit_negative(user_text,messages):
    messages.append({"role":"user","content":user_text})
    message = client.messages.create(
        system="You are a pundit who does not get stats themselves but discusses after getting stats from someone else, for the most part say not too many sentences you like if it was a sports TV cast. You are more pessimistic and negative.",
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=messages
    )
    messages.append({"role":"assistant","content":message.content})
        
    for block in message.content:
        if block.type == "text":
            return block.text
    return "*Says nothing*"

def run_individual_agent_pundit_positive(user_text,messages):
    messages.append({"role":"user","content":user_text})
    message = client.messages.create(
        system="You are a pundit who does not get stats themselves but discusses after getting stats from someone else, for the most part say not too many sentences you like if it was a sports TV cast. You are more positvie and chill.",
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=messages
    )
    messages.append({"role":"assistant","content":message.content})
        
    for block in message.content:
        if block.type == "text":
            return block.text
    return "*Says nothing*"

def load_id_data():
    game_mode_url = "riot_game_modes.json"
    champions_id = "riot_ids.json"
    items_id = "riot_items.json"
    with open(game_mode_url, "r") as f:
        game_modes = json.load(f)
    with open(champions_id, "r", encoding="utf-8") as f:
        champion_data = json.load(f)
    with open(items_id, "r", encoding="utf-8") as f:
        items_data = json.load(f)
    game_modes_dictionary = {}
    for i in game_modes:
        game_modes_dictionary[i["queueId"]]=i["description"]
    champion_dictionary = {}
    for i in champion_data["data"].values():
        champion_dictionary[int(i["key"])]=i["name"]
    item_dictionary = {}
    for item_id, item in items_data["data"].items():
        item_dictionary[int(item_id)] = item["name"]
    return game_modes_dictionary, champion_dictionary, item_dictionary


def summarize_for_one_player(puuid,match_data):
    returndata = None
    for i in match_data["info"]["participants"]:
        if i["puuid"]==puuid:
            returndata = {}
            returndata["championName"] = i["championName"]
            returndata["kills"] = i["kills"]
            returndata["deaths"] = i["deaths"]
            returndata["assists"] = i["assists"]
            returndata["win"] = i["win"]
            returndata["itemNames"] = i["itemNames"]
            returndata["gameMode"] = match_data["info"]["gameMode"]
            returndata["gameDuration"] = match_data["info"]["gameDuration"]/60
            returndata["gameStartTimestamp"] = match_data["info"]["gameStartTimestamp"]
            returndata["gameStart"] = datetime.fromtimestamp(match_data["info"]["gameStartTimestamp"] / 1000).strftime("%Y-%m-%d %H:%M")
            returndata["timeCCingOthers"] = i["timeCCingOthers"]
            returndata["totalDamageDealtToChampions"] = i["totalDamageDealtToChampions"]
    if returndata == None:
        return "Error did not find data of player in match"
    return returndata
            

#def game_details_for_specific_game(game_number,server, game_name, tag_line):
#    account = find_riot_account(server,game_name,tag_line)
#    new_games = find_match_history(server,account["puuid"],10)
#    counter = 0
#    game = None
#    if game_number > len(new_games) and game_number < 1:
#        return f"Number out of bounds should be max {len(new_games)} or more than 0"
#    for i in new_games:
#        counter+=1
#        if game_number == counter:
#            game = find_match_by_id(server,i)
#    if game is None:
#        return "Could not find game"
#    return game
    

def find_riot_account(server, game_name, tag_line):
    url = f"https://{server}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": riot_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Request failed with status {response.status_code}"


def find_masteries(server,encryptedPUUID):
    url = f"https://{server}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{encryptedPUUID}/top/"
    headers = {"X-Riot-Token": riot_key}
    response = requests.get(url, headers=headers)
    top_ten_masteries = []
    if response.status_code == 200:
        data = response.json()
        for i in data:
            i["championName"] = champion_dictionary.get(i["championId"], "Unknown champion")
        return data
    else:
        return f"Request failed with status {response.status_code}"


def find_match_history(server,puuid,count):
    url = f"https://{server}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids/"
    headers = {"X-Riot-Token": riot_key}
    response = requests.get(url, headers=headers,params={"count": count})
    top_ten_masteries = []
    if response.status_code == 200:
        return response.json()
    else:
        return f"Request failed with status {response.status_code}"

def find_match_by_id(server,match_id):
    url = f"https://{server}.api.riotgames.com/lol/match/v5/matches/{match_id}/"
    headers = {"X-Riot-Token": riot_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        queue_id = data["info"]["queueId"]
        game_mode = game_modes_dictionary.get(queue_id, f"Unknown mode (queue {queue_id})")
        data["info"]["gameMode"] = game_mode
        for i in data["info"]["participants"]:
            i["championName"] = champion_dictionary.get(i["championId"], "Unknown champion")
            item_names = []
            for item_slot in range(7): 
                item_id = i[f"item{item_slot}"]
                if item_id != 0:
                    item_names.append(item_dictionary.get(item_id, "Unknown item"))
            i["itemNames"] = item_names
        return data
    else:
        return f"Request failed with status {response.status_code}"

def find_recent_matches(server, game_name, tag_line, count):
    if count > 10:
        count = 10
    return_list = []
    account = find_riot_account(server,game_name,tag_line)
    if "Request failed" in account:
        return f"Did not find account on name {game_name} and tag {tag_line}"
    else:
        match_history = find_match_history(server,account["puuid"],count)
        if "Request failed" in match_history:
            return "Error with finding games"
        for i in match_history:
            my_stats = find_match_by_id(server,i)
            if "Request failed" in my_stats:
                return "Error with missing stats from individual game"
            my_summary = summarize_for_one_player(account["puuid"],my_stats)
            return_list.append(my_summary)    
    if len(return_list) == 0:
        return "No games on the account"
    return {
        "games_returned": len(return_list),
        "note": "Most recent first. Maximum 10 games per request.",
        "games": return_list,
    }


tool_functions = {"find_match_by_id":find_match_by_id,"find_match_history":find_match_history,"find_recent_matches":find_recent_matches,"find_riot_account":find_riot_account,"find_masteries":find_masteries}
game_modes_dictionary, champion_dictionary, item_dictionary = load_id_data()
game_modes_dictionary[1750] = "ARAM Mayhem"
result3 = "Stats guy : " +  run_individual_agent_stats("Fetch a report of the account of the player Jovial Kar with the tag EUW on the europe server",messages3)
print(result3)
print("\n")
result2 = "Pundit Johnson : " + run_individual_agent_pundit_positive(result3,messages1)
print(result2)
print("\n")
result1 = "Pundit Peterson : " + run_individual_agent_pundit_negative(result3 + "\n\n" + result2,messages2)
print(result1)
print("\n")
for x in range(3):
    result2 = "Pundit Johnson: " +   run_individual_agent_pundit_positive(result1,messages1)
    print(result2)
    print("\n")
    result1 = "Pundit Peterson : " + run_individual_agent_pundit_negative(result2,messages2)
    print(result1)
    print("\n")
    
    

