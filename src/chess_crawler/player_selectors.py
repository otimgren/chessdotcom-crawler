"""
Classes for implementing strategies for choosing the next player to be looked at by the crawler
"""
from abc import ABC, abstractmethod
import random
from typing import List

import numpy as np

from .getters import ArchivedTimeCtrlOpponentsGetter
from .player import Player, TimeControl

class PlayerSelector(ABC):
    """
    Abstract parent class for PlayerSelectors that are used to pick the next player to look at.
    """
    @abstractmethod
    def pick_next(self, player: Player) -> str:
        """
        Picks the next player to look at. Returns the username of the next playr.
        """
        ...

    def get_opponents(self, player: Player, n: int = 3) -> List[str]:
        """
        Find past opponents based on archival data
        """
        ArchivedTimeCtrlOpponentsGetter(n = n).get_data(player, TimeControl.rapid)

    def not_a_computer(self, player_username: str) -> str:
        """
        Checks that player name doesn't contain the word computer to make sure I don't pick
        one of the chess.com AIs as the next player
        """
        return 'Computer' not in player_username

class RandomOpponentSelector(PlayerSelector):
    """
    Picks a random past opponent based on archived games data
    """
    def pick_next(self, player: Player) -> str:
        # Get the past opponents
        self.get_opponents(player)

        # Pick a random past opponent
        username = random.choice(player.past_opponents["id"])

        # Check user is not an AI
        if self.not_a_computer(username):
            return username
        else:
            return RandomOpponentSelector().pick_next(player)

class HighestRatedOpponentSelector(PlayerSelector):
    """
    Picks highest rated past opponent based on archived games data
    """
    def pick_next(self, player: Player) -> str:
        # Get the past opponents
        self.get_opponents(player)

        # Pick past opponent with highest rating
        username = player.past_opponents["id"][np.argmax(player.past_opponents["rating"])]

        # Check user is not an AI
        if self.not_a_computer(username):
            return username
        else:
            return RandomOpponentSelector().pick_next(player)

class RandomHigherRatedOpponentSelector(PlayerSelector):
    """
    Picks a random higher rated past opponent based on archived games data
    """
    def pick_next(self, player: Player) -> str:
        # Get the past opponents
        self.get_opponents(player)

        # Get list of opponents with higher ratings than current player
        index = np.array(player.past_opponents["rating"]) > player.get_rapid_rating()
        opponents = np.array(player.past_opponents["id"])[index]

        # If list of opponents is empty, return a random opponent
        if len(opponents) == 0:
            return RandomOpponentSelector().pick_next(player)

        # Pick a past opponent with higher rating
        username = random.choice(opponents)

        # Check user is not an AI
        if self.not_a_computer(username):
            return username
        else:
            return RandomOpponentSelector().pick_next(player)

class RandomLowerRatedOpponentSelector(PlayerSelector):
    """
    Picks a random lower rated past opponent based on archived games data
    """
    def pick_next(self, player: Player) -> str:
        # Get the past opponents
        self.get_opponents(player)

        # Get list of opponents with higher ratings than current player
        index = np.array(player.past_opponents["rating"]) < player.get_rapid_rating()
        opponents = np.array(player.past_opponents["id"])[index]

        # If list of opponents is empty, return a random opponent
        if len(opponents) == 0:
            return RandomOpponentSelector().pick_next(player) 

        # Pick a past opponent with lower rating
        username = random.choice(opponents)

        # Check user is not an AI
        if self.not_a_computer(username):
            return username
        else:
            return RandomOpponentSelector().pick_next(player)


class HighestUntilSwitchSelector(PlayerSelector):
    """
    Uses the HighestRatedOpponent selector until a specified rating, and then starts using
    RandomOpponentSelector.
    """
    def __init__(self, switch_rating = 2400):
        # Store the rating at which selection strategy is switched
        self.switch_rating = switch_rating

        # Boolean to check if the specified rating has been reached 
        self.switch = False

        # Define selectors
        self.random_selector = RandomOpponentSelector()
        self.highest_selector = HighestRatedOpponentSelector()

    def pick_next(self, player: Player) -> str:
        if self.switch:
            return self.random_selector.pick_next(player)
        else:
            return self.highest_selector.pick_next(player)

    def check_rating(self, player: Player) -> None:
        """
        Checks the rating of the current player to determine if player selection strategy needs
        to be switched
        """
        rating = player.get_rapid_rating()
        self.switch = rating > self.switch_rating

    
class HigherLowerSelector(PlayerSelector):
    """
    Uses the RandomHigherRatedSelector selector until a specified rating, and then starts using
    RandomLowerRaterdSelector.
    """
    def __init__(self, high_rating = 2400, low_rating = 600):
        # Store the ratings at which selection strategy is switched
        self.high_rating =  high_rating
        self.low_rating = low_rating

        # Boolean to check if the specified rating has been reached 
        self.mode = 'higher'

        # Define selectors
        self.higher_selector = RandomHigherRatedOpponentSelector()
        self.lower_selector = RandomLowerRatedOpponentSelector()

    def pick_next(self, player: Player) -> str:
        # Check if mode needs to be switched
        self.check_rating(player)

        # Pick next player
        if self.mode == 'higher':
            return self.higher_selector.pick_next(player)
        else:
            return self.lower_selector.pick_next(player)

    def check_rating(self, player: Player) -> None:
        """
        Checks the rating of the current player to determine if player selection strategy needs
        to be switched
        """
        rating = player.get_rapid_rating()
        if rating > self.high_rating and self.mode == 'higher':
            self.mode = 'lower'

        elif rating < self.low_rating and self.mode == 'lower':
            self.mode = 'higher'
