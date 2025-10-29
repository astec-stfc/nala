import numpy as np
from scipy.constants import speed_of_light, pi
from pydantic import (
    BaseModel,
    model_serializer,
    Field,
    field_validator,
    NonNegativeInt,
    create_model,
    NonNegativeFloat,
    computed_field,
)
from .baseModels import IgnoreExtra, T

class PlasmaElement(IgnoreExtra):
    """Plasma model."""

    density: float = Field(gt=0)
    """Plasma density in m^-3"""

    species: str = "electron"
    """Plasma species (e.g., 'electron', 'proton', etc.)
    # TODO make these literals when we have a list of supported species"""

    ramp_up: float = Field(ge=0, default=0.001)
    """Plasma ramp length at entrance [metres]."""

    plateau: float = Field(ge=0, default=0.001)
    """Plasma plateau length [metres]."""

    ramp_down: float = Field(ge=0, default=0.001)
    """Plasma ramp length at exit [metres]."""

    ramp_decay_length: float = Field(ge=0, default=0.001)
    """Plasma decay length [metres]."""

    density_profile: bool = False
    """Density profile function; if False, a flat profile is used; if True, use
     the :func:`~_density_profile` method to calculate the density profile based on
     `ramp_up`, `plateau`, `ramp_down` and `ramp_decay_length`. Only linear profiles """

    parabolic_coefficient: float = 0
    """Parabolic coefficient for density profile"""