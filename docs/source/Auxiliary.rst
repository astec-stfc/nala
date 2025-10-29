.. _auxiliary:

Auxiliary Classes
=================

The goal of describing a lattice with :mod:`NALA` is to encapsulate as much information as possible about accelerator lattice elements in a single object or file. 
This page describes the auxiliary information that can be associated with an :py:class:`Element <nala.models.element.Element>` (see :ref:`element-class`). 

.. _simulation-element:

Simulation Element
------------------

Given that one intended use of :mod:`NALA` is to be able to translate accelerator lattices to various formats required for simulation codes, it is helpful to assign to each :py:class:`Element <nala.models.element.Element>` simulation-specific parameters. At the base level, all :py:class:`SimulationElement <nala.models.simulation.SimulationElement>` classes contain:

* ``field_definition: Optional[str]`` -- string pointing to a field definition, such as a fieldmap for an RF cavity or magnet.
* ``wakefield_definition: Optional[str]`` -- string pointing to a wakefield definition, such as the geometric wakefield associated with a cavity cell.
* ``field_reference_position: str`` -- the reference position for the field file, i.e. ``start``, ``middle``, ``end``.
* ``scale_field: float | bool`` -- if this has a numerical value, the field strength in the file is to be scaled by this factor. 

Element-specific child classes are also derived from this and associated with those elements; see :py:class:`MagnetSimulationElement <nala.models.simulation.MagnetSimulationElement>`, :py:class:`DriftSimulationElement <nala.models.simulation.DriftSimulationElement>`, :py:class:`DiagnosticSimulationElement <nala.models.simulation.DiagnosticSimulationElement>`, :py:class:`RFCavitySimulationElement <nala.models.simulation.RFCavitySimulationElement>`, :py:class:`WakefieldSimulationElement <nala.models.simulation.WakefieldSimulationElement>`.

Controls Information
--------------------

The :mod:`NALA` schema also allows the storage of information about how to control the :py:class:`Element <nala.models.element.Element>` from the accelerator control system. Each :py:class:`Element <nala.models.element.Element>` can have multiple :py:class:`ControlVariable <nala.models.control.ControlVariable>` items associated with its :py:class:`ControlsInformation <nala.models.control.ControlsInformation>`, with the latter consisting of a dictionary of the former. Each :py:class:`ControlVariable <nala.models.control.ControlVariable>` can refer to a specific attribute of that element in the control system, such as an EPICS Process Variable or a TANGO Attribute, organised as follows:

* ``identifier: str`` - unique identifier for the control variable.
* ``dtype: type`` -- data type of the control variable (e.g., ``int``, ``float``, ``str``).
* ``protocol: str`` -- protocol or method used to interact with the control variable, i.e. ``CA`` for EPICS Channel Access.
* ``units: str`` -- unit of measurement for the control variable.
* ``description: str`` -- description of the control variable.
* ``read_only: bool`` -- indicates if the variable is read-only.

Electrical and Manufacturer Information
----------------------

Other useful sets of information about an :py:class:`Element <nala.models.element.Element>` include electrical and manufacturer information, stored in :py:class:`ElectricalElement <nala.models.electrical.ElectricalElement>` and :py:class:`ManufacturerElement <nala.models.manufacturer.ManufacturerElement>`, respectively. The attributes of these classes are as follows:

Electrical
~~~~~~~~~~

* ``minI: float`` -- minimum current that the power source can deliver.
* ``maxI: float`` -- maximum current that the power source can deliver.
* ``read_tolerance: float`` -- read current tolerance.

Manufacturer
~~~~~~~~~~~~

* ``manufacturer: str`` -- name of the element manufacturer.
* ``serial_number: str`` -- serial number of the element
