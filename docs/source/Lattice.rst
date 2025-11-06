.. _lattice:

Lattice Definition
==================

Lattice structures in :mod:`NALA` provide a hierarchical way to organize accelerator elements into sections and
complete beam paths. The lattice system is built on three main classes that progressively combine elements into
larger structures: sections, layouts, and the complete machine model.

These classes work together to define the full accelerator lattice, from individual elements up to complete
beam paths through the machine.

.. _section-lattice:

Section Lattice
---------------

The :py:class:`SectionLattice <nala.models.elementList.SectionLattice>` class represents a section of a lattice,
consisting of an ordered list of elements along a beam path. Each section typically corresponds to a specific
area or functional region of the accelerator.

A section lattice must define:

* ``name: str``: The name of the lattice section.
* ``order: List[str]``: An ordered list of element names defining the sequence along the beam path.
* ``elements: ElementList``: A container holding the actual element objects.
* ``master_lattice_location: str | None``: Optional top-level directory containing lattice files.

Key methods and properties include:

* ``names``: Returns a list of element names in the section.
* ``createDrifts()``: Automatically inserts drift spaces between elements based on their physical positions.
* ``get_s_values(as_dict, at_entrance, starting_s)``: Calculates the cumulative S-position values for elements along the beamline.

Example usage:

.. code-block:: python

    section = SectionLattice(
        name="injector",
        order=["gun", "solenoid1", "buncher"],
        elements=element_list
    )
    s_positions = section.get_s_values(as_dict=True)

.. _machine-layout:

Machine Layout
--------------

The :py:class:`MachineLayout <nala.models.elementList.MachineLayout>` class represents a complete beam path
through the accelerator, composed of multiple :py:class:`SectionLattice <nala.models.elementList.SectionLattice>`
instances arranged in sequence.

A machine layout defines:

* ``name: str``: The name of the layout/beam path.
* ``sections: Dict[str, SectionLattice]``: Dictionary of lattice sections, keyed by section name.
* ``master_lattice_location: str | None``: Directory containing lattice files.

Important methods include:

* ``get_element(name)``: Returns the element object for a given element name.
* ``get_all_elements(element_type, element_model, element_class)``: Returns filtered lists of elements.
* ``elements_between(start, end, element_type, element_model, element_class)``: Returns elements within a specified range along the beam path.
* ``_get_all_elements()``: Returns all elements in the layout in order.

The layout automatically handles element ordering and can filter elements by various criteria:

.. code-block:: python

    layout = MachineLayout(
        name="main_beam",
        sections={"injector": inj_section, "linac": linac_section}
    )
    quads = layout.get_all_elements(element_type="Quadrupole")

.. _machine-model:

Machine Model
-------------

The :py:class:`MachineModel <nala.models.elementList.MachineModel>` class represents the complete accelerator model,
containing all possible beam paths, sections, and elements. This is the top-level class for managing the entire
lattice structure.

The machine model includes:

* ``layout: str | Dict | None``: Definition of available beam paths, either as a file path or dictionary.
* ``section: str | Dict[str, Dict] | None``: Definition of sections and their elements.
* ``elements: Dict[str, baseElement]``: Complete dictionary of all elements in the machine.
* ``sections: Dict[str, SectionLattice]``: All section lattices available in the model.
* ``lattices: Dict[str, MachineLayout]``: All machine layouts (beam paths) defined.
* ``master_lattice_location: str | None``: Directory containing lattice YAML files.
* ``default_path: str``: The default beam path to use when not explicitly specified.

Key functionality:

* ``get_element(name)``: Retrieve any element by name from the full machine.
* ``get_all_elements(element_type, element_model, element_class)``: Filter all machine elements by criteria.
* ``elements_between(start, end, element_type, element_model, element_class, path)``: Get elements within a range on a specific beam path.
* ``append(values)`` / ``update(values)``: Dynamically add new elements to the model.

The machine model supports multiple beam paths and can automatically build sections from elements if no explicit
section definition is provided:

.. code-block:: python

    model = MachineModel(
        layout="layouts.yaml",
        section="sections.yaml",
        elements=all_elements
    )

    # Get elements along default path
    elements = model.elements_between(
        start="gun",
        end="dump",
        element_type="Quadrupole"
    )

    # Access specific beam path
    bypass_elements = model.elements_between(
        start="split",
        end="merge",
        path="bypass_line"
    )

The machine model automatically manages the relationships between elements, sections, and layouts, ensuring
consistency across the entire lattice definition. It provides both dictionary-style access (``model["element_name"]``)
and method-based queries for flexible interaction with the lattice data.