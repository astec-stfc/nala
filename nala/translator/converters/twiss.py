from .base import BaseElementTranslator
from nala.models.simulation import TwissMatchSimulationElement

class TwissMatchTranslator(BaseElementTranslator):
    """
    Translator class for converting a :class:`~nala.models.element.TwissMatch` element instance into a string or
    object that can be understood by various simulation codes.
    """

    simulation: TwissMatchSimulationElement
    """Twiss match simulation element"""