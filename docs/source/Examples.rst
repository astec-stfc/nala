.. _examples:

Examples
========

This section provides practical examples for creating and working with NALA elements, lattices, and machine models
in pure Python. These examples demonstrate the fundamental workflows for building accelerator lattice descriptions
programmatically.

.. _creating-elements:

Creating Elements
-----------------

Basic Element Creation
~~~~~~~~~~~~~~~~~~~~~~

The simplest NALA element requires only basic identification properties:

.. code-block:: python

    from nala.models.element import baseElement

    # Create a basic element
    element = baseElement(
        name="QUAD-01",
        hardware_class="Magnet",
        hardware_type="Quadrupole",
        machine_area="LINAC-1"
    )

    print(element.name)  # "QUAD-01"
    print(element.hardware_info)  # {"class": "Magnet", "type": "Quadrupole"}

Physical Elements
~~~~~~~~~~~~~~~~~

Elements with physical properties include position and dimensions:

.. code-block:: python

    from nala.models.element import PhysicalBaseElement
    from nala.models.physical import PhysicalElement, Position

    # Create element with physical properties
    cavity = PhysicalBaseElement(
        name="CAV-01",
        hardware_class="RF",
        hardware_type="Cavity",
        machine_area="LINAC-1",
        physical=PhysicalElement(
            length=1.0,
            middle=Position(x=0, y=0, z=5.0)
        )
    )

    # Access physical properties
    print(cavity.physical.length)  # 1.0
    print(cavity.physical.start.z)  # 4.5
    print(cavity.physical.end.z)    # 5.5

Complete Elements
~~~~~~~~~~~~~~~~~

Full element definitions include electrical, manufacturer, and simulation properties:

.. code-block:: python

    from nala.models.element import Element
    from nala.models.electrical import ElectricalElement
    from nala.models.manufacturer import ManufacturerElement
    from nala.models.simulation import SimulationElement

    quad = Element(
        name="QUAD-02",
        hardware_class="Magnet",
        hardware_type="Quadrupole",
        machine_area="LINAC-1",
        electrical=ElectricalElement(
            maxI=100.0,
            minI=-100.0,
            read_tolerance=0.1
        ),
        manufacturer=ManufacturerElement(
            manufacturer="Company XYZ",
            model="QD-2000",
            serial_number="SN12345"
        ),
        simulation=SimulationElement(
            field_amplitude=25.0
        )
    )

    # Access nested properties directly
    print(quad.maxI)  # 100.0 (finds electrical.maxI)
    print(quad.serial_number)  # "SN12345"
    
Importing from YAML
-------------------

Elements can also be created from YAML files:

.. code-block:: yaml

  # INJ-MAG-DIP-01.yaml
  alias: INJ:DIP1
  controls:
    variables:
      readback:
        description: Readback of INJ-MAG-DIP-01
        dtype: float
        identifier: INJ-MAG-DIP-01:RBV
        protocol: CA
        read_only: true
        units: N/A
      setpoint:
        description: Setpoint of INJ-MAG-DIP-01
        dtype: float
        identifier: INJ-MAG-DIP-01:SP
        protocol: PVA
        read_only: true
        units: N/A
      state:
        description: State of INJ-MAG-DIP-01
        dtype: int
        identifier: INJ-MAG-DIP-01:STATE
        protocol: CA
        read_only: false
        units: N/A
  degauss:
    steps: 11
    tolerance: 0.5
    values: [115.77, -115.77, 69.6, -69.6, 46.4, -46.4, 23.2, -23.2, 11.6, -11.6, 0.0]
  electrical:
    maxI: 116
    minI: -116.0
    read_tolerance: 0.1
  hardware_class: Magnet
  hardware_model: Generic
  hardware_type: Dipole
  machine_area: INJ
  magnetic:
    multipoles: 
      K0L:
        normal: 0.5
        order: 0
        radius: 0.0
        skew: 0.0
    order: 0
    random_multipoles: {}
    skew: false
    systematic_multipoles: {}
  manufacturer:
    hardware_class: Dipole
    manufacturer: Dipole Type 1
    serial_number: '13256'
  name: INJ-MAG-DIP-01
  physical:
    datum: [-0.14887689, 0.0, 1.18670069]
    error:
      position: [0.0, 0.0, 0.0]
      rotation: [0.0, 0.0, 0.0]
    global_rotation: [0.0, 0.0, 0.0]
    length: 0.399216
    middle: [0.0, 0.0, 1.03782375]
    rotation: [0.0, 0.0, 0.0]
    survey:
      position: [0.0, 0.0, 0.0]
      rotation: [0.0, 0.0, 0.0]
  subelement: false
  virtual_name: V-INJ-MAG-DIP-01
  
