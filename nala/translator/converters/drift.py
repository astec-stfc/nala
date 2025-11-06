from .base import BaseElementTranslator
from nala.models.simulation import DriftSimulationElement

class DriftTranslator(BaseElementTranslator):
    """
    Translator class for converting a :class:`~nala.models.element.Diagnostic` element instance into a string or
    object that can be understood by various simulation codes.
    """

    simulation: DriftSimulationElement
    """Drift simulation attributes."""

    def to_elegant(self) -> str:
        """
        Generates a string representation of the object's properties in the Elegant format.
        If `element.simulation.csr_enable`, a `CSRDRIFT` is written;
        if `element.simulation.lsc_enable`, a `LSCDRIFT` is written;
        else a `DRIFT` is written.

        See `Elegant manual LSC drift`_ and `Elegant manual CSR drift`_

        .. _Elegant manual CSR drift: https://ops.aps.anl.gov/manuals/elegant_latest/elegantsu133.html#x144-14300010.23

        Returns
        -------
        str
            A formatted string representing the object's properties in Elegant format.
        """
        self.start_write()
        if self.simulation.csr_enable:
            self.hardware_type = "csrdrift"
        elif self.simulation.lsc_enable:
            self.hardware_type = "lscdrift"
        return super().to_elegant()
