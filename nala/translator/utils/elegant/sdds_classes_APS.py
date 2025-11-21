from itertools import groupby
import numpy as np
from warnings import warn

try:
    from counter import Counter
except ImportError:
    from ..functions import Counter
from ..functions import chop, introspect_model_defaults
from .SDDSFile import SDDSFile
from ...converters import (
    type_conversion_rules_aliases,
    type_conversion_rules_Elegant,
    keyword_conversion_rules_elegant,
    element_keywords,
)
import nala.models.element as NALA_elements


class SDDS_Floor:

    duplicates: list = []

    sdds_position_columns = [
        "ElementName",
        "X",
        "Y",
        "Z",
    ]

    sdds_angle_columns = [
        "ElementName",
        "phi",
        "psi",
        "theta",
    ]

    def __init__(self, filename: str = None, page: int = 0, prefix: str = "."):
        [
            setattr(self, c, [])
            for c in (self.sdds_position_columns + self.sdds_angle_columns)
        ]
        self.prefix = prefix
        self.counter = Counter()
        if filename is not None:
            self.floor_data = self.import_sdds_floor_file(filename, page)

    def get_duplicate_element_names(self) -> list:
        return [k for k, g in groupby(sorted(self.ElementName)) if len(list(g)) > 1]

    def number_element(self, elem):
        if elem in self.duplicates:
            no = self.counter.counter(elem)
            self.counter.add(elem)
            return elem + self.prefix + str(no)
        return elem

    def import_sdds_floor_file(self, filename: str, page: int = 0) -> list:
        elegantObject = SDDSFile(index=1)
        elegantObject.read_file(filename, page=page)
        elegantData = elegantObject.data
        for a in self.sdds_position_columns + self.sdds_angle_columns:
            if np.array(elegantData[a]).ndim > 1:
                setattr(self, a, elegantData[a][page])
            else:
                setattr(self, a, elegantData[a])
        self.counter = Counter()
        self.duplicates = self.get_duplicate_element_names()
        self.ElementName = [self.number_element(e) for e in self.ElementName]
        # print(self.ElementName)
        # exit()
        rawpositiondata = {
            e: list(map(float, chop([x, y, z], 1e-6)))
            for e, x, y, z in list(
                zip(*[getattr(self, a) for a in self.sdds_position_columns])
            )
        }
        rawangledata = {
            e: list(map(float, chop([phi, psi, theta], 1e-6)))
            for e, phi, psi, theta in list(
                zip(*[getattr(self, a) for a in self.sdds_angle_columns])
            )
        }
        self.data = {
            e: {"end": rawpositiondata[e], "end_rotation": rawangledata[e]}
            for e in self.ElementName
        }

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        print(f"{key} missing!")

