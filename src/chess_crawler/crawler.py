"""
Defines a Crawler class
"""
from dataclasses import dataclass
import random

import pandas as pd
import sqlalchemy as sal
from tqdm import tqdm

from .discriminators import DiscriminatorPipeline
from .getters import GetterPipeline
from .player import Player
from .player_selectors import PlayerSelector
from .savers import SaverPipeline

@dataclass
class Crawler:
    """
    Class for crawlers
    """
    database_name: str
    engine: sal.engine.Engine
    latest_saved_player: Player = None

    def run(self, getter: GetterPipeline, discriminator: DiscriminatorPipeline,
            saver: SaverPipeline, selector: PlayerSelector, n_players: int = 10,
            player: Player = None) -> None:

        # If initial player is not provided, use latest addition to database
        if not player:
            # Find the name of the table that data is being saved to
            table_name = saver.savers[0].table_name

            # Find a the latest player in the database and find data for them
            player = self.get_latest_player(table_name)
            self.latest_saved_player = player

            # Find opponent based on the latest player
            player = self.pick_opponent_based_on_db_entry(getter, selector, table_name)

        # Loop that processes the specified number of players
        print("Crawling through player profiles on chess.com...")
        for i in tqdm(range(n_players)):
            # Get data, check if player needs to be saved, save, find next player, repeat
            getter.get_data(player)
            if discriminator.should_save(player):
                saver.save_data(player)
                self.latest_saved_player = player
            player = Player(selector.pick_next(player))

            # Check that the latest player saved to database isn't the same one as the new pick;
            # if it is pick a random player from the database
            if self.same_as_latest(player):
                player = Player(self.random_previous_player_id(saver.savers[0].table_name))

    def same_as_latest(self, player: Player) -> bool:
        """
        Checks is a player is the same as the latest player stored in the database
        """
        return player.id == self.latest_saved_player.id


    def fetch_usernames(self, table_name: str) -> pd.DataFrame:
        """
        Fetches the usernames and row_ids from database
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(sal.text(f'SELECT username, row_id FROM {table_name} ORDER BY row_id'), conn)

        return df

    def get_latest_player(self, table_name: str) -> Player:
        """
        Returns the latest player stored in the table with the given name
        """
        # Fetch the last entry that was saved to the table
        username = self.fetch_usernames(table_name).iloc[0]['username']
        
        return Player(id=username)

    def random_previous_player_id(self, table_name: str) -> Player:
        """
        Returns a random player stored in the database
        """
        # Fetch datafraem of usernames
        usernames = self.fetch_usernames(table_name)['username'].tolist()

        # Pick a random username
        return random.choice(usernames)

    def pick_opponent_based_on_db_entry(self, getter: GetterPipeline, selector: PlayerSelector,
                                         table_name: str) -> Player:
        """
        Picks a random player from the database and returns one of their past opponents
        """
        db_player = Player(self.random_previous_player_id(table_name))

        getter.get_data(db_player)

        # Pick new player from opponents of that player
        return Player(selector.pick_next(db_player))

