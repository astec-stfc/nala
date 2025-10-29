import numpy as np
from scipy.constants import pi, c, e, m_e, epsilon_0
from typing import Any
from warnings import warn
from .base import BaseElementTranslator
from nala.models.plasma import PlasmaElement
from nala.models.simulation import PlasmaSimulationElement
from nala.models.laser import LaserElement
from .laser import LaserTranslator

class PlasmaTranslator(BaseElementTranslator):
    plasma: PlasmaElement

    simulation: PlasmaSimulationElement

    laser: LaserElement | None

    def to_wake_t(self) -> Any:
        """
        Create a Wake-T plasma element object based on the attributes of this element.

        If a `laser` sub-element is defined, it is also converted to a Wake-T laser object and
        added to the plasma element; if two laser sub-elements are defined, they are summed together
        using the :class:`~wake_t.physics_models.laser.laser_pulse.SummedPulse` class.

        Returns
        -------
        wake_t.PlasmaStage
            Wake-T plasma element object

        Raises
        ------
        ValueError
            If the wakefield model is not supported; note that not all models are implemented yet
        """
        from wake_t.physics_models.laser.laser_pulse import (
            SummedPulse,
        )
        from ..conversion_rules.codes import wake_t_conversion

        type_conversion_rules_Wake_T = wake_t_conversion.wake_t_conversion_rules
        if self.simulation.wakefield_model is None:
            warn(
                "No wakefield model defined; no plasma wakefields will be computed."
                 f"Supported models are {list(self.simulation.required_attrs.keys())[1:]}."
            )
        elif self.simulation.wakefield_model not in self.simulation.required_attrs.keys():
            raise ValueError(
                f"Invalid wakefield model {self.wakefield_model}. "
                f"Supported models are {list(self.simulation.required_attrs.keys())[1:]}."
            )
        commondict = {
            self._convertKeyword_WakeT(param): getattr(self, param) for param in
            self.simulation.required_attrs["common"]
        }
        modeldict = {self._convertKeyword_WakeT(param): getattr(self, param) for param in
                     self.simulation.required_attrs[self.simulation.wakefield_model]}
        if self.plasma.density_profile:
            modeldict["density"] = self._density_profile
        else:
            modeldict["density"] = float(self.plasma.density)
        elemdict = modeldict | commondict
        lasers = []
        if isinstance(self.laser, LaserElement):
            laser_translator = LaserTranslator.model_validate(self.model_dump())
            lasers.append(laser_translator.to_wake_t())
        if len(lasers) == 1:
            elemdict.update({"laser": lasers[0]})
        elif len(lasers) == 2:
            elemdict.update({"laser": SummedPulse(lasers[0], lasers[1])})
        elif len(lasers) > 2:
            warn("More than two laser sub-elements found; only the first two will be used.")
            elemdict.update({"laser": SummedPulse(lasers[0], lasers[1])})
        obj = type_conversion_rules_Wake_T[
            self.hardware_type
        ](wakefield_model=self.simulation.wakefield_model, **elemdict)
        return obj

    # Density function.
    def _density_profile(self, z: float) -> np.ndarray:
        """
        Define plasma density as a function of length.
        This takes the :attr:`~length` of the plasma element and calculates the density profile based
        on the :attr:`~ramp_up`, :attr:`~plateau`, :attr:`~ramp_down` and :attr:`~ramp_decay_length` attributes.

        Parameters
        ----------
        n_steps : int, optional
            Number of steps to use for the density profile, by default 1000

        Returns
        -------
        np.ndarray
            Array of length `n_steps` containing the density profile in m^-3
        """
        # Allocate relative density array.
        if self.plasma.plateau <= 0:
            raise ValueError("Plateau length must be positive for density profile.")
        if self.plasma.ramp_up < 0 or self.plasma.ramp_down < 0 or self.plasma.ramp_decay_length <= 0:
            raise ValueError(
                "Ramp lengths must be non-negative and ramp decay length must be positive for density profile."
            )
        n = np.ones_like(z)
        # Add upramp.
        n = np.where(z < self.plasma.ramp_up, 1 / (1 + (self.plasma.ramp_up - z) / self.plasma.ramp_decay_length) ** 2, n)
        # Add downramp.
        try:
            n = np.where(
                (z > self.plasma.ramp_up + self.plasma.plateau) & (z <= self.plasma.ramp_up + self.plasma.plateau + self.plasma.ramp_down),
                1 / (1 + (z - self.plasma.ramp_up - self.plasma.plateau) / self.plasma.ramp_decay_length) ** 2,
                n,
            )
        except ZeroDivisionError:
            n = np.where(
                (z > self.plasma.ramp_up + self.plasma.plateau) & (z <= self.plasma.ramp_up + self.plasma.plateau + self.plasma.ramp_down),
                1,
                n,
            )
        # Make zero after downramp.
        n = np.where(z > self.plasma.ramp_up + self.plasma.plateau + self.plasma.ramp_down, 1e-6, n)
        # Return absolute density.
        return n * self.plasma.density
