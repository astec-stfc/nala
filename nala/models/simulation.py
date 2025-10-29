from pydantic import PositiveInt, PositiveFloat, SerializeAsAny
from typing import Literal, Any, Dict
from .baseModels import IgnoreExtra


class ApertureElement(IgnoreExtra):
    """Physical info model."""

    number_of_elements: int | None = None
    """Number of aperture elements"""

    horizontal_size: PositiveFloat = 1.0
    """Horizontal aperture size [m]"""

    vertical_size: PositiveFloat = 1.0
    """Vertical aperture size [m]"""

    shape: Literal["elliptical", "planar", "circular", "rectangular", "scraper"] | None = None
    """Aperture shape"""

    radius: float | None = None
    """Radius of aperture"""

    negative_extent: float | None = None
    """Longitudinal start position of an aperture"""

    positive_extent: float | None = None
    """Longitudinal end position of an aperture"""


class SimulationElement(IgnoreExtra):
    field_definition: SerializeAsAny[Any] = None
    """String pointing to field definition"""

    wakefield_definition: SerializeAsAny[Any] = None
    """String pointing to wakefield definition"""

    field_reference_position: Literal["start", "middle", "end"] = "middle"
    """Reference position for field file"""

    scale_field: int | float | bool = False
    """Flag indicating whether to scale the field from the field file"""


class MagnetSimulationElement(SimulationElement):
    n_kicks: int = 4
    """Number of kicks for tracking through the quad"""

    smooth: int | float | None = 2
    """Number of points to smooth the field map [ASTRA only]"""

    edge_field_integral: float = 0.5
    """Edge field integral for fringes"""

    edge1_effects: int = 1
    """Flag to indicate whether entrance edge effects are included"""

    edge2_effects: int = 1
    """Flag to indicate whether exit edge effects are included"""

    sr_enable: bool = True
    """Flag to enable SR calculations"""

    integration_order: int = 4
    """Runge-Kutta integration order"""

    nonlinear: int = 1
    """Flag to indicate whether to perform nonlinear calculations"""

    smoothing_half_width: int = 1
    """Half-width for smoothing"""

    edge_order: int = 2
    """Matrix order for edges"""

    csr_bins: int = 100
    """Number of CSR bins"""

    deltaL: float = 0.0
    """Delta length"""

    csr_enable: bool = True
    """Flag to indicate whether CSR is enabled"""

    isr_enable: bool = True
    """Flag to indicate whether ISR is enabled"""

    field_amplitude: float = 0.0


class DriftSimulationElement(SimulationElement):
    lsc_interpolate: int = 1
    """Flag to allow for interpolation of computed longitudinal space charge wake.
    See `Elegant manual LSC drift`_
    
    .. _Elegant manual LSC drift: https://ops.aps.anl.gov/manuals/elegant_latest/elegantsu168.html#x179-18000010.58
    """

    csr_enable: bool = True
    """Enable CSR drift calculations"""

    lsc_enable: bool = True
    """Enable LSC drift calculations"""

    use_stupakov: int = 1
    """Use Stupakov formula; see `Elegant manual LSC drift`_"""

    csrdz: PositiveFloat = 0.01
    """Step size for CSR calculations"""

    lsc_bins: PositiveInt = 20
    """Number of bins for LSC calculations"""

    lsc_high_frequency_cutoff_start: float = -1.0
    """Spatial frequency at which smoothing filter begins. If not positive, no frequency filter smoothing is done. 
    See `Elegant manual LSC drift`_
    """

    lsc_high_frequency_cutoff_end: float = -1.0
    """Spatial frequency at which smoothing filter is 0. See `Elegant manual LSC drift`_"""

    lsc_low_frequency_cutoff_start: float = -1.0
    """Highest spatial frequency at which low-frequency cutoff filter is zero. See `Elegant manual LSC drift`_"""

    lsc_low_frequency_cutoff_end: float = -1.0
    """Lowest spatial frequency at which low-frequency cutoff filter is 1. See `Elegant manual LSC drift`_"""


class DiagnosticSimulationElement(SimulationElement):
    output_filename: str | None = None
    """Output filename for the diagnostic"""


