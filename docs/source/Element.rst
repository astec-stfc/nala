.. _element:

Element Definition
==================

.. _base-element:

Base-level element
------------------

All elements in a :mod:`NALA` lattice derive from the :py:class:`baseElement <nala.models.element.baseElement>` class. At a minimum, each element must define:

* ``name: str``: The (unique) name of the element.
* ``hardware_class: str``: The generic type of the element. 
* ``hardware_type: str``: The element type. For example, a ``Quadrupole`` has ``hardware_type='Quadrupole'`` and ``hardware_class='Magnet'``. 
* ``machine_area: str``: Used for dividing the lattice into sections based on position.

The following additional properties can also be provided:

* ``hardware_model: str``: A specific model type of an element, for example the manufacturer name.
* ``virtual_name: str``: The name of the element in the virtual control system (if it exists).
* ``alias: str | list``: Alternative name(s) for the element.
* ``subelement: bool``: Represents whether the element 'belongs' to another, i.e. if they overlap in physical space, such as a wakefield attached to a cavity or a solenoid magnet around an RF photoinjector.

While most elements that are typically considered part of an accelerator lattice are defined with reference to a fiducial position, and therefore are described in physical space with respect to that position, not all elements supported by the :mod:`NALA` standard need to have their position defined. Objects that control lighting, low-level RF modules, RF modulators, or feedback systems, are all examples of elements that derive from :py:class:`baseElement <nala.models.element.baseElement>` but do not have a physical position defined.

.. _element-class:

Element
-------

On top of the :py:class:`baseElement <nala.models.element.baseElement>`, additional information pertaining to a
given element can be specified in the :py:class:`Element <nala.models.element.Element>` class, which defines the
following additional properties (described in more detail in :ref:`auxiliary`):

* ``simulation: SimulationElement`` -- see :py:class:`SimulationElement <nala.models.simulation.SimulationElement>`.
* ``controls: ControlsInformation`` -- see :py:class:`ControlsInformation <nala.models.controls.ControlsInformation>`.
* ``manufacturer: ManufacturerElement`` -- see :py:class:`ManufacturerElement <nala.models.manufacturer.ManufacturerElement>`.
* ``electrical: ElectricalElement`` -- see :py:class:`ElectricalElement <nala.models.electrical.ElectricalElement>`.
* ``reference: ReferenceElement`` -- see :py:class:`ReferenceElement <nala.models.reference.ReferenceElement>`.

.. _physical-element:

Physical element
----------------

The :py:class:`PhysicalBaseElement <nala.models.element.PhysicalBaseElement>` class derives from
:py:class:`Element <nala.models.element.Element>`, with the additional ``physical`` property based on
the :py:class:`PhysicalElement <nala.models.physical.PhysicalElement>` class.
This allows the position and rotation of the element in Cartesian co-ordinates to be defined.
Furthermore, elements can be specified with ``error`` and ``survey`` attributes, both of which define
a ``position`` and ``rotation``.

The full specification of an element position therefore consists of:

* ``position: Position(x, y, z)`` -- this refers to the middle of the element.
* ``global_rotation: Rotation(phi, psi, theta)``
* ``length: float``
* ``angle: float`` -- this is a simplified way of retrieving the bend angle in the X-Z plane.
* ``error: ElementError(position=Position(x, y, z), rotation=Rotation(phi, psi, theta))`` -- see :py:class:`ElementError <nala.models.physical.ElementError>`; the reference position for an error is the middle of the element.
* ``survey: ElementSurvey(position=Position(x, y, z), rotation=Rotation(phi, psi, theta))`` -- see :py:class:`ElementSurvey <nala.models.physical.ElementSurvey>`.