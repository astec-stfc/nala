import os
import numpy as np
from typing import List, Dict, Any, Union
from pydantic import field_validator, BaseModel, ValidationInfo, Field, PositiveInt
from warnings import warn
from ._functions import read_yaml, merge_two_dicts
from .element import baseElement, Drift, PhysicalBaseElement, Diagnostic
from .physical import PhysicalElement, Position
from .baseModels import ModelBase
from .exceptions import LatticeError
import warnings

from .simulation import DriftSimulationElement


def dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def chunks(li, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(li), n):
        yield li[i: i + n]

class BaseLatticeModel(ModelBase):
    """
    Base-level description for defining lattices. Allows dynamic extensibility via `append`, `remove` functions.

    This class should not be used for creating lattices from scratch; rather, use
    `nala.models.elementList.SectionLattice`, `nala.models.elementList.MachineLayout`.
    """

    name: str
    """Name of lattice model."""

    _basename: str

    master_lattice_location: str | None = None
    """Top-level directory containing lattice files."""

    def __add__(self, other: dict) -> dict:
        copy = getattr(self, self._basename).copy()
        copy.extend(other)
        return copy

    def __radd__(self, other: dict) -> dict:
        copy = other.copy()
        copy.extend(getattr(self, self._basename))
        return copy

    def __sub__(self, other):
        copy = getattr(self, self._basename).copy()
        if other in copy:
            del copy[other]
        return copy

    def append(self, other: Any) -> None:
        if not isinstance(other, list):
            other = [other]
        super().__init__(name=self.name, elements=self + other)
        setattr(self, self._basename, self + other)

    def remove(self, other: Any) -> None:
        if other in getattr(self, self._basename):
            copy = getattr(self, self._basename).copy()
            copy.remove(other)
            super().__init__(name=self.name, elements=copy)
            getattr(self, self._basename).remove(other)

    def __str__(self):
        return str({k: v.names() for k, v in getattr(self, self._basename).items()})

    def __repr__(self):
        return self.__str__()


class ElementList(ModelBase):
    """
    A container for an unordered dictionary of :class:`~nala.models.element.baseElement`.
    """
    elements: Dict[str, Union[baseElement, None]]

    def __str__(self):
        return str([e.name for e in self.elements.values()])

    def __getitem__(self, item: str) -> int:
        return self.elements[item]

    @property
    def names(self) -> list:
        return [e.name for e in self.elements.values()]

    def index(self, element: Union[str, baseElement]):
        if isinstance(element, str):
            return list(self.elements.keys()).index(element)
        return list(self.elements.values()).index(element)

    def _get_attributes_or_none(self, a):
        data = {}
        for k, v in self.elements.items():
            if v is not None and hasattr(v, a):
                data.update({k: getattr(v, a)})
            else:
                data.update({k: None})
        return data

    def __getattr__(self, a):
        try:
            return super().__getattr__(a)
        except Exception:
            data = self._get_attributes_or_none(a)
            if all([isinstance(d, (Union[baseElement, None])) for d in data.values()]):
                return ElementList(elements=data)
            return data

    def list(self):
        return list(self.elements.values())


