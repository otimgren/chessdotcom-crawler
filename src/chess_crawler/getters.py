"""
Define the various classes that are used to get data from chess.com here
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from bs4 import BeautifulSoup
from enum import Enum
import js2py
import json
import pandas as pd
import re
import requests

from tqdm import tqdm

from .player import Player, TimeControl


@dataclass
class TimeSeriesData:
    """
    Container class for timeseries data, e.g. chess rating
    """
    n: int # Number of games played or puzzles attempted
    ratings_df: pd.DataFrame # Ratings at given times
    t: int = None # Amount of time spent on puzzles

class DataGetter(ABC):
    """
    Abstract parent class for fetching data
    """
    @abstractmethod
    def get_data(self, player: Player) -> None:
        """
        Scrapes data for the specific player
        """
        ...

@dataclass
class GetterPipeline(DataGetter):
    """
    Contains multiple getters and has a method to run all of them sequentially
    """
    getters: List[DataGetter]

    def get_data(self, player: Player) -> None:
        """
        Run get_data method for each getter in the list.
        """
        # print("Fetching data from chess.com...")
        for getter in self.getters:
            getter.get_data(player)

class ProfileGetter(DataGetter):
    """
    Gets the player profile data using the API
    """
    def get_data(self, player: Player) -> None:
        player.profile = json.loads(requests.get(f'https://api.chess.com/pub/player/{player.id}').text)

class BasicStatsGetter(DataGetter):
    """
    Gets the player stats data obtained using the API
    """
    def get_data(self, player: Player) -> None:
        player.basic_stats = json.loads(requests.get(f'https://api.chess.com/pub/player/{player.id}/stats').text)

class ArchivedGamesGetter(DataGetter):
    """
    Gets the player archived game data using the API
    """
    def get_data(self, player: Player) -> None:
        archives = json.loads(requests.get(f'https://api.chess.com/pub/player/{player.id}/games/archives').text)
        player.archived_games = json.loads(requests.get(archives['archives'][-1]).text)['games']

@dataclass
class ArchivedOpponentsGetter(DataGetter):
    """
    Gets data about the past opponents of the player
    """
    n: int = 3 # Number of archive months to retrieve

    def get_data(self, player: Player) -> None:
        archives = json.loads(requests.get(f'https://api.chess.com/pub/player/{player.id}/games/archives').text)['archives']
        
        # Container for opponents
        opponents = []
        ratings = []

        # Loop over the specified number of monthly archives
        for i in range(min(self.n, len(archives))):
            games = json.loads(requests.get(archives[-i]).text)['games']
            # Check if opponent was black or white
            for game in games:
                if game["white"]["username"].lower() == player.profile["username"].lower():
                    opponents.append(game["black"]["username"])
                    ratings.append(game["black"]["rating"])

                else:
                    opponents.append(game["white"]["username"])
                    ratings.append(game["white"]["rating"])
        
        player.past_opponents = {}
        player.past_opponents["id"] = opponents
        player.past_opponents["rating"] = ratings

@dataclass
class ArchivedTimeCtrlOpponentsGetter(DataGetter):
    """
    Gets data about the past opponents of the player for a specific time control
    """
    n: int = 3 # Number of archive months to retrieve

    def get_data(self, player: Player, time_ctrl: TimeControl) -> None:
        archives = json.loads(requests.get(f'https://api.chess.com/pub/player/{player.id}/games/archives').text)['archives']
        
        # Container for opponents
        opponents = []
        ratings = []

        # Loop over the specified number of monthly archives
        for i in range(min(self.n, len(archives))):
            games = json.loads(requests.get(archives[-i]).text)['games']

            # Loop over archived games
            for game in games:

                # Check if time control was right
                if game["time_class"] == time_ctrl.value:

                    # Check if opponent was black or white
                    if game["white"]["username"].lower() == player.profile["username"].lower():
                        opponents.append(game["black"]["username"])
                        ratings.append(game["black"]["rating"])

                    else:
                        opponents.append(game["white"]["username"])
                        ratings.append(game["white"]["rating"])
        
        player.past_opponents = {}
        player.past_opponents["id"] = opponents
        player.past_opponents["rating"] = ratings
class PuzzlesGetter(DataGetter):
    """
    Scrapes puzzle data for given player using the stats page of chess.com
    """
    def get_data(self, player: Player) -> None:
        # Get the html for the puzzles section of stats
        html_text = self.get_html(player)

        # Convert the html to soup
        soup = BeautifulSoup(html_text, features='html.parser')

        # Get ratings over time
        try:
            ratings_df = self.get_ratings(soup)
        except IndexError as e:
            print("Error in PuzzlesGetter:")
            print(e)
            print(f"Player: {player.id}")

        # Get the total number of puzzles solved
        n_puzzles = self.get_n_puzzles(soup)

        # Total time spent on puzzles
        t_puzzles = self.get_puzzle_time(soup)

        # Store the puzzle data in the player object
        data = TimeSeriesData(n = n_puzzles, ratings_df=ratings_df, t = t_puzzles)
        player.puzzle_data = data

    def get_html(self, player: Player) -> None:
        """
        Gets the html of the puzzles section of the stats page
        """
        return requests.get(f'https://www.chess.com/stats/puzzles/{player.id}').text

    def get_ratings(self, soup: BeautifulSoup) -> pd.DataFrame:
        """
        Gets puzzle ratings and their timestamps based on a BeautifulSoup object
        """
        # Find the part of the html that has the ratings
        ratings_string = soup.find_all('script', string = re.compile("ratings"))[0].text


        # Parse the string into timestamps and the corresponding ratings
        lines = ratings_string.split('\n')

        # Find the line that contains the ratings
        for line in lines:
            if 'ratings' in line:
                ratings_line = line

        # Find the part where the ratings are being parsed
        for block in ratings_line.split(" "):
            if '[' in block:
                parser_block = block

        # Use JavaScript to parse the ratings
        js_code = parser_block[:-1]
        json_result = list(js2py.eval_js(js_code))

        # Convert json_result into python dictionary and then to pandas dataframe
        result = {}
        result["timestamp"] = []
        result["rating"] = []
        for el in json_result:
            result["timestamp"].append(el["timestamp"])
            result["rating"].append(el["rating"])

        dataframe = pd.DataFrame(data = result)

        return pd.DataFrame(data = result)

    def get_n_puzzles(self, soup: BeautifulSoup) -> int:
        """
        Returns the number of puzzles attempted by the player
        """
        # Find the part of the html that has the number of attempts
        script_string = soup.find_all('script', string = re.compile("attemptCount:"))[0].text

        # Parse the string into timestamps and the corresponding ratings
        lines = script_string.split('\n')

        # Find the line that contains the attempt count
        for line in lines:
            if 'attemptCount' in line:
                attempts_line = line

        # Get the number of attempts from the line
        code_str = attempts_line.strip().replace(':',' =').replace(',','')

        return [int(s) for s in code_str.split() if s.isdigit()][0]

    def get_puzzle_time(self, soup: BeautifulSoup) -> int:
        """
        Returns the number of seconds used on puzzles by the player
        """
        # Find the part of the html that has the number of attempts
        script_string = soup.find_all('script', string = re.compile("trainingTime:"))[0].text

        # Parse the string into timestamps and the corresponding ratings
        lines = script_string.split('\n')

        # Find the line that contains the attempt count
        for line in lines:
            if 'trainingTime' in line:
                training_line = line

        # Get the number of attempts from the line
        code_str = training_line.strip().replace(':',' =').replace(',','')

        return [int(s) for s in code_str.split() if s.isdigit()][0]

class LiveGetter(DataGetter):
    """
    Gets timeseries data for the specified time control
    """
    def __init__(self, time_ctrl: TimeControl):
        self.time_ctrl = time_ctrl

    def get_data(self, player: Player) -> None:
        """
        Gets data for games with the given time control and stores in player
        """
        # Get the html for the correct stats page
        html_text = self.get_html(player)

        # Make html into BeautifulSoup
        soup = BeautifulSoup(html_text, features='html.parser')

        # Extract ratings from soup
        try:
            ratings_df = self.get_ratings(soup)
        except IndexError as e:
            print("Error in PuzzlesGetter:")
            print(e)
            print("HTML soup:")
            print(soup)
            print(f"Player: {player.id}")

        # Extract number of games played
        n = self.get_n_games(soup)

        # Store the dataframe in the player object
        data_name = self.time_ctrl.value + "_data" 
        data = TimeSeriesData(n = n, ratings_df = ratings_df)
        setattr(player, data_name, data)
        
    def get_html(self, player: Player) -> None:
        """
        Gets the html of the relevant time control section of the stats page
        """
        return requests.get(f'https://www.chess.com/stats/live/{self.time_ctrl.value}/{player.id}').text

    def get_ratings(self, soup: BeautifulSoup) -> pd.DataFrame:
        """
        Gets time control ratings and their timestamps based on a BeautifulSoup object
        """
        # Find the part of the html that has the ratings
        ratings_string = soup.find_all('script', string = re.compile("ratings"))[0].text

        # Parse the string into timestamps and the corresponding ratings
        lines = ratings_string.split('\n')

        # Find the line that contains the ratings
        for line in lines:
            if 'ratings' in line:
                ratings_line = line

        # Find the part where the ratings are being parsed
        for block in ratings_line.split(" "):
            if 'JSON.parse' in block:
                parser_block = block
                
        # Use JavaScript to parse the ratings
        js_code = parser_block[:-1]
        json_result = list(js2py.eval_js(js_code))

        # Convert json_result into python dictionary and then to pandas dataframe
        result = {}
        result["timestamp"] = []
        result["rating"] = []
        for el in json_result:
            result["timestamp"].append(el["timestamp"])
            result["rating"].append(el["rating"])
    
        return pd.DataFrame(data = result)

    def get_n_games(self, soup: BeautifulSoup) -> int:
        # Find the part of the html that has the ratings
        script_string = soup.find_all('script', string = re.compile("ratings"))[0].text

        # Parse the string into timestamps and the corresponding ratings
        lines = script_string.split('\n')

        # Find the line that contains the number of games played
        for line in lines:
            if 'chartData' in line:
                n_played_line = line[:-1].strip().replace("chartData:","chartData = ")
                
        # Evaluate the line using json
        code = n_played_line
        json_result = js2py.eval_js(code)

        # Tally to get total number of games
        n = json_result['all']['wins'] + json_result['all']['draws'] + json_result['all']['losses']

        return n

class DailyGetter(DataGetter):
    """
    Gets timeseries data for daily games
    """
    def get_data(self, player: Player) -> None:
        """
        Gets data for games with the given time control and stores in player
        """
        # Get the html for the correct stats page
        html_text = self.get_html(player)

        # Make html into BeautifulSoup
        soup = BeautifulSoup(html_text, features='html.parser')

        # Extract ratings from soup
        ratings_df = self.get_ratings(soup)

        # Extract number of games played
        n = self.get_n_games(soup)

        # Store the dataframe in the player object
        data_name = "daily_data" 
        data = TimeSeriesData(n = n, ratings_df = ratings_df)
        setattr(player, data_name, data)
        
    def get_html(self, player: Player) -> None:
        """
        Gets the html of the relevant time control section of the stats page
        """
        return requests.get(f'https://www.chess.com/stats/daily/chess/{player.id}').text

    def get_ratings(self, soup: BeautifulSoup) -> pd.DataFrame:
        """
        Gets time control ratings and their timestamps based on a BeautifulSoup object
        """
        # Find the part of the html that has the ratings
        ratings_string = soup.find_all('script', string = re.compile("ratings"))[0].text

        # Parse the string into timestamps and the corresponding ratings
        lines = ratings_string.split('\n')

        # Find the line that contains the ratings
        for line in lines:
            if 'ratings' in line:
                ratings_line = line

        # Find the part where the ratings are being parsed
        for block in ratings_line.split(" "):
            if 'JSON.parse' in block:
                parser_block = block
                
        # Use JavaScript to parse the ratings
        js_code = parser_block[:-1]
        json_result = list(js2py.eval_js(js_code))

        # Convert json_result into python dictionary and then to pandas dataframe
        result = {}
        result["timestamp"] = []
        result["rating"] = []
        for el in json_result:
            result["timestamp"].append(el["timestamp"])
            result["rating"].append(el["rating"])
    
        return pd.DataFrame(data = result)

    def get_n_games(self, soup: BeautifulSoup) -> int:
        # Find the part of the html that has the ratings
        script_string = soup.find_all('script', string = re.compile("ratings"))[0].text

        # Parse the string into timestamps and the corresponding ratings
        lines = script_string.split('\n')

        # Find the line that contains the number of games played
        for line in lines:
            if 'chartData' in line:
                n_played_line = line[:-1].strip().replace("chartData:","chartData = ")
                
        # Evaluate the line using json
        code = n_played_line
        json_result = js2py.eval_js(code)

        # Tally to get total number of games
        n = json_result['all']['wins'] + json_result['all']['draws'] + json_result['all']['losses']

        return n







