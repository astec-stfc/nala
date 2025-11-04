from typing import Dict, Any
from warnings import warn
import numpy as np

from ...models.elementList import SectionLattice
from ...models.RF import WakefieldElement
from ...models.simulation import WakefieldSimulationElement, DiagnosticSimulationElement
from .cavity import RFCavityTranslator
from .converter import translate_elements
from .diagnostic import DiagnosticTranslator
from .wake import WakefieldTranslator
from .codes.gpt import gpt_ccs, gpt_Zminmax
from ..utils.functions import tw_cavity_energy_gain
from ..utils.fields import field


class SectionLatticeTranslator(SectionLattice):
    directory: str = '.'

    astra_headers: Dict = {}

    csrtrack_headers: Dict = {}

    gpt_headers: Dict = {}

    opal_headers: Dict = {}

    @classmethod
    def from_section(cls, section: SectionLattice) -> "SectionLatticeTranslator":
        return cls.model_validate(
            {
                "name": section.model_copy().name,
                "order": section.model_copy().order,
                "elements": section.model_copy().elements,
                "master_lattice_location": section.model_copy().master_lattice_location
            }
        )

    def to_astra(self) -> str:
        from .codes.astra import section_header_text_ASTRA
        headers = ["&APERTURE", "&CAVITY", "&SOLENOID", "&QUADRUPOLE", "&DIPOLE", "&WAKE"]
        counter = {k: 1 for k in headers}
        written = []
        element_headers = {h: "" for h in headers}
        elem_dict = translate_elements(
            list(self.elements.elements.values()),
            master_lattice_location=self.master_lattice_location,
            directory=self.directory,
        )
        astrastr = ""
        for h in self.astra_headers.values():
            astrastr += h.write_ASTRA()

        for e in elem_dict.values():
            for key, count in counter.items():
                if "&" + e.hardware_type.upper().replace("RF", "").replace("FIELD", "") == key:
                    if key not in written:
                        element_headers[key] += f"{section_header_text_ASTRA[key]} = True\n"
                        written.append(key)
                    element_headers[key] += e.to_astra(n=count)
                    counter[key] += 1
                    try:
                        w = WakefieldTranslator(
                            name=e.name + "_wake",
                            hardware_class="Wakefield",
                            hardware_type="Wakefield",
                            machine_area=e.machine_area,
                            physical=e.physical,
                            cavity=WakefieldElement(cell_length=e.cavity.cell_length, n_cells=e.cavity.n_cells),
                            simulation=WakefieldSimulationElement(
                                wakefield_definition=e.simulation.wakefield_definition),
                            directory=e.directory,
                        )
                        if "&WAKE" not in written:
                            element_headers["&WAKE"] += f"{section_header_text_ASTRA["&WAKE"]} = True\n"
                            written.append("&WAKE")
                        element_headers["&WAKE"] += w.to_astra(n=counter["&WAKE"])
                        counter["&WAKE"] += e.cavity.n_cells
                    except Exception as ex:
                        pass
                else:
                    if not e.hardware_class == "Diagnostic":
                        warn(f"Element of type {e.hardware_type} not supported for ASTRA")
        for k, v in element_headers.items():
            astrastr += k + "\n"
            astrastr += v + "\n"
            astrastr += "/ \n"
        return astrastr

    def to_gpt(self, startz: float, endz: float, Brho: float = 0.0) -> str:
        fulltext = ""
        for header in self.gpt_headers.values():
            fulltext += header.write_GPT()
        elem_dict = translate_elements(
            list(self.elements.elements.values()),
            master_lattice_location=self.master_lattice_location,
            directory=self.directory,
        )
        for i, element in enumerate(list(elem_dict.values())):
            if i == 0:
                ccs = gpt_ccs(
                    name="wcs",
                    position=element.physical.start.model_dump(),
                    rotation=element.physical.global_rotation.model_dump(),
                )
            fulltext += element.to_gpt(Brho, ccs=ccs.name)
            if (
                element.hardware_type.lower() == "rfcavity"
                and isinstance(element.simulation.wakefield_definition, field)
            ):
                w = WakefieldTranslator(
                    name=element.name + "_wake",
                    hardware_class="Wakefield",
                    hardware_type="Wakefield",
                    machine_area=element.machine_area,
                    physical=element.physical,
                    cavity=WakefieldElement(cell_length=element.cavity.cell_length, n_cells=element.cavity.n_cells),
                    simulation=WakefieldSimulationElement(
                        wakefield_definition=element.simulation.wakefield_definition,
                    ),
                    directory=element.directory,
                )
                fulltext += w.to_gpt(Brho, ccs=ccs.name)
            new_ccs = element.ccs
            if not new_ccs.name == ccs.name:
                relpos, relrot = ccs.relative_position(
                    element.physical.middle.model_dump(), element.physical.global_rotation.model_dump()
                )
            else:
                relpos = element.physical.middle.model_dump()
            screen0pos = 0
            ccs = new_ccs
            if element.hardware_class.lower() == "diagnostic":
                fulltext += f'screen({ccs.name_as_str}, "I", {str(relpos[2])}, {ccs.name_as_str});\n'
                # if self.gpt_headers["setfile"].particle_definition == "laser":
        lastelem = list(elem_dict.values())[-1]
        lastscreen = DiagnosticTranslator(
            name="end_screen",
            hardware_class="Diagnostic",
            hardware_type="Diagnostic",
            machine_area=lastelem.machine_area,
            simulation=DiagnosticSimulationElement(output_filename=f"{self.name}_out.gdf"),
            physical=lastelem.physical,
        )
        fulltext += lastscreen.to_gpt(
            Brho, ccs=ccs.name, output_ccs="wcs"
        )
        relpos, relrot = ccs.relative_position(
            lastelem.physical.end.model_dump(), lastelem.physical.global_rotation.model_dump()
        )
        fulltext += f'screen({ccs.name_as_str}, "I", {str(relpos[2])}, {ccs.name_as_str});\n'
        zminmax = gpt_Zminmax(
            ECS='"wcs", "I"',
            zmin=startz - 0.1,
            zmax=endz + 0.1,
        )
        fulltext += zminmax.write_GPT()
        return fulltext

    def to_opal(self, energy: float = 0, breakstr: str="") -> str:
        check_dict = [
            "option",
            "distribution",
            "fieldsolver",
            "beam",
            "track",
            "run",
        ]
        for k in check_dict:
            if k not in self.opal_headers:
                raise KeyError(f"Header {k} must be defined for OPAL.")
        fulltext = ""
        fulltext += self.opal_headers["option"].write_Opal()
        fulltext += f'{breakstr}\n// LATTICE\n'
        zstops = []
        elem_dict = translate_elements(
            list(self.elements.elements.values()),
            master_lattice_location=self.master_lattice_location,
            directory=self.directory,
        )
        written = []
        svals = self.get_s_values(as_dict=True, at_entrance=True)
        for d in elem_dict.values():
            if isinstance(d, RFCavityTranslator):
                if d.structure_type.lower() == "travellingwave":
                    energy += tw_cavity_energy_gain(d)
                else:
                    energy += d.field_amplitude * np.cos(np.pi * d.phase / 180)
            stnew = d.to_opal(sval=svals[d.name], designenergy=energy)
            if len(stnew) > 0:
                written.append(d.name)
                fulltext += d.to_opal(sval=svals[d.name], designenergy=energy)
            zstops.append(d.physical.end.z)
        zstop = max(zstops)
        self.opal_headers["track"].ZSTOP = zstop
        fulltext += "\n" + self.name + ": LINE=("
        for e, element in list(elem_dict.items()):
            if len((fulltext + e).splitlines()[-1]) > 60:
                fulltext += "\n"
            if element.name in written:
                fulltext += e.replace('-', '_') + ", "
        fulltext = (fulltext[:-2] + ");\n")

        fulltext += self.opal_headers["distribution"].write_Opal()
        fulltext += self.opal_headers["fieldsolver"].write_Opal()
        fulltext += self.opal_headers["beam"].write_Opal()
        fulltext += self.opal_headers["track"].write_Opal()
        fulltext += self.opal_headers["run"].write_Opal()
        fulltext += "ENDTRACK;\n\n Quit;\n"
        return fulltext

    def to_elegant(self, charge: float = None) -> str:
        section_with_drifts = self.createDrifts()
        elem_dict = translate_elements(
            section_with_drifts.values(),
            master_lattice_location=self.master_lattice_location,
            directory=self.directory,
        )
        string = ""
        if charge:
            string += f"{self.name}_Q: CHARGE, TOTAL = {charge};\n"

        for d in elem_dict.values():
            string += d.to_elegant()

        string += f"{self.name}: LINE = ("
        if charge:
            string += f"{self.name}_Q, "
        for elem in section_with_drifts.keys():
            string += f"{elem}, "
        string = f"{string[:-2]})" + "\n"
        return string

    def to_genesis(self) -> str:
        section_with_drifts = self.createDrifts()
        elem_dict = translate_elements(
            section_with_drifts.values(),
            master_lattice_location=self.master_lattice_location,
            directory=self.directory,
        )
        string = ""

        for d in elem_dict.values():
            string += d.to_genesis()

        string += f"{self.name}: LINE = " + "{"
        for elem in section_with_drifts.keys():
            string += f"{elem}, "
        string = f"{string[:-2]}" + "};\n"
        return string

    def to_ocelot(self, save=False) -> "MagneticLattice":
        from ocelot.cpbd.magnetic_lattice import MagneticLattice
        from ocelot.cpbd.transformations.second_order import SecondTM
        from ocelot.cpbd.transformations.kick import KickTM
        from ocelot.cpbd.transformations.runge_kutta import RungeKuttaTM
        from ocelot.cpbd.elements import Octupole, Undulator, Marker
        method = {"global": SecondTM, Octupole: KickTM, Undulator: RungeKuttaTM}
        section_with_drifts = self.createDrifts()
        elem_dict = translate_elements(
            section_with_drifts.values(),
            master_lattice_location=self.master_lattice_location,
            directory=self.directory,
        )
        elements = []

        for d in elem_dict.values():
            elements.append(d.to_ocelot())

        maglat = MagneticLattice(elements, method=method)
        if save:
            maglat.save_as_py_file(f"{self.directory}/{self.name}.py")

        return maglat

    def to_cheetah(self, save=False) -> "Segment":
        from cheetah import Segment
        section_with_drifts = self.createDrifts()
        elem_dict = translate_elements(
            section_with_drifts.values(),
            master_lattice_location=self.master_lattice_location,
            directory=self.directory,
        )
        segment = []
        segments = False
        for element in elem_dict.values():
            if not element.subelement:
                elem = element.to_cheetah()
                if elem is not None:
                    segment.append(elem)
                    segments = True
        if segments:
            full_segment = Segment(elements=segment, name=self.name)
        else:
            raise ValueError(f"No cheetah elements added for {self.name}")

        if save:
            full_segment.to_lattice_json(
                filepath=f'{self.directory}/{self.name}.json'
        )

        return full_segment

    def to_xsuite(self, beam_length: int, env: Any = None, particle_ref: Any = None, save=True) -> object:
        import xtrack as xt
        if not isinstance(env, xt.Environment):
            env = xt.Environment()
        section_with_drifts = self.createDrifts()
        elem_dict = translate_elements(
            section_with_drifts.values(),
            master_lattice_location=self.master_lattice_location,
            directory=self.directory,
        )
        line = env.new_line()
        for i, element in enumerate(list(elem_dict.values())):
            if not element.subelement:
                name, component, properties = element.to_xsuite(
                    beam_length=beam_length
                )
                line.append(element.name, component(**properties))
        if isinstance(particle_ref, xt.Particles):
            line.particle_ref = particle_ref
        if save:
            line.to_json(f"{self.directory}/{self.name}.json")
        return line

    def to_csrtrack(self) -> str:
        headers = ["dipole", "quadrupole", "screen"]
        counter = {k: 1 for k in headers}
        elem_dict = translate_elements(
            list(self.elements.elements.values()),
            master_lattice_location=self.master_lattice_location,
            directory=self.directory,
        )
        csrtrackstr = "io_path{logfile = log.txt}\nlattice{\n"
        for e in elem_dict.values():
            for key, count in counter.items():
                if e.hardware_type.lower() == key:
                    csrtrackstr += e.to_csrtrack(n=count)
                    counter[key] += 1
                else:
                    if not e.hardware_class == "Diagnostic":
                        warn(f"Element of type {e.hardware_type} not supported for CSRTrack")
        lastelem = list(elem_dict.values())[-1]
        lastscreen = DiagnosticTranslator(
            name="end_screen",
            hardware_class="Diagnostic",
            hardware_type="Diagnostic",
            machine_area=lastelem.machine_area,
            simulation=DiagnosticSimulationElement(output_filename="end_screen.csrtrack"),
            physical=lastelem.physical,
        )
        csrtrackstr += lastscreen.to_csrtrack(n=counter["screen"])
        csrtrackstr += "}\n"
        self.csrtrack_headers["tracker"].end_time_marker = "screen" + str(counter["screen"]) + "b"
        for h in self.csrtrack_headers.values():
            csrtrackstr += h.write_CSRTrack()
        return csrtrackstr

    def to_wake_t(self) -> "Beamline":
        from wake_t import Beamline
        section_with_drifts = self.createDrifts()
        elem_dict = translate_elements(
            section_with_drifts.values(),
            master_lattice_location=self.master_lattice_location,
            directory=self.directory,
        )
        beamline = []
        for element in elem_dict.values():
            if not element.subelement:
                # try:
                if element.length > 0:
                    beamline.append(element.to_wake_t())
                # except Exception as e:
                #     print('Wake-T writeElements error:', element.name, e)
        return Beamline(beamline)