class SectionLattice(BaseLatticeModel):
    """
    A section of a lattice, consisting of a list of elements and their order along the beam path.
    """

    order: List[str]
    """Ordered list of element names."""

    elements: ElementList = Field(default_factory=ElementList)
    """Container for elements."""

    # other_elements: ElementList = ElementList(elements={})
    # TODO should we put this back in?

    _basename: str = "elements"

    @field_validator("elements", mode="before")
    @classmethod
    def validate_elements(
        cls, elements: Union[List[baseElement], ElementList], info: ValidationInfo
    ) -> ElementList:
        if isinstance(elements, list):
            elemdict = {e.name: e for e in elements}
            # print([e for e in info.data['order'] if e not in elemdict.keys()])
            return ElementList(
                elements={
                    e: elemdict[e] for e in info.data["order"] if e in elemdict.keys()
                }
            )
        assert isinstance(elements, ElementList)
        return elements
    #
    # @model_serializer(mode="plain")
    # def serialize(self) -> dict:
    #     data = self.__dict__.copy()
    #     data['elements'] = {"elements": {}}
    #     data['elements']["elements"] = {
    #         k: v.model_dump() for k, v in self.elements.elements.items()
    #     }
    #     return data

    @property
    def names(self) -> List:
        """List of element names.

        Returns
        -------
        List
            List of element names.
        """
        return self.elements.names

    def __str__(self):
        # return str(getattr(self, self._basename).__str__())
        return str(self.names)

    def __getitem__(self, item: Union[str, int]) -> BaseModel:
        if isinstance(item, int):
            return self.elements[self.names[item]]
        return self.elements[item]

    def __getattr__(self, a):
        try:
            return super().__getattr__(a)
        except Exception:
            return getattr(self.elements, a)

    def _get_all_elements(self) -> List:
        """
        Get a list of all the elements in order.

        Returns
        -------
        List
            Ordered list of elements.
        """
        return [self.elements[e] for e in self.order if e in self.elements.names]

    def createDrifts(self, csr_enable: bool=True, lsc_enable: bool=True, lsc_bins: PositiveInt=20):
        """Insert drifts into a sequence of 'elements'"""
        positions = []
        originalelements = dict()
        elementno = 0
        newelements = dict()

        elements = self._get_all_elements()

        # if any([x != y for x, y in zip(elements[0].physical.start.model_dump(), [0, 0, 0])]):
        #     machine_area = elements[0].machine_area
        #     self.order.insert(0, "initial_marker")
        #     self.elements.elements.update(
        #         {
        #             "initial_marker": PhysicalBaseElement(
        #                 name="initial_marker",
        #                 hardware_class="Marker",
        #                 hardware_type="Marker",
        #                 machine_area=machine_area,
        #             )
        #         }
        #     )
        #     elements = self._get_all_elements()

        for elem in elements:
            if not elem.subelement:
                originalelements[elem.name] = elem
                if isinstance(elem, Diagnostic):
                    elem.physical.length = 0
                start = elem.physical.start.array
                end = elem.physical.end.array
                positions.append(start)
                positions.append(end)
        positions = positions[1:]
        positions.append(positions[-1])
        driftdata = list(
            zip(iter(list(originalelements.items())), list(chunks(positions, 2)))
        )

        for e, d in driftdata:
            newelements[e[0]] = e[1]
            if len(d) > 1:
                x1, y1, z1 = d[0]
                x2, y2, z2 = d[1]
                try:
                    length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
                    vector = dot((d[1] - d[0]), [0, 0, 1])
                except Exception as exc:
                    print("Element with error = ", e[0])
                    print(d)
                    raise exc
                if round(length, 6) > 0:
                    elementno += 1
                    name = self.name + "_drift_" + str(elementno)
                    x, y, z = [(a + b) / 2.0 for a, b in zip(d[0], d[1])]
                    newdrift = Drift(
                        name=name,
                        machine_area=newelements[e[0]].machine_area,
                        hardware_class="drift",
                        physical=PhysicalElement(
                            length=abs(round(np.copysign(length, vector), 6)),
                            middle=Position(x=x, y=y, z=z),
                            datum=Position(x=x, y=y, z=z),
                        ),
                        simulation=DriftSimulationElement(
                            csr_enable=csr_enable,
                            lsc_enable=lsc_enable,
                            lsc_bins=lsc_bins,
                        )
                    )
                    newelements[name] = newdrift
        return newelements

    def get_s_values(
        self,
        as_dict: bool = False,
        at_entrance: bool = False,
        starting_s: float = 0
    ) -> list | dict:
        """
        Get the S values for the elements in the lattice.
        This method calculates the cumulative length of the elements in the lattice,
        starting from the entrance or the first element, depending on the `at_entrance` parameter.
        It returns a list or dict of S values, which represent the positions of the elements along the lattice.

        Parameters
        ----------
        as_dict: bool, optional
            If True, returns a dictionary with element names as keys and their S values as values.
        at_entrance: bool, optional
            If True, calculates S values starting from the entrance of the lattice.
            If False, calculates S values starting from the first element.
        starting_s: float, optional
            Initial s position

        Returns
        -------
        list | dict
            A list or dictionary of S values for the elements in the lattice.
            If `as_dict` is True, returns a dictionary with element names as keys and their S values as values.
            If `as_dict` is False, returns a list of S values.
        """
        elems = self.createDrifts()
        s = [starting_s]
        for e in list(elems.values()):
            s.append(s[-1] + e.physical.length)
        s = s[:-1] if at_entrance else s[1:]
        if as_dict:
            return dict(zip([e.name for e in elems.values()], s))
        return list(s)


