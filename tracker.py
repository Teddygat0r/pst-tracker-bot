import requests
import urllib.parse
from bs4 import BeautifulSoup as bs4

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

