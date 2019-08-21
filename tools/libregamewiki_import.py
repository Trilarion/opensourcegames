"""
Imports game details from libregamewiki by scraping the website, starting from https://libregamewiki.org/Category:Games

Also parse rejected games (https://libregamewiki.org/Libregamewiki:Rejected_games_list) and maybe https://libregamewiki.org/Libregamewiki:Suggested_games
"""

import requests
import re

if __name__ == "__main__":

    regex_games = re.compile(r"<li><a href=\"\/(.+?)\".*?>(.+?)<\/a><\/li>") # url part, name

    # read base url
    base_url = 'https://libregamewiki.org/Category:Games'
    text = requests.get(base_url).text
    print(text)
