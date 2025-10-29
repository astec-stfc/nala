from pydantic import Field, computed_field
from typing import Type, Union, Literal
from warnings import warn
from scipy.constants import pi, c, e, m_e, epsilon_0
import numpy as np

from .baseModels import IgnoreExtra, T


class LaserElement(IgnoreExtra):
    """Laser info model."""

    initial_position: float = 0
    """Initial position of the laser pulse [m]"""

    waist: float = Field(ge=0, default=0)
    """Laser waist [m]"""

    wavelength: float = Field(gt=0)
    """Laser wavelength [m]"""

    pulse_energy: float = Field(gt=0)
    """Laser pulse energy [J]"""

    pulse_duration_fwhm: float = Field(gt=0)
    """Pulse duration FWHM [s]"""

    focal_position: float = 0.0
    """Focal position of the laser pulse [m], optional"""

    cep_phase: float = 0
    """CEP phase [radians]"""

    polarization: Literal["linear", "circular", "elliptical"] | None = None
    """Laser polarization: 'linear', 'circular', 'elliptical'"""

    profile_type: Literal['gaussian', 'laguerre-gaussian', 'flattened-gaussian', 'file'] = "gaussian"
    """Laser profile type [str]: 'gaussian', 'laguerre-gaussian', 'flattened-gaussian', 'file'"""

    laguerre_polynomial_order_p: int = 0
    """Order of Laguerre-Gaussian polynomial mode, if profile_type is 'laguerre-gaussian'"""

    flatness: int = 6
    """Flatness parameter, if profile_type is 'flattened-gaussian'.
    Default: N=6; somewhat close to an 8th order super-gaussian."""

    @computed_field
    @property
    def amplitude(self) -> float:
        """
        Laser amplitude: ((e*lambda0)/(pi*m_e*c**2*w0)) * np.sqrt( E/(pi*epsilon_0*c*tau_FWHM) )

        Returns
        -------
        float
            Laser amplitude (dimensionless)

        Raises
        ------
        ValueError
            If any of the requires parameters are not set or non-positive
        """
        if any([self.wavelength, self.waist, self.pulse_energy, self.pulse_duration_fwhm]) <= 0:
            warn("Wavelength, waist, pulse enegy and pulse duration must be positive "
                 "to compute laser amplitude.")
            return 0
        return ((e * self.wavelength) / (pi * m_e * c ** 2 * self.waist)) * np.sqrt(
            self.pulse_energy / (pi * epsilon_0 * c * self.pulse_duration_fwhm)
        )

    @property
    def angular_frequency(self) -> float:
        """
        Laser angular frequency: 2*pi*c/lambda0

        Returns
        -------
        float
            Laser angular frequency [rad/s]

        Raises
        ------
        ValueError
            If wavelength is not set or non-positive
        """
        if self.wavelength <= 0:
            raise ValueError("Wavelength must be positive to compute laser angular frequency.")
        return 2 * pi * c / self.wavelength


class LaserHalfWavePlateElement(IgnoreExtra):
    """Laser info model."""

    calibration_factor: float = Field()
    pv_type: str = Field(alias="laser_pv_type")

class LaserEnergyMeterElement(IgnoreExtra):
    """Laser info model."""

    calibration_factor: float = Field()
    pv_type: str = Field(alias="laser_pv_type")


class LaserMirrorSense(IgnoreExtra):
    left: float = Field(alias="left_sense")
    right: float = Field(alias="right_sense")
    up: float = Field(alias="up_sense")
    down: float = Field(alias="down_sense")


class LaserMirrorElement(IgnoreExtra):
    """Laser info model."""

    step_max: float = Field()
    sense: LaserMirrorSense
    vertical_channel: Union[int, None] = None
    horizontal_channel: Union[int, None] = None

    @classmethod
    def from_CATAP(cls: Type[T], fields: dict) -> T:
        cls._create_field_class(cls, fields, "sense", LaserMirrorSense)
        return super().from_CATAP(fields)