class MachineLayout(BaseLatticeModel):
    """
    A machine layout, consisting of a dictionary of lattice sections.
    This class could represent a full beam path, for example.
    """

    sections: Dict[str, SectionLattice]  # = Field(frozen=True)
    """Dictionary of :class:`~nala.models.elementList.SectionLattice`, keyed by name."""

    master_lattice_location: str | None = None
    """Directory containing lattice files. """

    _basename: str = "sections"

    def model_post_init(self, __context):
        matrix = [v.elements.elements.values() for v in self.sections.values()]
        all_elems = [item for row in matrix for item in row]
        if len(all_elems) > 0:
            all_elems_reversed = reversed(all_elems)
            superelem = all_elems[-1].name
            start_pos = all_elems[-1].physical.start
            all_elem_corrected = []
            for elem in all_elems_reversed:
                vector = (
                    not elem.physical.end.vector_angle(start_pos, [0, 0, -1]) < -5e-6
                )
                if not elem.is_subelement():
                    superelem = elem.name
                subelem = (
                    elem.subelement == superelem if elem.is_subelement() else False
                )
                # if vector:
                all_elem_corrected += [elem]
                start_pos = elem.physical.start
            self._all_elements = list(reversed(all_elem_corrected))
        else:
            self._all_elements = {}

    @property
    def names(self) -> List:
        """
        Names of lattice sections

        Returns
        -------
        List
            Names of :attr:`~sections`
        """
        return list(self.sections.keys())

    def __str__(self):
        return str([k for k, v in self.sections.items()])

    def __getattr__(self, item: str):
        return getattr(self.sections, item)

    def __getitem__(self, item: str) -> int:
        return self.sections[item]

    def _get_all_elements(self) -> List[baseElement]:
        """
        List of all elements defined in the layout

        Returns
        -------
        List[baseElement]
            List of all elements.
        """
        return self._all_elements

    def _get_all_element_names(self) -> List[str]:
        """
        List of all element names defined in the layout.

        Returns
        -------
        List[str]
            Names of all elements.
        """
        return [e.name for e in self._get_all_elements()]

    def get_element(self, name: str) -> baseElement:
        """
        Return the LatticeElement object corresponding to a given machine element

        :param str name: Name of the element to look up
        :returns: :class:`~nala.models.element.baseElement` instance for that element
        """
        if name in self._get_all_element_names():
            index = self._get_all_element_names().index(name)
            return self._get_all_elements()[index]
        else:
            message = "Element %s does not exist along the beam path" % name
            raise LatticeError(message)

    def _get_element_names(self, lattice: list) -> list:
        """
        Return the name for each LatticeElement object in a list defining a lattice

        :param str lattice: List of LatticeElement objects representing machine hardware
        :returns: List of strings defining the names of the machine elements
        """
        return [ele.name for ele in lattice]

    def _lookup_index(self, name: str) -> int:
        """
        Look up the index of an element in a given lattice

        :param str name: Name of the element to search for
        :returns: List index of the item within that beam path
        """
        try:
            # fetch the index of the element
            return self._get_all_element_names().index(name)
        except ValueError:
            message = "Element %s does not exist along the beam path" % name
            raise LatticeError(message)

    @property
    def elements(self) -> List[str]:
        """
        List of all element names.

        Returns
        -------
        List[str]
            List of all element names.
        """
        return self._get_all_element_names()

    def _filter_element_list(self, result, filt, attrib):
        if isinstance(filt, (str, list)):
            # make list of valid types
            if isinstance(filt, str):
                filter_list = [filt.lower()]
            elif isinstance(filt, list):
                filter_list = [_type.lower() for _type in filt]
            # apply search criteria
            return [
                ele
                for ele in result
                if (
                    hasattr(ele, attrib) and getattr(ele, attrib).lower() in filter_list
                )
            ]
        return result

    def get_all_elements(
        self,
        element_type: Union[str, list, None] = None,
        element_model: Union[str, list, None] = None,
        element_class: Union[str, list, None] = None,
    ) -> List[str]:
        """
        Get all elements in the lattice, or filter them by type/model/class
        # TODO function name implies this returns elements rather than names; rename?

        Parameters
        ----------
        element_type: str | list | None
            Filter by element type; if list, gather multiple types; if None, gather all.
        element_model: str | list | None
            Filter by element model; if list, gather multiple models; if None, gather all.
        element_class
            Filter by element hardware class; if list, gather multiple classes; if None, gather all.

        Returns
        -------
        List[str]
            Filtered names of elements.
        """
        return self.elements_between(
            end=None,
            start=None,
            element_type=element_type,
            element_class=element_class,
            element_model=element_model,
        )

    def elements_between(
        self,
        end: str = None,
        start: str = None,
        element_type: Union[str, list, None] = None,
        element_model: Union[str, list, None] = None,
        element_class: Union[str, list, None] = None,
    ) -> List[str]:
        """
        Returns a list of all lattice elements (of a specified type) between
        any two points along the accelerator (inclusive). Elements are ordered according
        to their longitudinal position along the beam path.

        Parameters
        ----------
        end: str
            Name of the element defining the end of the search region
        start: str
            Name of the element defining the start of the search region
        element_type: str | list | None
            Filter by element type; if list, gather multiple types; if None, gather all.
        element_model: str | list | None
            Filter by element model; if list, gather multiple models; if None, gather all.
        element_class
            Filter by element hardware class; if list, gather multiple classes; if None, gather all.

        Returns
        -------
        List[str]
            Filtered names of elements.
        """
        # replace blank start and/or end point
        element_names = self._get_all_element_names()
        if start is None:
            start = element_names[0]
        if end is None:
            end = element_names[-1]

        # truncate the list between the start and end elements
        first = self._lookup_index(start)
        last = self._lookup_index(end) + 1
        result = self._get_all_elements()[first:last]

        result = self._filter_element_list(result, element_type, "hardware_type")
        result = self._filter_element_list(result, element_model, "hardware_model")
        result = self._filter_element_list(result, element_class, "hardware_class")

        return self._get_element_names(result)