This can then be loaded in as a :mod:`NALA` object:

.. code-block:: python

  from nala.Importers.YAML_Loader import interpret_YAML_Element, read_YAML_Element_File
  
  filename = "INJ-MAG-DIP-01.yaml"
  
  inj_dip_01 = read_YAML_Element_File(filename)
  
  print(inj_dip_01.middle)
  
.. _creating-sections:

Creating Lattice Sections
-------------------------

Sections group elements into ordered sequences:

.. code-block:: python

    from nala.models.elementList import SectionLattice, ElementList
    from nala.models.element import PhysicalBaseElement
    from copy import deepcopy

    # Create elements for a section
    elem1 = PhysicalBaseElement(
        name="BPM-01",
        hardware_class="Diagnostic",
        hardware_type="BPM",
        machine_area="INJECTOR",
        physical={"middle": {"z": 1.0}, "length": 0.1}
    )

    elem2 = PhysicalBaseElement(
        name="QUAD-01",
        hardware_class="Magnet",
        hardware_type="Quadrupole",
        machine_area="INJECTOR",
        physical={"middle": {"z": 2.0}, "length": 0.2}
    )

    elem3 = PhysicalBaseElement(
        name="BPM-02",
        hardware_class="Diagnostic",
        hardware_type="BPM",
        machine_area="INJECTOR",
        physical={"middle": {"z": 3.0}, "length": 0.1}
    )

    # Create section with ordered elements
    section = SectionLattice(
        name="INJECTOR",
        order=["BPM-01", "QUAD-01", "BPM-02"],
        elements=ElementList(elements={
            "BPM-01": elem1,
            "QUAD-01": elem2,
            "BPM-02": elem3
        })
    )

    # Access section properties
    print(section.names)  # ["BPM-01", "QUAD-01", "BPM-02"]
    print(section["QUAD-01"].hardware_type)  # "Quadrupole"
    print(section[1].name)  # "QUAD-01" (by index)

Working with Drifts
~~~~~~~~~~~~~~~~~~~

Automatically insert drift spaces between elements:

.. code-block:: python

    # Create drifts between elements
    elements_with_drifts = section.createDrifts()

    # The result includes original elements plus drifts
    for name, elem in elements_with_drifts.items():
        if "drift" in name:
            print(f"Drift: {name}, Length: {elem.physical.length}")

S-Position Calculation
~~~~~~~~~~~~~~~~~~~~~~

Calculate cumulative path length along the beamline:

.. code-block:: python

    # Get S-positions as list
    s_values = section.get_s_values()
    print(s_values)  # [0.95, 1.1, 1.9, 2.1, 2.95]

    # Get S-positions as dictionary
    s_dict = section.get_s_values(as_dict=True)
    print(s_dict["QUAD-01"])  # S-position of QUAD-01

    # Start from a different S-value
    s_values_offset = section.get_s_values(starting_s=10.0)

.. _creating-layouts:

Creating Machine Layouts
------------------------

Layouts combine multiple sections into beam paths:

