from typing import List, Dict

from nala.models.element import (
    Element,
    Magnet,
    Solenoid,
    Dipole,
    RFCavity,
    RFDeflectingCavity,
    Drift,
    Aperture,
    Diagnostic,
    Marker,
    Plasma,
    Laser,
)

from .base import BaseElementTranslator
from .magnet import MagnetTranslator, SolenoidTranslator, DipoleTranslator
from .cavity import RFCavityTranslator
from .drift import DriftTranslator
from .diagnostic import DiagnosticTranslator
from .aperture import ApertureTranslator
from .plasma import PlasmaTranslator
from .laser import LaserTranslator

def translate_elements(
        elements: List[Element],
        master_lattice_location: str = None,
        directory: str = '.',
) -> Dict[str, BaseElementTranslator]:
    elem_dict = {}
    for elem in elements:
        if isinstance(elem, Magnet):
            if isinstance(elem, Solenoid):
                translator = SolenoidTranslator
            elif isinstance(elem, Dipole):
                translator = DipoleTranslator
            else:
                translator = MagnetTranslator
        elif type(elem) in [RFCavity, RFDeflectingCavity]:
            translator = RFCavityTranslator
        elif isinstance(elem, Drift):
            translator = DriftTranslator
        elif isinstance(elem, Diagnostic) or isinstance(elem, Marker):
            translator = DiagnosticTranslator
        elif isinstance(elem, Aperture):
            translator = ApertureTranslator
        elif isinstance(elem, Plasma):
            translator = PlasmaTranslator
        elif isinstance(elem, Laser):
            translator = LaserTranslator
        else:
            translator = BaseElementTranslator
        elem_dict.update({elem.name: translator.model_validate(elem.model_dump())})
        elem_dict[elem.name].master_lattice_location = master_lattice_location
        elem_dict[elem.name].directory = directory
    return elem_dict