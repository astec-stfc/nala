from .base import BaseElementTranslator
from nala.models.simulation import DiagnosticSimulationElement

class DiagnosticTranslator(BaseElementTranslator):
    simulation: DiagnosticSimulationElement

    directory: str = ""

    def to_elegant(self) -> str:
        self.start_write()
        if not self.simulation.output_filename:
            self.simulation.output_filename = f"\"{self.directory}/{self.name}.SDDS\""
        return super().to_elegant()

    def to_csrtrack(self, n: int) -> str:
        """
        Writes the screen element string for CSRTrack.

        Parameters
        ----------
        n: int
            Modulator index

        Returns
        -------
        str
            String representation of the element for CSRTrack
        """
        z = self.physical.middle.z
        return (
                """quadrupole{\nposition{rho="""
                + str(z)
                + """, psi=0.0, marker=screen"""
                + str(n)
                + """a}\nproperties{strength=0.0, alpha=0, horizontal_offset=0,vertical_offset=0}\nposition{rho="""
                + str(z + 1e-6)
                + """, psi=0.0, marker=screen"""
                + str(n)
                + """b}\n}\n"""
        )