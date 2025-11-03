import pytest
from copy import deepcopy

from nala.unit_tests.models.test_element import physical_base_element
from nala.models.elementList import SectionLattice, ElementList, MachineLayout, MachineModel
from nala.models.exceptions import LatticeError

def chunks(li, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(li), n):
        yield li[i: i + n]

@pytest.fixture
def section_lattice(physical_base_element):
    be1 = deepcopy(physical_base_element)
    be1.name = "elem1"
    be1.physical.middle.z = 1.0
    be1.physical.length = 0.1
    be2 = deepcopy(physical_base_element)
    be2.name = "elem2"
    be2.physical.middle.z = 2.0
    be2.physical.length = 0.1
    elements = ElementList(elements={"elem1": be1, "elem2": be2})
    return SectionLattice(name="TestSection", order=["elem1", "elem2"], elements=elements)

@pytest.fixture
def machine_layout(section_lattice):
    return MachineLayout(name="TestLayout", sections={"TestSection": section_lattice})

@pytest.fixture
def machine_model(section_lattice, machine_layout):
    return MachineModel(
        elements=section_lattice.elements.elements,
        section={"sections": {section_lattice.name: section_lattice.names}},
        layout={
            "layouts": {
                machine_layout.name: list(machine_layout.sections.keys())
            },
            "default_layout": machine_layout.name,
        },
    )

def test_section_lattice_names(section_lattice):
    assert section_lattice.names == ["elem1", "elem2"]

def test_section_lattice_create_drifts(section_lattice):
    drifts = section_lattice.createDrifts()
    print(drifts)
    assert isinstance(drifts, dict)

def test_section_lattice_get_s_values(section_lattice):
    s_values = section_lattice.get_s_values(as_dict=True)
    print(s_values)
    assert isinstance(s_values, dict)
    s_values = section_lattice.get_s_values()
    assert isinstance(s_values, list)

def test_machine_layout_names(machine_layout):
    assert machine_layout.names == ["TestSection"]

def test_machine_layout_get_element(machine_layout):
    with pytest.raises(LatticeError):
        machine_layout.get_element("nonexistent")

def test_machine_layout_elements_between(machine_layout):
    elements = machine_layout.elements_between()
    assert isinstance(elements, list)

def test_machine_model_addition(machine_model, physical_base_element):
    new_elements = {"elem3": physical_base_element}
    result = machine_model + new_elements
    assert "elem3" in result

def test_machine_model_get_element(machine_model):
    element = machine_model.get_element("elem1")
    assert element.name == "elem1"

def test_machine_model_elements_between(machine_model):
    elements = machine_model.elements_between()
    assert isinstance(elements, list)