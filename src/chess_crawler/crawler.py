"""
Defines a Crawler class
"""
from dataclasses import dataclass

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

    def run(self, getter: GetterPipeline, discriminator: DiscriminatorPipeline,
            saver: SaverPipeline, selector: PlayerSelector, n_players: int = 10,
            player: Player = None) -> None:

        # If initial player is not provided, use latest addition to database
        if not player:
            # Find the name of the table that data is being saved to
            table_name = saver.savers[0].table_name

            # Find a the latest player in the database and find data for them
            player = self.latest_player(table_name)
            getter.get_data(player)

            # Pick new player from opponents of that player
            player = Player(selector.pick_next(player))

        # Loop that processes the specified number of players
        print("Crawling through player profiles on chess.com...")
        for i in tqdm(range(n_players)):
            # Get data, check if player needs to be saved, save, find next player, repeat
            getter.get_data(player)
            if discriminator.should_save(player): 
                saver.save_data(player)
            player = Player(selector.pick_next(player))

    def latest_player(self, table_name: str) -> Player:
        """
        Returns the latest player stored in the table with the given name
        """
        # Fetch the last entry that was saved to the table
        with self.engine.connect() as conn:
            username = pd.read_sql(sal.text(f'SELECT username, row_id FROM {table_name} ORDER BY row_id DESC LIMIT 1'), conn).iloc[0]['username']
        
        return Player(id=username)