import numpy as np
from pydantic import BaseModel
from typing import Dict
from ...utils.elegant import SDDSFile
import nala.models.element as NALA_elements
from nala.models.elementList import SectionLattice, MachineLayout, ElementList
from ...utils.elegant.sdds_classes_APS import SDDS_Floor, SDDS_Params

class ElegantLatticeImporter(BaseModel):

    params_file: str
    """Name of ELEGANT parameters file"""

    floor_file: str
    """Name of ELEGANT floor file"""

    elegant_data: Dict = {}
    """Dictionary containing data about the ELEGANT lattice"""

    floor_data: Dict = {}
    """Dictionary containing floor positions for the ELEGANT lattice"""

    elements: Dict = {}
    """Dictionary containing converted 
    :class:`~nala.models.element.Element` objects"""

    def create_element_dictionary(self):
        params = SDDS_Params(self.params_file)
        self.elegant_data = params.create_element_dictionary()

    def update_floor_coordinates(self):
        flr = SDDS_Floor()
        flr.import_sdds_floor_file(self.floor_file)
        self.floor_data = flr.data

        i = 0
        for k, v in self.floor_data.items():
            if i == 0:
                pass
            else:
                prevind = list(self.floor_data.keys()).index(k) - 1
                self.floor_data[k].update(
                    {
                        "start": list(self.floor_data.values())[prevind]["end"],
                        "start_rotation": list(self.floor_data.values())[prevind]["end_rotation"]
                    }
                )
            i += 1

    def create_element_dictionary(self):
        if not self.elegant_data:
            self.create_element_dictionary()
        if not self.floor_data:
            self.update_floor_coordinates()
        self.elements = {}

        for k, v in self.elegant_data.items():
            if k in self.floor_data:
                if "length" in v:
                    centre = np.array(self.floor_data[k]["start"]) + np.array([0, 0, v["length"] / 2])
                else:
                    centre = np.array(self.floor_data[k]["start"])
                vtype = v["hardware_type"]
                v = self._convert_k_to_kl(v)
                # v = sanitize_kwargs(
                #     model_cls=getattr(NALA_elements, v["hardware_type"]),
                #     data=v
                # )
                rotation = self.floor_data[k]["start_rotation"]
                v.update(
                    {
                        "physical": {
                            "middle": centre,
                            "global_rotation": rotation,
                        },
                    }
                )
                self.elements.update({k: getattr(NALA_elements, vtype)(**v)})

    def create_section(self, section: Dict) -> Dict[str, SectionLattice]:
        if not self.elements:
            self.create_element_dictionary()
        secname = list(section.keys())
        assert len(secname) == 1
        secelements = list(section.values())[0]
        assert len(secelements) == 2
        appending = False
        order = []
        elems = {}
        for name, elem in self.elements.items():
            if name == secelements[0]:
                appending = True
            elif name == secelements[1]:
                appending = False
            if appending:
                order.append(name)
                elems.update({name: elem})
        if not order:
            raise KeyError(f"element {secelements[0]} not found in lattice; could not construct section")
        seclat = SectionLattice(order=order, elements=ElementList(elements=elems), name=secname[0])
        return {secname[0]: seclat}

    def create_layout(self, name: str, sections: Dict) -> MachineLayout:
        layout_sections = {}
        for secname, secpos in sections.items():
            layout_sections.update(self.create_section({secname: secpos}))
        return MachineLayout(
            name=name,
            sections={k: v for k, v in zip(list(layout_sections.keys()), list(layout_sections.values()))}
        )

    @staticmethod
    def _convert_k_to_kl(v) -> dict:
        multi = {}
        if "angle" in v:
            v["k0"] = v["angle"] / float(v["magnetic"]["length"])
        for n in range(1, 9):
            if f"k{n}" in v and ("length" in v["magnetic"] or "length" in v["physical"]):
                try:
                    knl = float(v[f"k{n}"]) * float(v["magnetic"]["length"])
                except KeyError:
                    knl = float(v[f"k{n}"]) * float(v["physical"]["length"])
                multi.update({f"K{n}L": {"order": n, "normal": knl}})
                del v[f"k{n}"]
        if "magnetic" in v:
            v["magnetic"].update({"multipoles": multi})
        return v

    @staticmethod
    def import_sdds_params_file(filename: str, page: int = 0) -> list:
        elegantObject = SDDSFile(index=1)
        elegantObject.read_file(filename, page=page)
        elegantData = elegantObject.data
        return elegantData