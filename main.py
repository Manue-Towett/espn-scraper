import re
import json
import dataclasses
from typing import Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from utils import Logger

print(datetime.strptime("2023-10-26T01:30Z", "%Y-%m-%dT%H:%MZ"))

BASE_URL = "https://www.espn.com/{}/team/schedule/_/name/{}/season/{}"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Dnt": "1",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

@dataclasses.dataclass
class Game:
    date: datetime
    season_year: int
    home_team: Optional[str] = None
    home_team_abbr: Optional[str] = None
    away_team: Optional[str] = None
    away_team_abbr: Optional[str] = None
    home_score: Optional[str] = None
    away_score: Optional[str] = None

@dataclasses.dataclass
class Team:
    id: str
    href: str
    name: str
    shortName: str
    abbrev: str
    logo: str

class ESPNScraper:
    """Scrapes past games from espn website https://www.espn.com/"""
    def __init__(self) -> None:
        self.logger = Logger(__class__.__name__)
        self.logger.info("{:*^50}".format(f"{__class__.__name__} Started"))

        self.games: list[Game] = []
        self.teams_crawled: list[str] = []

    def __request(self, sport: str, abbrev: str, year: int) -> requests.Response:
        """Requests data from the website"""
        url = BASE_URL.format(sport, abbrev, year)

        while True:
            try:
                response = requests.get(url, headers=HEADERS)

                if response.ok:
                    return response
                
            except: pass
    
    @staticmethod
    def __read_json(json_path: str) -> list[Team]:
        with open(json_path, "r") as file:
            return [Team(**team) for team in json.load(file)]
    
    @staticmethod
    def __extract_script_text(response: requests.Response) -> str:
        soup = BeautifulSoup(response.text, "html.parser")

        for script in soup.select("script"):
            script_text = script.get_text(strip=True)

            if re.search(r"window\['__espnfitt__'\]", script_text):
                return script_text.split("window['__espnfitt__']=")[-1].strip()
    
    def __extract_games(self, response: requests.Response, current_team: Team) -> list[Game]:
        """Extracts games from the response object"""
        self.logger.info("Extracting games...")

        text = self.__extract_script_text(response)

        data = json.loads(text.rstrip(";"))

        games = []

        try:
            team_schedule = data["page"]["content"]["scheduleData"]["teamSchedule"]

            posts = team_schedule[0]["events"]["post"][0]["group"]

            for post in posts:
                # datetime.strptime(post["date"]["date"], "%Y-%m-%dT%H:%MZ")
                try:
                    game = Game(date=post["date"]["date"],
                                season_year=post["seasonYear"])

                    if post["opponent"]["homeAwaySymbol"] == "@":
                        game.home_team = current_team.name
                        game.home_team_abbr = current_team.abbrev.upper()
                        game.away_team = post["opponent"]["displayName"]
                        game.away_team_abbr = post["opponent"]["abbrev"]
                        game.home_score = post["result"]["currentTeamScore"]
                        game.away_score = post["result"]["opponentTeamScore"]

                    else:
                        game.away_team = current_team.name
                        game.away_team_abbr = current_team.abbrev.upper()
                        game.home_team = post["opponent"]["displayName"]
                        game.home_team_abbr = post["opponent"]["abbrev"]
                        game.away_score = post["result"]["currentTeamScore"]
                        game.home_score = post["result"]["opponentTeamScore"]

                except: continue
                
                if game.home_team in self.teams_crawled or game.away_team in self.teams_crawled:
                    continue

                games.append(game)

        except Exception as e: print(e)

        return games
    
    def __save(self, name: str, games: list[Game]) -> None:
        self.logger.info("Saving results...")

        results = [dataclasses.asdict(game) for game in games]

        with open("./games/{}".format(name), "w") as file:
            json.dump(results, file, indent=4)
        
        self.logger.info("{} games saved to json.".format(len(results)))

        del results

    def run(self, league: str) -> None:
        nba_teams = self.__read_json(f"./data/{league}.json")

        with open("./data/seasons.json") as f:
            seasons = [season["value"] for season in json.load(f)]

        seasons.sort()

        for team in nba_teams:
            for season in seasons:
                self.logger.info("Fetching {} games for {} in {}".format(league, team.shortName, season))

                response = self.__request(league, team.abbrev, season)

                games = self.__extract_games(response, team)

                self.games.extend(games)

                self.__save(f"{league}.json", self.games)

                # return
            
            self.teams_crawled.append(team.name)
    

app = ESPNScraper()
app.run("nba")