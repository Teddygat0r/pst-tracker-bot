import requests
import urllib.parse
from bs4 import BeautifulSoup as bs4
import json
import valo_api

def get_match_count(user: str, mode="competitive", allSeason=True):
    try:
        url = f"https://tracker.gg/valorant/profile/riot/{ user }/overview?playlist={ mode }".replace('#', '%23')
        if allSeason:
            url += "&season=all"

        r = requests.get(url)
        soup = bs4(r.text, 'html.parser')

        mytext = soup.find('span', {"class": "matches"}).getText().split(' ')[1]
        return mytext
    except Exception as e:
        print(e)
        return "broke"

def get_match_history(user: str, mode="competitive", allSeason=True, region="na", count=5):
    try:
        return valo_api.endpoints.get_match_history_by_name_v3(region, user.split('#')[0], user.split('#')[1], game_mode=mode, size=count)
        
    except Exception as e:
        print(e)
        return "broke"
    
def get_image_link(agent: str):
    operators = json.load(open('operator_data.json'))['data']
    for operator in operators:
        if agent == operator['displayName']:
            return operator['displayIcon']

def getKAST(puuid, round):
    pdeathTime = -1
    murderer = None
    for player in round.player_stats:
        for kill in player.kill_events:
            if kill.killer_puuid == puuid:
                return True
            if kill.victim_puuid == murderer and kill.kill_time_in_round - pdeathTime < 5000:
                return True
            if puuid in [ast.assistant_puuid for ast in kill.assistants]:
                return True
            if kill.victim_puuid == puuid:
                pdeathTime = kill.kill_time_in_round
                murderer = kill.killer_puuid
    
    if pdeathTime == -1:
        return True

    return False

def statKast(puuid, round):
    pdeathTime = -1
    murderer = None
    traded = False
    survived = True
    assists = 0
    for player in round.player_stats:
        for kill in player.kill_events:
            if kill.victim_puuid == murderer and kill.kill_time_in_round - pdeathTime < 5000:
                traded = True
            if puuid in [ast.assistant_puuid for ast in kill.assistants]:
                assists += 1
            if kill.victim_puuid == puuid:
                pdeathTime = kill.kill_time_in_round
                murderer = kill.killer_puuid
                survived = False
    
    return assists, traded, survived


def refresh_operator_data():
    with open('operator_data.json', 'w') as myf:
        myf.write(requests.get('https://valorant-api.com/v1/agents/?isPlayableCharacter=true'))

