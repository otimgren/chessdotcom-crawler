"""
This crawler goes through player profiles based on a list. Used to get new data for profiles that were
crawled through earlier.
"""


import sqlalchemy as sal
from sqlalchemy_utils import database_exists, create_database

from chess_crawler.crawler import Crawler
from chess_crawler.discriminators import NGamesDiscriminator, DiscriminatorPipeline, CheaterDiscriminator
from chess_crawler.getters import (ProfileGetter, PuzzlesGetter, LiveGetter, DailyGetter, TimeControl, 
                                    BasicStatsGetter, ArchivedOpponentsGetter, GetterPipeline)
from chess_crawler.player import Player
from chess_crawler.player_selectors import ListSelector
from chess_crawler.savers import ProfileSaver, SaverPipeline, TimeControlSaver
from chess_crawler.utils import get_usernames


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
        ProfileSaver(table_name = 'profiles', engine = engine),
        TimeControlSaver(engine=engine, time_ctrl = TimeControl.rapid),
        TimeControlSaver(engine=engine, time_ctrl = TimeControl.bullet),
        TimeControlSaver(engine=engine, time_ctrl = TimeControl.blitz)
    ]
    saver_pipeline = SaverPipeline(savers)

    # Get list of usernames to go through
    usernames = get_usernames(engine)
    first_username = usernames.pop(0)

    # Define the picker that is used to pick the next player
    player_selector = ListSelector(usernames)

    # Define the crawler
    crawler = Crawler(database_name='chess_crawler', engine=engine)

    # Run the crawler
    crawler.run(data_getter, discr_pipeline, saver_pipeline, player_selector,
                n_players = len(usernames)+1, player=Player(id=first_username))

if __name__ == "__main__":
    main()