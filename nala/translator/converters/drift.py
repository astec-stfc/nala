from .base import BaseElementTranslator
from nala.models.simulation import DriftSimulationElement

class DriftTranslator(BaseElementTranslator):
    simulation: DriftSimulationElement

    def to_elegant(self) -> str:
        self.start_write()
        if self.simulation.csr_enable:
            self.hardware_type = "csrdrift"
        elif self.simulation.lsc_enable:
            self.hardware_type = "lscdrift"
        return super().to_elegant()