class SDDS_Params:

    def __init__(self, filename: str, page: int = 0):
        self.filename = filename
        self.page = page
        self.elegantObject = None
        self.elegantData = None
        self.elegantParams = None

    def import_sdds_params_file(self) -> None:
        self.elegantObject = SDDSFile(index=1)
        self.elegantObject.read_file(self.filename, page=self.page)
        self.elegantData = self.elegantObject.data

    def join_params(self) -> None:
        if not self.elegantData:
            self.import_sdds_params_file()
        self.elegantParams = {}
        for i, k in enumerate(self.elegantData["ElementName"]):
            if k not in self.elegantParams:
                self.elegantParams.update(
                    {
                        f"{k}.{self.elegantData['ElementOccurence'][i]}":
                            {param: [] for param in list(self.elegantData.keys())[1:]}
                    }
                )
            for val in list(self.elegantData.keys())[1:]:
                if self.elegantData["ElementName"][i] == k:
                    self.elegantParams[f"{k}.{self.elegantData['ElementOccurence'][i]}"][val].append(self.elegantData[val][i])

    def create_element_dictionary(self) -> tuple:
        if not self.elegantParams:
            self.join_params()
        sfconvert = {}
        # disallowed = ["bore", "zwakefile"]
        filenames = {}
        sfconvert = {}
        for k, v in self.elegantParams.items():
            elemtype = v["ElementType"][0].lower()
            if elemtype in element_keywords and "drift" not in elemtype:
                sfconvert.update({k: {"hardware_type": elemtype, "name": k, "hardware_class": elemtype, "machine_area": "test"}})
            elif elemtype in list(type_conversion_rules_Elegant.values()):
                switch_dict = {y: x for x, y in type_conversion_rules_Elegant.items()}
                sfconvert.update(
                    {k: {"hardware_type": switch_dict[elemtype], "name": k, "hardware_class": switch_dict[elemtype], "machine_area": "test"}})
            else:
                found = False
                for sf, aliases in type_conversion_rules_aliases.items():
                    if elemtype in aliases:
                        sfconvert.update(
                            {k: {"hardware_type": sf, "name": k, "machine_area": "test"}})
                        found = True
                if not found:
                    warn(f"Could not parse ELEGANT element type {elemtype} for {k}; setting as drift.")
                    sfconvert.update(
                        {k: {"hardware_type": "Drift", "name": k, "hardware_class": "Drift", "machine_area": "test"}})
            sftype = sfconvert[k]["hardware_type"]
            try:
                if sftype == "kicker":
                    model_fields = introspect_model_defaults(getattr(NALA_elements, "Combined_Corrector"))
                    sfconvert[k]["hardware_type"] = "Combined_Corrector"
                elif "Cavity" not in sftype:
                    model_fields = introspect_model_defaults(getattr(NALA_elements, sftype.capitalize()))
                    sfconvert[k]["hardware_type"] = sfconvert[k]["hardware_type"].capitalize()
                else:
                    model_fields = introspect_model_defaults(getattr(NALA_elements, sftype))
            except AttributeError:
                print(f"type {sftype} not recognized")
                sfconvert.update({k: {"hardware_type": "Drift", "name": k, "hardware_class": "Drift", "machine_area": "test"}})
                continue
            for subk in ["magnetic", "cavity", "simulation", "diagnostic", "physical"]:
                if subk in model_fields:
                    sfconvert[k].update({subk: {}})
            if sfconvert[k]["hardware_type"] == "Drift":
                continue
            for i, param in enumerate(v["ElementParameter"]):
                param = param.lower()
                merged = keyword_conversion_rules_elegant["general"]
                if sftype.lower() in keyword_conversion_rules_elegant:
                    merged = keyword_conversion_rules_elegant[sftype.lower()] | keyword_conversion_rules_elegant[
                        "general"]
                kwele = {y: x for x, y in merged.items()}
                # if param in kwele:
                val = v["ParameterValueString"][i] if len(v["ParameterValueString"][i]) > 0 else \
                    v["ParameterValue"][i]
                # sfconvert[k].update({kwele[param]: val})
                for subk in model_fields:
                    val = v["ParameterValueString"][i] if len(v["ParameterValueString"][i]) > 0 else \
                        v["ParameterValue"][i]
                    if isinstance(model_fields[subk], dict):
                        if param in ["k1", "k2", "k3", "angle", "l"]:
                            sfconvert[k].update({param: v["ParameterValue"][i]})
                        if param in model_fields[subk]:
                            if val:
                                sfconvert[k][subk].update({param: val})
                        elif param in kwele:
                            if kwele[param] in model_fields[subk]:
                                if not isinstance(model_fields[subk][kwele[param]], str) or model_fields[subk][
                                    kwele[param]]:
                                    sfconvert[k][subk].update({kwele[param]: val})
                if "file" in param and v['ParameterValueString'][i]:
                    filenames.update({k: {param: v['ParameterValueString'][i]}})
                    warn(f"Apparent filename found for element {k}: "
                         f"{param} = {v['ParameterValueString'][i]}; "
                         f"check path, file format and column data")
        print(sfconvert)
        return sfconvert, filenames