class PlasmaSimulationElement(SimulationElement):
    wakefield_model: Literal["quasistatic_2d"] | None = None
    """Wakefield model (Wake-T); possible values: 
    'blowout', 'custom_blowout', 'focusing_blowout', 'cold_fluid_1d' and 'quasistatic_2d'; if None, no
    wakefields are computed.
    # TODO add more of these and check which we support
    """

    required_attrs: Dict = {
        "common": [
            "length",
        ],
        "quasistatic_2d": [
            "density",
            "r_max",
            "n_longitudinal",
            "n_radial",
            "min_longitudinal_position",
            "max_longitudinal_position"
        ],
    }

    bunch_pusher: Literal["rk4", "boris"] = "boris"
    """Pusher used to evolve particles in time in the plasma [Wake-T]; possible values:
    'rk4', 'boris'; see `Wake-T pusher`_

    .. _Wake-T pusher: https://github.com/AngelFP/Wake-T/tree/dev/wake_t/particles/push
    """

    dt_bunch: float | Literal["auto"] = "auto"
    """The time step for evolving the particle bunches. If 'auto', set to dt=T/(10*2*pi) with T
    the plasma period.
    """

    n_out: int = 1
    """Number of times to dump the particle distribution during the plasma stage."""

    min_longitudinal_position: float = 0
    """Minimum longitudinal position [metres] up to which
    plasma wakefield will be calculated. Converted to boosted co-ordinates for Wake-T during 
    simulation setup."""

    max_longitudinal_position: float = 0
    """Maximum longitudinal position [metres] up to which
        plasma wakefield will be calculated. Converted to boosted co-ordinates for Wake-T during
        simulation setup."""

    n_longitudinal: int = 0
    """Number of grid points in the longitudinal direction"""

    n_radial: int = 0
    """Number of grid points in the radial direction"""

    plasma_particles_per_cell: int = 2
    """Number of plasma particles per cell; 2 by default"""

    r_max: float = 0
    """Radial extent of the simulation box [meters]"""

    r_max_plasma: float | None = None
    """Maximum radial extension of the plasma column; set to `r_max` if None"""

    dz_fields: float | None = None
    """Determines how often the plasma wakefields should be updated; 
        `max_longitudinal_position`-`min_longitudinal_position` by default"""

    plasma_pusher: Literal["rk4", "boris"] = "boris"
    """Pusher used to evolve the plasma in time [Wake-T]; possible values:
    'rk4', 'boris'; see `Wake-T pusher`_

    .. _Wake-T pusher: https://github.com/AngelFP/Wake-T/tree/dev/wake_t/particles/push
    """


class RFCavitySimulationElement(SimulationElement):
    field_amplitude: float = 0
    """Cavity field amplitude"""

    t_column: str | None = None
    """t column in wake file"""

    z_column: str | None = None
    """z column in wake file"""

    wx_column: str | None = None
    """Wx column in wake file"""

    wy_column: str | None = None
    """Wy column in wake file"""

    wz_column: str | None = None
    """Wz column in wake file"""

    change_p0: int = 1
    """Flag to indicate whether cavity is changing momentum"""

    n_kicks: int = 0
    """Number of cavity kicks to apply"""

    end1_focus: int = 1
    """Apply entrance focusing"""

    end2_focus: int = 1
    """Apply exit focusing"""

    body_focus_model: str = "SRS"
    """Cavity focusing model"""

    lsc_bins: int = 100
    """Number of longitudinal space charge bins"""

    current_bins: int = 0
    """Number of current bins"""

    interpolate_current_bins: int = 1
    """Flag to indicate whether to interpolate during current histogram"""

    smooth_current_bins: int = 1
    """Flag to indicate whether to smooth the current histogram"""

    smooth: int | None = None
    """Smoothing parameter"""

    ez_peak: float | None = None
    """Peak longitudinal electric field"""

    field_file_name: str | None = None
    """Cavity field file name"""

    wakefile: str | None = None
    """Name of wake file"""

    zwakefile: str | None = None
    """Name of longitudinal wake file"""

    trwakefile: str | None = None
    """Name of transverse wake file"""


class WakefieldSimulationElement(SimulationElement):
    allow_long_beam: bool = True
    bunched_beam: bool = False
    change_momentum: bool = True
    factor: float = 1
    field_amplitude: float = 0
    interpolate: bool = True
    scale_kick: float = 1
    t_column: str | None = None
    """t column in wake file"""

    z_column: str | None = None
    """z column in wake file"""

    wx_column: str | None = None
    """Wx column in wake file"""

    wy_column: str | None = None
    """Wy column in wake file"""

    wz_column: str | None = None
    """Wz column in wake file"""
    scale_field_ex: float = 0.0
    """x-component of the longitudinal direction vector."""

    scale_field_ey: float = 0.0
    """y-component of the longitudinal direction vector."""

    scale_field_ez: float = 1.0
    """z-component of the longitudinal direction vector."""

    scale_field_hx: float = 1.0
    """x-component of the horizontal direction vector."""

    scale_field_hy: float = 0.0
    """y-component of the horizontal direction vector."""

    scale_field_hz: float = 0.0
    """z-component of the horizontal direction vector."""

    equal_grid: float = 0.66
    """If 1.0 an equidistant grid is set up, if 0.0 a grid with equal charge per grid cell is
    employed. Values between 1.0 and 0.0 result in intermediate binning based on
    a linear combination of the two methods."""

    interpolation_method: int = 2
    """Interpolation method for ASTRA: 0 = rectangular, 1 = triangular, 2 = Gaussian."""
    smooth: float = 0.25
    """Smoothing parameter for Gaussian interpolation."""

    subbins: int = 10
    """Sub binning parameter."""

class TwissMatchSimulationElement(IgnoreExtra):
    beta_x: float
    """Horizontal beta"""

    beta_y: float
    """Vertical beta"""

    alpha_x: float
    """Horizontal alpha"""

    alpha_y: float
    """Vertical alpha"""

    eta_x: float = 0.0
    """Horizontal dispersion"""

    eta_y: float = 0.0
    """Vertical dispersion"""

    eta_xp: float = 0.0
    """Horizontal dispersion derivative"""

    eta_yp: float = 0.0
    """Vertical dispersion derivative"""

    from_beam: bool = True
    """If `True`, compute transformation from tracked beam properties instead of Twiss parameters"""