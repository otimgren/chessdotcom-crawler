"""
This crawler goes through player profiles randomly and gets some basic data about them
"""


import sqlalchemy as sal
from sqlalchemy_utils import database_exists, create_database

from chess_crawler.crawler import Crawler
from chess_crawler.discriminators import NGamesDiscriminator, DiscriminatorPipeline, CheaterDiscriminator
from chess_crawler.getters import (ProfileGetter, PuzzlesGetter, LiveGetter, DailyGetter, TimeControl, 
                                    BasicStatsGetter, ArchivedOpponentsGetter, GetterPipeline)
from chess_crawler.player import Player
from chess_crawler.player_selectors import HigherLowerSelector
from chess_crawler.savers import ProfileSaver, SaverPipeline


def main():
    # Start the SQL engine
    engine = sal.create_engine('mysql://oskari:pw@localhost/chess_crawler', pool_recycle=3600, echo = False)
    if not database_exists(engine.url):
        create_database(engine.url)

    # Define data getters
    getters = [
        ProfileGetter(),
        BasicStatsGetter(),
        PuzzlesGetter(),
        LiveGetter(TimeControl.bullet),
        LiveGetter(TimeControl.blitz),
        LiveGetter(TimeControl.rapid),
        DailyGetter()
    ]

    # Define a getter pipeline based on the getters
    data_getter = GetterPipeline(getters)

    # Define the discriminator that is used to decide if a player should be saved
    discriminators = [NGamesDiscriminator(N = 50)]#, CheaterDiscriminator()]
    discr_pipeline = DiscriminatorPipeline(discriminators)

    # Define the saver pipeline
    savers = [
        ProfileSaver(table_name = 'profiles', engine = engine)
    ]
    saver_pipeline = SaverPipeline(savers)

    # Define the picker that is used to pick the next player
    player_selector = HigherLowerSelector()

    # Define the crawler
    crawler = Crawler(database_name='chess_crawler', engine=engine)

    # Run the crawler
    crawler.run(data_getter, discr_pipeline, saver_pipeline, player_selector,
                n_players = 10)#, player=Player(id='FlyingMo0se'))

if __name__ == "__main__":
    main()