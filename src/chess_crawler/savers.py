"""
Contains classes for saving data
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time
from typing import List

import sqlalchemy as sal
import pandas as pd
from sqlalchemy import engine
from sqlalchemy import MetaData, Table, Column, Integer, String
from tqdm import tqdm

from .getters import TimeControl
from .player import Player

@dataclass
class DataSaver(ABC):
    """
    Abstract parent class for saving data
    """
    table_name: str
    engine: sal.engine.Engine

    @abstractmethod
    def save_data(self, player: Player) -> None:
        """
        Saves some of the player data
        """
        ...

    @abstractmethod
    def init_table(self) -> None:
        """
        Initializes the SQL table to which the data is saved
        """
        ...

@dataclass
class SaverPipeline:
    """
    Contains a list of savers and has method to them
    """
    savers: List[DataSaver]

    def save_data(self, player: Player) -> None:
        # print("Saving data...")
        for saver in self.savers:
            saver.save_data(player)

class ProfileSaver(DataSaver):
    """
    Used to save basic info about a player profile into a MySQL database
    """
    def save_data(self, player: Player) -> None:
        # Gather data into dataframe
        df = self.gather_data(player)

        # Check that table is initialized, if not, initialize it
        if not self.engine.has_table(self.table_name):
            print(f"Initializing table: {self.engine.url}.{self.table_name}")
            self.init_table()

        # Save dataframe into SQL database
        df.to_sql(self.table_name, self.engine, if_exists = 'append')

    def init_table(self) -> None:
        """
        Initialize the SQL table
        """
        # Initialize MetaData object
        meta = MetaData()

        # Define the table
        table = Table(self.table_name, meta,
            Column('row_id', Integer, primary_key = True, autoincrement=True),
            Column('id', Integer),
            Column('username', String(50)),
            Column('jointime', Integer),
            Column('status', String(50)),
            Column('puzzle_rush_best', Integer),
            Column('blitz_rating', Integer),
            Column('blitz_n_games', Integer),
            Column('bullet_rating', Integer),
            Column('bullet_n_games', Integer),
            Column('rapid_rating', Integer),
            Column('rapid_n_games', Integer),
            Column('daily_rating', Integer),
            Column('daily_n_games', Integer),
            Column('puzzle_rating', Integer),
            Column('n_puzzles', Integer),
            Column('t_puzzles', Integer),
            Column('retrievetime', Integer)
        )

        meta.create_all(self.engine)


    def gather_data(self, player: Player) -> pd.DataFrame:
        """
        Gathers data to be saved into a pandas dataframe
        """
        # Initialize a container for data
        data = {}

        # Get data from the player object
        id = self.get_id(player)
        data["row_id"] = 0
        data["username"] = self.get_username(player)
        data["jointime"] = self.get_jointime(player)
        data["status"] = self.get_status(player)
        data["puzzle_rush_best"] = self.get_best_puzzle_rush(player)
        for time_ctrl in TimeControl:
            data[f"{time_ctrl.value}_rating"] = self.get_rating(player, time_ctrl)
            data[f"{time_ctrl.value}_n_games"] = self.get_n_games(player, time_ctrl)
        data["puzzle_rating"] = self.get_puzzle_rating(player)
        data["n_puzzles"] = self.get_n_puzzles(player)
        data["t_puzzles"] = self.get_t_puzzles(player)
        data["retrievetime"] = int(time.time())

        index = pd.Index([id], name = 'id')

        # Make dictionary into dataframe and return it
        return pd.DataFrame(data = data, index = index)
        
    def get_id(self, player: Player) -> str:
        """
        Get the user id of the player
        """
        return player.profile["player_id"]

    def get_username(self, player: Player) -> str:
        """
        Get the username of the player
        """
        return player.profile["username"]

    def get_jointime(self, player: Player) -> str:
        """
        Get the timestamp of when the player joined chess.com
        """
        return player.profile["joined"]

    def get_status(self, player: Player) -> str:
        """
        Get the premium status of a player
        """
        return player.profile["status"]

    def get_n_games(self, player: Player, time_ctrl: TimeControl) -> int:
        """
        Gets the number of games played with the specified time control.
        """
        key = 'chess_' + time_ctrl.value
        try:
            wins = player.basic_stats[key]['record']['win']
            losses = player.basic_stats[key]['record']['loss']
            draws = player.basic_stats[key]['record']['draw']

            return wins + losses + draws

        except KeyError as e:
            # print(e)
            # print(f"No {time_ctrl.value} games for {player.id}")
            return 0

    def get_rating(self, player: Player, time_ctrl: TimeControl) -> int:
        """
        Gets the rating of a player for the specified time control
        """
        key = 'chess_' + time_ctrl.value
        try:
            rating = player.basic_stats[key]['last']['rating']
            return rating

        except KeyError as e:
            # print(e)
            # print(f"No {time_ctrl.value} games for {player.id}")
            return None

    def get_best_puzzle_rush(self, player: Player) -> int:
        """
        Get the puzzle rush record of the player
        """
        try:
            return player.basic_stats['puzzle_rush']['best']['score']
        except KeyError:
            return 0

    def get_n_puzzles(self, player: Player) -> int:
        """
        Gets the number of puzzles attempted by the player
        """
        return player.puzzle_data.n

    def get_t_puzzles(self, player: Player) -> int:
        """
        Gets the number of seconds spent on puzzle training by player
        """
        return player.puzzle_data.t

    def get_puzzle_rating(self, player: Player) -> int:
        """
        Gets the current puzzle rating of the player
        """
        # Check that data exists for puzzles
        if len(player.puzzle_data.ratings_df.rating) < 1:
            return None

        return player.puzzle_data.ratings_df.rating.iloc[-1]

class TimeControlSaver(DataSaver):
    # to do
    pass

