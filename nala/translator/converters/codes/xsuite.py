import os
import numpy as np
import yaml
from pydantic import BaseModel, ConfigDict
from pydantic_core import PydanticUndefinedType
from typing import Dict, List
import xtrack as xt
from xtrack.beam_elements.elements import _HasKnlKsl
from nala.models.elementList import (
    SectionLattice,
    MachineLayout,
    ElementList,
)
from . import magnetic_orders
from ...utils.functions import introspect_model_defaults
from ...conversion_rules.codes import xsuite_conversion
from warnings import warn

type_conversion_rules_xsuite_reversed = xsuite_conversion.xsuite_conversion_rules_reverse


with open(
    os.path.dirname(os.path.abspath(__file__)) +
    "/../../conversion_rules/keywords/keyword_conversion_rules_Xsuite.yaml",
    "r",
) as infile:
    keyword_conversion_rules = yaml.safe_load(infile)

class XsuiteLatticeConverter(BaseModel):

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    name: str = "Lattice"

    machine_area: str = "Lattice"

    line: xt.Line
    """Xsuite line"""

    elements: Dict = {}
    """Dictionary containing converted element objects"""

    sections: Dict = {}

    layouts: Dict = {}

    def create_element_dictionary(self):
        s = self.line.survey()._data
        elems = {k: v for k, v in zip(s["name"], self.line.elements)}
        survey = {
            s["name"][i]: {
                "x": s["X"][i],
                "y": s["Y"][i],
                "z": s["Z"][i],
                "phi": (s["phi"][i] + np.pi) % (2*np.pi) - np.pi,
                "psi": (s["psi"][i] + np.pi) % (2*np.pi) - np.pi,
                "theta": (s["theta"][i] + np.pi) % (2*np.pi) - np.pi,
            } for i in range(len(s["X"]))
        }
        for k, v in elems.items():
            machine_area = "IOTA_v8pt4_madx"
            length = 0
            if hasattr(v, "length"):
                length = v.length
            pos = [float(x) for x in [survey[k]["x"], survey[k]["y"], survey[k]["z"]]]
            rot = [float(x) for x in [survey[k]["phi"], survey[k]["psi"], survey[k]["theta"]]]
            phys = {"middle": pos, "global_rotation": rot, "length": length}

            if type(v) in type_conversion_rules_xsuite_reversed:
                p_obj = type_conversion_rules_xsuite_reversed[type(v)]
                model_fields = introspect_model_defaults(p_obj)
                hardware_class = p_obj.model_fields["hardware_class"].default
                if not type(p_obj.model_fields["hardware_type"].default) == PydanticUndefinedType:
                    hardware_type = p_obj.model_fields["hardware_type"].default
                else:
                    hardware_type = hardware_class
                if type(hardware_class) == PydanticUndefinedType:
                    hardware_class = hardware_type
                newobj = {
                    "name": k,
                    "hardware_type": hardware_type,
                    "hardware_class": hardware_class,
                    "machine_area": machine_area,
                    "physical": phys,
                }
                try:
                    merged = keyword_conversion_rules[hardware_type.lower()] | keyword_conversion_rules["general"]
                except KeyError:
                    merged = keyword_conversion_rules["general"]
                except TypeError:
                    merged = keyword_conversion_rules["general"]
                for subk in ["magnetic", "cavity", "simulation", "diagnostic"]:
                    if subk in model_fields:
                        newobj.update({subk: {}})
                kwele = {y: x for x, y in merged.items()}
                exclude = ["order"]
                for name in dir(v):
                    for subk in model_fields:
                        if isinstance(model_fields[subk], dict) and name not in exclude:
                            if name in ["k1", "k2", "k3", "angle"] and isinstance(v, _HasKnlKsl):
                                if "magnetic" not in newobj:
                                    newobj.update({"magnetic": {"length": length}})
                                try:
                                    newobj["magnetic"]["kl"] = getattr(
                                        v, f"k{magnetic_orders[newobj['hardware_type']]}"
                                    ) * v.length
                                except AttributeError as e:
                                    print(e)
                                    newobj["magnetic"]["kl"] = getattr(v, name)
                                newobj["magnetic"].update({name: getattr(v, name)})
                                newobj["hardware_class"] = "Magnet"
                            if name in ["ks"]:
                                newobj.update({"magnetic": {"ks": v.ks, "length": v.length}})
                            if name in model_fields[subk]:
                                newobj[subk].update({name: getattr(v, name)})
                            elif name in kwele:
                                if kwele[name] in model_fields[subk]:
                                    if not isinstance(model_fields[subk][kwele[name]], str) or model_fields[subk][
                                        kwele[name]]:
                                        try:
                                            newobj[subk].update({kwele[name]: getattr(v, name)})
                                        except KeyError as e:
                                            print(e)
                                        except AttributeError as e:
                                            print(e)
                self.elements.update({k: p_obj(**newobj)})
            else:
                warn(f"Type conversion {type(v)} not implemented")

    def create_section(self, start: str, end: str, name: str) -> Dict[str, SectionLattice]:
        if not self.elements:
            self.create_element_dictionary()
        appending = False
        order = []
        elems = {}
        if any([start not in self.elements.keys(), end not in self.elements.keys()]):
            raise KeyError(f"Could not find {start} or {end} in lattice; please check names")
        for name, elem in self.elements.items():
            if name == start:
                appending = True
            if appending:
                order.append(name)
                elems.update({name: elem})
            if name == end:
                appending = False
        if not elems:
            raise ValueError(f"Could not create list of elements; check {start} is before {end}")
        seclat = SectionLattice(order=order, elements=ElementList(elements=elems), name=name)
        self.sections.update({name: seclat})
        return {name: seclat}

    def create_layout(self, name: str, sections: List[Dict]) -> MachineLayout:
        if not self.elements:
            self.create_element_dictionary()
        layout_sections = {}
        for sec in sections:
            assert "name" in sec and "start" in sec and "end" in sec
            layout_sections.update(
                self.create_section(
                    start=sec["start"],
                    end=sec["end"],
                    name=sec["name"],
                )
            )
        layout = MachineLayout(
            name=name,
            sections={k: v for k, v in zip(list(layout_sections.keys()), list(layout_sections.values()))}
        )
        self.layouts.update({name: layout})
        return layout