"""
Class for storing info about a player
"""
from dataclasses import dataclass
from enum import Enum

class TimeControl(Enum):
    """
    Enumerator for different chess time controls
    """
    blitz = 'blitz'
    bullet = 'bullet'
    rapid = 'rapid'
    daily = 'daily'

@dataclass
class Player:
    """
    Class for representing Players on chess.com (used as a data cointainer mostly)
    """
    id : str # Can be player id or username

    def get_id(self) -> str:
        """
        Get the user id of the player
        """
        return self.profile["player_id"]

    def get_username(self) -> str:
        """
        Get the username of the player
        """
        return self.profile["username"]

    def get_jointime(self) -> str:
        """
        Get the timestamp of when the player joined chess.com
        """
        return self.profile["joined"]

    def get_status(self) -> str:
        """
        Get the premium status of a player
        """
        return self.profile["status"]

    def get_n_games(self, time_ctrl: TimeControl) -> int:
        """
        Gets the number of games played with the specified time control.
        """
        key = 'chess_' + time_ctrl.value
        try:
            wins = self.basic_stats[key]['record']['win']
            losses = self.basic_stats[key]['record']['loss']
            draws = self.basic_stats[key]['record']['draw']

            return wins + losses + draws

        except KeyError as e:
            # print(e)
            # print(f"No {time_ctrl.value} games for {player.id}")
            return 0

    def get_rating(self, time_ctrl: TimeControl) -> int:
        """
        Gets the rating of a player for the specified time control
        """
        key = 'chess_' + time_ctrl.value
        try:
            rating = self.basic_stats[key]['last']['rating']
            return rating

        except KeyError as e:
            # print(e)
            # print(f"No {time_ctrl.value} games for {player.id}")
            return None

    def get_best_puzzle_rush(self) -> int:
        """
        Get the puzzle rush record of the player
        """
        try:
            return self.basic_stats['puzzle_rush']['best']['score']
        except KeyError:
            return 0

    def get_n_puzzles(self) -> int:
        """
        Gets the number of puzzles attempted by the player
        """
        return self.puzzle_data.n

    def get_t_puzzles(self) -> int:
        """
        Gets the number of seconds spent on puzzle training by player
        """
        return self.puzzle_data.t

    def get_puzzle_rating(self) -> int:
        """
        Gets the current puzzle rating of the player
        """
        # Check that data exists for puzzles
        if len(self.puzzle_data.ratings_df.rating) < 1:
            return None

        return self.puzzle_data.ratings_df.rating.iloc[-1]

    def get_rapid_rating(self) -> int:
        """
        Gets the rating of a player for the specified time control
        """
        key = 'chess_rapid' 
        try:
            rating = self.basic_stats[key]['last']['rating']
            return rating

        except KeyError as e:
            # print(e)
            # print(f"No {time_ctrl.value} games for {player.id}")
            return 0
    

