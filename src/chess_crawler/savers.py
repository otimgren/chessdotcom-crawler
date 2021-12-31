"""
Contains classes for saving data
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time
from typing import List

import sqlalchemy as sal
import pandas as pd
from sqlalchemy import MetaData, Table, Column, Integer, String
from sqlalchemy_utils.functions.orm import table_name

from .getters import TimeControl
from .player import Player

@dataclass
class DataSaver(ABC):
    """
    Abstract parent class for saving data
    """
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

@dataclass
class ProfileSaver(DataSaver):
    """
    Used to save basic info about a player profile into a MySQL database
    """
    table_name: str
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
        id = player.get_id()
        data["row_id"] = 0
        data["username"] = player.get_username()
        data["jointime"] = player.get_jointime()
        data["status"] = player.get_status()
        data["puzzle_rush_best"] = player.get_best_puzzle_rush()
        for time_ctrl in TimeControl:
            data[f"{time_ctrl.value}_rating"] = player.get_rating(time_ctrl)
            data[f"{time_ctrl.value}_n_games"] = player.get_n_games(time_ctrl)
        data["puzzle_rating"] = player.get_puzzle_rating()
        data["n_puzzles"] = player.get_n_puzzles()
        data["t_puzzles"] = player.get_t_puzzles()
        data["retrievetime"] = int(time.time())

        index = pd.Index([id], name = 'id')

        # Make dictionary into dataframe and return it
        return pd.DataFrame(data = data, index = index)

@dataclass
class TimeControlSaver(DataSaver):
    """
    Used to save time series data for different time controls
    """
    time_ctrl: TimeControl
    def save_data(self, player: Player) -> None:
        # Gather data into dataframe
        df = self.gather_data(player)

        # Figure out the name for the table
        table_name = self.time_ctrl.value +'_'+ player.get_username()

        # Check that table is initialized, if not, initialize it
        if not self.engine.has_table(table_name):
            self.init_table(table_name)

        # Save dataframe into SQL database
        df.to_sql(table_name, self.engine, if_exists = 'replace')

    def init_table(self, table_name: str) -> None:
        """
        Initializes the table in which data is saved
        """
        # Initialize MetaData object
        meta = MetaData()

        # Define the table
        table = Table(table_name, meta,
            Column('timestamp', Integer, primary_key = True),
            Column('rating', Integer),
        )

        meta.create_all(self.engine)

    def gather_data(self, player: Player) -> pd.DataFrame:
        """
        Gathers the timeseries data for the time control to a pandas dataframe 
        """
        # Figure out the name for the data we want
        data_name = self.time_ctrl.value + "_data"
        
        # Return the data
        return getattr(player, data_name).ratings_df

    