.. code-block:: python

    from nala.models.elementList import MachineLayout

    # Create another section
    linac_section = SectionLattice(
        name="LINAC-1",
        order=["CAV-01", "BPM-03"],
        elements=ElementList(elements={
            "CAV-01": PhysicalBaseElement(
                name="CAV-01",
                hardware_class="RF",
                hardware_type="Cavity",
                machine_area="LINAC-1",
                physical={"middle": {"z": 10.0}, "length": 1.0}
            ),
            "BPM-03": PhysicalBaseElement(
                name="BPM-03",
                hardware_class="Diagnostic",
                hardware_type="BPM",
                machine_area="LINAC-1",
                physical={"middle": {"z": 12.0}, "length": 0.1}
            )
        })
    )

    # Create layout from sections
    layout = MachineLayout(
        name="MainBeamline",
        sections={
            "INJECTOR": section,
            "LINAC-1": linac_section
        }
    )

    # Access layout properties
    print(layout.names)  # ["INJECTOR", "LINAC-1"]
    print(layout.elements)  # All element names in order

    # Get specific element
    cav = layout.get_element("CAV-01")
    print(cav.machine_area)  # "LINAC-1"

    # Filter elements by type
    bpms = layout.get_all_elements(element_type="BPM")
    print(bpms)  # ["BPM-01", "BPM-02", "BPM-03"]

    # Get elements between two points
    between = layout.elements_between(
        start="QUAD-01",
        end="CAV-01"
    )
    print(between)  # Elements from QUAD-01 to CAV-01

.. _creating-machine-models:

Creating Machine Models
-----------------------

The complete machine model manages all elements, sections, and layouts:

.. code-block:: python

    from nala.models.elementList import MachineModel
    from nala.models.element import Element

    # Define elements dictionary
    elements = {
        "MAG-01": Element(
            name="MAG-01",
            hardware_class="Magnet",
            hardware_type="Quadrupole",
            machine_area="AREA-01"
        ),
        "BPM-01": Element(
            name="BPM-01",
            hardware_class="Monitor",
            hardware_type="BPM",
            machine_area="AREA-01"
        ),
        "CAV-01": Element(
            name="CAV-01",
            hardware_class="RF",
            hardware_type="Cavity",
            machine_area="AREA-02"
        )
    }

Building from Elements Only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

NALA can automatically create sections from machine areas:

.. code-block:: python

    # Create model with elements only
    # Sections are auto-generated from machine_area
    model = MachineModel(elements=elements)

    print(list(model.sections.keys()))  # ["AREA-01", "AREA-02"]
    print(model.sections["AREA-01"].names)  # ["MAG-01", "BPM-01"]

Defining Explicit Sections
~~~~~~~~~~~~~~~~~~~~~~~~~~

Specify the order of elements within sections:

.. code-block:: python

    model = MachineModel(
        elements=elements,
        section={
            "sections": {
                "AREA-01": ["BPM-01", "MAG-01"],  # Custom order
                "AREA-02": ["CAV-01"]
            }
        }
    )

    print(model.sections["AREA-01"].order)  # ["BPM-01", "MAG-01"]

Complete Model with Layouts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Define beam paths through the machine:

.. code-block:: python

    model = MachineModel(
        elements=elements,
        section={
            "sections": {
                "AREA-01": ["MAG-01", "BPM-01"],
                "AREA-02": ["CAV-01"]
            }
        },
        layout={
            "layouts": {
                "main_beam": ["AREA-01", "AREA-02"],
                "bypass": ["AREA-01"]  # Alternative path
            },
            "default_layout": "main_beam"
        }
    )

    # Access layouts
    print(list(model.lattices.keys()))  # ["main_beam", "bypass"]
    print(model.default_path)  # "main_beam"

    # Get elements along specific path
    main_elements = model.elements_between(
        path="main_beam"
    )
    print(main_elements)  # ["MAG-01", "BPM-01", "CAV-01"]

    bypass_elements = model.elements_between(
        path="bypass"
    )
    print(bypass_elements)  # ["MAG-01", "BPM-01"]

Dynamic Model Updates
~~~~~~~~~~~~~~~~~~~~~

Add elements to an existing model:

.. code-block:: python

    # Start with empty model
    model = MachineModel()

    # Add elements dynamically
    new_elements = {
        "NEW-01": Element(
            name="NEW-01",
            hardware_class="Magnet",
            hardware_type="Dipole",
            machine_area="NEW-AREA"
        )
    }

    model.append(new_elements)

    # Sections are automatically updated
    print("NEW-AREA" in model.sections)  # True
    print(model["NEW-01"].hardware_type)  # "Dipole"
