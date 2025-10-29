from typing import Any, List
from .base import BaseElementTranslator
from nala.models.laser import LaserElement


class LaserTranslator(BaseElementTranslator):
    laser: LaserElement

    supported_pulses: List = [
        'gaussian',
        'laguerre-gaussian',
        'flattened-gaussian',
        # 'file'
    ]

    additional_attrs: List = [
        "focal_position",
        "wavelength",
        "cep_phase",
        "polarization",
    ]

    def to_wake_t(self) -> Any:
        """
        Create a Wake-T laser element object based on the attributes of this element.

        Returns
        -------
        wake_t.LaserPulse
            Wake-T laser element object

        Raises
        ------
        ValueError
            If the laser model is not supported; note that not all models are implemented yet
        """
        from wake_t.physics_models.laser.laser_pulse import (
            GaussianPulse,
            LaguerreGaussPulse,
            FlattenedGaussianPulse,
            # SummedPulse,
            # OpenPMDPulse,
        )
        additional_dict = {
            self._convertKeyword_WakeT(param): getattr(self.laser, param) for param in self.additional_attrs
        }
        if self.profile_type == "gaussian":
            obj = GaussianPulse(
                self.laser.initial_position,
                self.laser.amplitude,
                self.laser.waist,
                self.laser.pulse_duration_fwhm,
                **additional_dict,
            )
        elif self.profile_type == "laguerre-gaussian":
            obj = LaguerreGaussPulse(
                self.laser.initial_position,
                self.laser.laguerre_polynomial_order_p,
                self.laser.amplitude,
                self.laser.waist,
                self.laser.pulse_duration_fwhm,
                **additional_dict,
            )
        elif self.profile_type == "flattened-gaussian":
            obj = FlattenedGaussianPulse(
                self.laser.initial_position,
                self.laser.amplitude,
                self.laser.waist,
                self.laser.pulse_duration_fwhm,
                N=self.laser.flatness,
                **additional_dict,
            )
        else:
            raise ValueError(
                f"Invalid laser profile type {self.laser.profile_type}. "
                f"Supported models are {self.supported_pulses}."
            )
        return obj