class MachineModel(ModelBase):
    """
    The full model of the accelerator. It describes all :class:`~nala.models.elementList.MachineLayout` and
    :class:`~nala.models.elementList.SectionLattice` that particles can follow.
    These layouts and sections are also defined as Dict[str, list] and Dict[str, list], and the full dictionary
    containing all elements is also accessible.
    """

    layout: str | Dict | None = None
    """Dictionary containing layout names and the names of the sections of which they are composed."""

    section: str | Dict[str, Dict] | None = None
    """Dictionary containing section names and the elements that compose it."""

    elements: Dict[str, baseElement] = {}
    """Dictionary containing all elements defined in the machine model."""

    sections: Dict[str, SectionLattice] = {}
    """Dictionary containing :class:`~nala.models.elementList.SectionLattice`, keyed by name."""

    lattices: Dict[str, MachineLayout] = {}
    """Dictionary containing :class:`~nala.models.elementList.MachineLayout`, keyed by name.
    #TODO rationalise either this name `lattices` or the class name `MachineLayout`.
    """

    master_lattice_location: str | None = None
    """Directory containing lattice YAML files."""

    _layouts: List[str] = None

    _section_definitions: Dict = {}

    _default_path: str = None

    @field_validator("layout", mode="before")
    @classmethod
    def validate_layout(cls, v: str | dict) -> str | dict:
        if isinstance(v, str):
            if os.path.isfile(v):
                return v
            elif os.path.isfile(
                os.path.abspath(os.path.dirname(__file__) + "/../" + v)
            ):
                return os.path.abspath(os.path.dirname(__file__) + "/../" + v)
            else:
                raise ValueError(f"Directory {v} does not exist")
        elif isinstance(v, dict):
            if "layouts" not in v:
                raise KeyError("layout must specify lines each with a list of sections")
            return v
        else:
            raise ValueError("layout must be a str or dict")

    @field_validator("section", mode="before")
    @classmethod
    def validate_section(cls, v: str | dict) -> str | dict:
        if isinstance(v, str):
            if os.path.isfile(v):
                return v
            elif os.path.isfile(
                os.path.abspath(os.path.dirname(__file__) + "/../" + v)
            ):
                return os.path.abspath(os.path.dirname(__file__) + "/../" + v)
            else:
                raise ValueError(f"Directory {v} does not exist")
        elif isinstance(v, dict):
            if "sections" not in v:
                raise KeyError(
                    "section must specify sections each with lists of elements"
                )
            return v
        else:
            warnings.warn(
                "No sections specified. Sections will be generated from elements."
            )

    def model_post_init(self, __context):
        if isinstance(self.layout, str):
            config = read_yaml(self.layout)
            self._layouts = config.layouts
            try:
                self._default_path = config.default_layout
            except AttributeError:
                message = 'Missing "default_layout" in %s ' % self.layout_file
                warn(message)
        elif self.layout is None:
            self._layouts = {}
            self._default_path = None
            warnings.warn("No layouts specified. Lattices will be empty.")
        else:
            for key in ["layouts"]:
                if key not in self.layout:
                    raise KeyError("layout must specify layouts")
            self._layouts = self.layout["layouts"]
            if "default_layout" in self.layout:
                self._default_path = self.layout["default_layout"]
        if isinstance(self.section, str):
            config = read_yaml(self.section)
            self._section_definitions = config.sections
        elif self.section is None:
            self._section_definitions = {}
        else:
            if "sections" not in self.section:
                raise KeyError("section must specify sections with a list of sections")
            self._section_definitions = self.section["sections"]
        if len(self.elements) > 0:
            if self.section:
                self._build_layouts(self.elements)
            else:
                self._build_sections_from_elements(self.elements)

    def __add__(self, other) -> dict:
        copy = self.elements.copy()
        copy.update(other)
        return copy

    def __radd__(self, other) -> dict:
        copy = other.copy()
        copy.update(self.elements)
        return copy

    def __iter__(self) -> iter:
        return iter(self.elements)

    def __str__(self):
        return str(list(self.elements.keys()))

    def append(self, values: dict) -> None:
        self.elements = merge_two_dicts(values, self.elements)
        self._build_sections_from_elements(self.elements)
        self._build_layouts(self.elements)

    def update(self, values: dict) -> None:
        return self.append(values)

    def __getitem__(
        self, item: str | list[str] | tuple[str]
    ) -> BaseModel | List[BaseModel]:
        if isinstance(item, (list, tuple)):
            return [self.elements[subitem] for subitem in item]
        return self.elements[item]

    def __setitem__(self, item: str, value: Any) -> None:
        super().__init__(elements=self + {item: value})

    @property
    def default_path(self) -> str:
        return self._default_path

    @default_path.setter
    def default_path(self, path: str):
        self._default_path = path

    def _build_sections_from_elements(self, elements: dict) -> None:
        """build sections from the elements if no section definition is provided"""
        # Build a unique list of machine areas from the elements
        areas = set()
        for elem in elements.values():
            area = (
                elem.get("machine_area")
                if isinstance(elem, dict)
                else getattr(
                    elem,
                    "machine_area",
                    None,
                )
            )
            if area is not None:
                areas.add(area)
        areas = list(areas)
        for area in areas:
            # collect list of elements from this machine area
            new_elements = [
                x
                for x in elements.values()
                if (
                    x.get("machine_area")
                    if isinstance(x, dict)
                    else getattr(x, "machine_area", None)
                )
                == area
            ]
            self.sections[area] = SectionLattice(
                name=area,
                elements=new_elements,
                order=[
                    e["name"] if isinstance(e, dict) else e.name for e in new_elements
                ],
                master_lattice_location=self.master_lattice_location,
            )
            if not self._section_definitions or area not in self._section_definitions:
                self._section_definitions[area] = [
                    e["name"] if isinstance(e, dict) else e.name for e in new_elements
                ]
        self.lattices = {}

    def _build_layouts(self, elements: dict) -> None:
        """build lists defining the lattice elements along each possible beam path"""
        # build dictionary with a lattice for each beam path
        if self._layouts:
            for path, areas in self._layouts.items():
                for _area in areas:
                    if _area in self._section_definitions:
                        # collect list of elements from this machine area
                        new_elements = [
                            x
                            for x in elements.values()
                            if x.name in self._section_definitions[_area]
                        ]
                        try:
                            self.sections[_area] = SectionLattice(
                                name=_area,
                                elements=new_elements,
                                order=self._section_definitions[_area],
                                master_lattice_location=self.master_lattice_location,
                            )
                        except KeyError:
                            pass
                    else:
                        print("MachineModel", "_build_layouts", _area, "missing")
                self.lattices[path] = MachineLayout(
                    name=path,
                    sections={
                        _area: self.sections[_area]
                        for _area in areas
                        if _area in self.sections
                    },
                    master_lattice_location=self.master_lattice_location,
                )
            if len(self.lattices) == 1 and self._default_path is None:
                self._default_path = list(self.lattices.keys())[0]
        else:
            for _area, elem_names in self._section_definitions.items():
                # collect list of elements from this machine area
                new_elements = [
                    x
                    for x in elements.values()
                    if (x.name in self._section_definitions[_area])
                ]
                self.sections[_area] = SectionLattice(
                    name=_area,
                    elements=new_elements,
                    order=elem_names,
                    master_lattice_location=self.master_lattice_location,
                )
            self.lattices = {}

    def get_element(self, name: str) -> baseElement:
        """
        Return the LatticeElement object corresponding to a given machine element

        :param str name: Name of the element to look up
        :returns: LatticeElement instance for that element
        """
        if name in self.elements:
            return self.elements[name]
        else:
            message = (
                "Element %s does not exist anywhere in the accelerator lattice" % name
            )
            raise LatticeError(message)

    def get_all_elements(
        self,
        element_type: Union[str, list, None] = None,
        element_model: Union[str, list, None] = None,
        element_class: Union[str, list, None] = None,
    ) -> List[str]:
        """
        Get all elements in the lattice, or filter them by type/model/class
        # TODO function name implies this returns elements rather than names; rename?

        Parameters
        ----------
        element_type: str | list | None
            Filter by element type; if list, gather multiple types; if None, gather all.
        element_model: str | list | None
            Filter by element model; if list, gather multiple models; if None, gather all.
        element_class
            Filter by element hardware class; if list, gather multiple classes; if None, gather all.

        Returns
        -------
        List[str]
            Filtered names of elements.
        """
        return self.elements_between(
            end=None,
            start=None,
            element_type=element_type,
            element_class=element_class,
            element_model=element_model,
        )

    def elements_between(
        self,
        end: str = None,
        start: str = None,
        element_type: Union[str, list, None] = None,
        element_model: Union[str, list, None] = None,
        element_class: Union[str, list, None] = None,
        path: str = None,
    ) -> List[str]:
        """
        Returns a list of all lattice elements (of a specified type) between
        any two points along the accelerator (inclusive). Elements are ordered according
        to their longitudinal position along the beam path.

        Parameters
        ----------
        end: str
            Name of the element defining the end of the search region
        start: str
            Name of the element defining the start of the search region
        element_type: str | list | None
            Filter by element type; if list, gather multiple types; if None, gather all.
        element_model: str | list | None
            Filter by element model; if list, gather multiple models; if None, gather all.
        element_class
            Filter by element hardware class; if list, gather multiple classes; if None, gather all.
        path: str
            Optional beam path, i.e. name of :class:`~nala.models.elementList.MachineLayout`.

        Returns
        -------
        List[str]
            Filtered names of elements.
        """
        # determine the beam path
        if path is None:
            if hasattr(self, "_default_path") and self._default_path in self.lattices:
                path = self._default_path
            else:
                raise Exception(
                    '"default_layout" = %s is not defined, and more than one layout exists.'
                    % self._default_path,
                )
        elif path not in self.lattices:
            raise Exception('"path" = %s is not defined' % path)

        if end is None:
            path_obj = self.lattices[path]
            end = path_obj.elements[-1]
        else:
            end_obj = self.get_element(end)
            beam_path = (
                end_obj.machine_area
                if (end_obj.machine_area in self.lattices)
                else path
            )
            path_obj = self.lattices[beam_path]

        # find the start of the search area
        if start is None:
            start = path_obj.elements[0]

        # return a list of elements along this beam path
        elements = path_obj.elements_between(
            start=start,
            end=end,
            element_type=element_type,
            element_class=element_class,
            element_model=element_model,
        )
        return elements
