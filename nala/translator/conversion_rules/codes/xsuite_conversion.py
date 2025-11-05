from xtrack.beam_elements import Solenoid as Solenoid_xs
from xtrack.beam_elements import Bend as Bend_xs
from xtrack.beam_elements import DipoleEdge as DipoleEdge_xs
from xtrack.beam_elements import Quadrupole as Quadrupole_xs
from xtrack.beam_elements import Sextupole as Sextupole_xs
from xtrack.beam_elements import Octupole as Octupole_xs
from xtrack.beam_elements import Drift as Drift_xs
from xtrack.beam_elements import NonLinearLens as NonLinearLens_xs
from xtrack.beam_elements import Cavity as Cavity_xs
from xtrack.beam_elements import UniformSolenoid as UniformSolenoid_xs
from xtrack.beam_elements import Multipole as Multipole_xs
from xtrack.beam_elements import Marker as Marker_xs
from xtrack.monitors import ParticlesMonitor as ParticlesMonitor_xs

from nala.models.element import (
    Dipole,
    Solenoid,
    Quadrupole,
    Sextupole,
    Octupole,
    RFCavity,
    Drift,
    Solenoid,
    NonLinearLens,
    Magnet,
    Marker,
)

xsuite_conversion_rules_reverse = {
    Bend_xs: Dipole,
    DipoleEdge_xs: Marker,
    Solenoid_xs: Solenoid,
    Quadrupole_xs: Quadrupole,
    Sextupole_xs: Sextupole,
    Octupole_xs: Octupole,
    Cavity_xs: RFCavity,
    Drift_xs: Drift,
    UniformSolenoid_xs: Solenoid,
    NonLinearLens_xs: NonLinearLens,
    Multipole_xs: Magnet,
    Marker_xs: Marker,
}

xsuite_conversion_rules = {
    "Dipole": Bend_xs,
    "Solenoid": Solenoid_xs,
    "Quadrupole": Quadrupole_xs,
    "Sextupole": Sextupole_xs,
    "Octupole": Octupole_xs,
    "Beam_Position_Monitor": ParticlesMonitor_xs,
    "Beam_Arrival_Monitor": Drift_xs,
    "Bunch_Length_Monitor": Drift_xs,
    "Screen": ParticlesMonitor_xs,
    "Marker": ParticlesMonitor_xs,
    "Rcollimator": Drift_xs,
    "Collimator": Drift_xs,
    "Monitor": Marker_xs,
    "Wall_Current_Monitor": Drift_xs,
    "Integrated_Current_Transformer": Drift_xs,
    "Faraday_Cup": Drift_xs,
    "RFCavity": Cavity_xs,
    "RFDeflectingCavity": Cavity_xs,
    "Aperture": Drift_xs,
    "Shutter": Drift_xs,
    "Valve": Drift_xs,
    "Bellows": Drift_xs,
    "Cleaner": Drift_xs,
    "Drift": Drift_xs,
    "NonLinearLens": NonLinearLens_xs,
    "Combined_Corrector": Bend_xs,
    "Horizontal_Corrector": Bend_xs,
    "Vertical_Corrector": Bend_xs,
    "Scatter": Marker_xs,
    "APContour": Marker_xs,
    "Center": Marker_xs,
    "FEL_Modulator": Drift_xs,
    "Wiggler": Drift_xs,
    "Charge": Marker_xs,
    "Wakefield": Marker_xs,
    "Watch_Point": ParticlesMonitor_xs,
    "Laser": Drift_xs,
}