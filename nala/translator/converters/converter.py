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
    Wiggler,
    Combined_Corrector,
    Horizontal_Corrector,
    Vertical_Corrector,
    NonLinearLens,
    TwissMatch,
)

from .base import BaseElementTranslator
from .magnet import (
    MagnetTranslator,
    SolenoidTranslator,
    DipoleTranslator,
    WigglerTranslator,
    NonLinearLensTranslator,
)
from .cavity import RFCavityTranslator
from .drift import DriftTranslator
from .diagnostic import DiagnosticTranslator
from .aperture import ApertureTranslator
from .plasma import PlasmaTranslator
from .laser import LaserTranslator
from .twiss import TwissMatchTranslator


def translate_elements(
        elements: List[Element],
        master_lattice_location: str = None,
        directory: str = '.',
) -> Dict[str, BaseElementTranslator]:
    """
    Function for translating a list of elements into their respective Translator classes.

    Parameters
    ----------
    elements: List[Element]
        List of :class:`~nala.models.element.Element` objects.
    master_lattice_location: str
        Directory containing lattice/data files including field/wakefield files.
    directory:
        Directory to which files will be written.

    Returns
    -------
    Dict[str, BaseElementTranslator]
        Dictionary of :class:`~nala.translator.converters.base.BaseElementTranslator` objects, keyed
        by their original name.
    """
    elem_dict = {}
    for elem in elements:
        if isinstance(elem, Magnet):
            if isinstance(elem, Solenoid):
                translator = SolenoidTranslator
            elif isinstance(elem, Dipole) and not type(elem) in [
                Combined_Corrector,
                Horizontal_Corrector,
                Vertical_Corrector,
            ]:
                translator = DipoleTranslator
            elif isinstance(elem, Wiggler):
                translator = WigglerTranslator
            elif isinstance(elem, NonLinearLens):
                translator = NonLinearLensTranslator
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
        elif isinstance(elem, TwissMatch):
            translator = TwissMatchTranslator
        else:
            translator = BaseElementTranslator
        elem_dict.update({elem.name: translator.model_validate(elem.model_dump())})
        elem_dict[elem.name].master_lattice_location = master_lattice_location
        elem_dict[elem.name].directory = directory
    return elem_dict