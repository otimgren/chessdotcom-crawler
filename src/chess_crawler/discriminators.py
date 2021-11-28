"""
Classes for checking if a player fullfils the criteria to be saved in the database
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from .player import Player

class Discriminator(ABC):
    """
    Abstract parent class for discriminators. These are used to decide if a player's data shoud be
    saved.
    """
    @abstractmethod
    def should_save(self, player: Player) -> bool:
        """
        Determines if player data should be saved based on some criterion.
        """
        ...

@dataclass
class DiscriminatorPipeline:
    """
    Contains many discriminators and runs them in sequence, testing if all return True
    """
    discriminators: List[Discriminator]

    def should_save(self, player: Player) -> bool:
        for discr in self.discriminators:
            if not discr.should_save(player):
                return False

        return True

@dataclass
class NGamesDiscriminator(Discriminator):
    """
    Requires at least N rapid games to return true
    """
    N: int = 100

    def should_save(self, player: Player) -> bool:
        return player.rapid_data.n > self.N

class CheaterDiscriminator(Discriminator):
    """
    Don't save cheaters
    """
    def should_save(self, player: Player) -> bool:
        return 'closed' not in player.profile["status"] 