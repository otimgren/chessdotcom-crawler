"""
Class for storing info about a player
"""
from dataclasses import dataclass

@dataclass
class Player:
    """
    Class for representing Players on chess.com (used as a data cointainer mostly)
    """
    id : str # Can be player id or username

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
    

