from pydantic import Field

from .baseModels import IgnoreExtra


class ElectricalElement(IgnoreExtra):
    """
    Electrical info model.
    """

    minI: float = Field(alias="min_i", default=0)
    """Minimum current that can be set [A]."""

    maxI: float = Field(alias="max_i", default=0)
    """Maximum current that can be set [A]."""

    read_tolerance: float = Field(alias="ri_tolerance", default=0.1)
    """Tolerance on read current [A]."""
