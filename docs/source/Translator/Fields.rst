.. _translator-fields:

Field Utilities
===============

The :mod:`NALA` translator utilities include a comprehensive field module for representing and manipulating
electromagnetic fields used in particle accelerator simulations. This module provides functionality for
reading, writing, and converting field maps between different simulation codes.

.. warning::

   The field utilities module is currently under construction. Not all field types and formats are
   fully supported. Please report bugs or questions through the issue tracker.
   The plan is to migrate these utilities to use the :mod:`OpenPMD` standard :cite:`OpenPMD`.

.. _field-class:

Field Class
-----------

The :py:class:`field <nala.translator.utils.fields.field>` class provides a generic representation for
electromagnetic fields including RF structures, wakefields, and magnetic fields.

Key attributes include:

**Coordinate parameters:**

* ``x, y, z``: Cartesian position coordinates
* ``r``: Radial coordinate (for cylindrically symmetric fields)
* ``t``: Time parameter

**Field components:**

* ``Ex, Ey, Ez, Er``: Electric field components
* ``Bx, By, Bz, Br``: Magnetic field components
* ``Wx, Wy, Wz, Wr``: Wakefield components
* ``G``: Magnetic gradient (for quadrupoles)

**Metadata and configuration:**

* ``filename: str``: Path to the field file
* ``field_type: fieldtype``: Type of electromagnetic field
* ``origin_code: str``: Code that generated the field
* ``frequency: float``: RF frequency (for dynamic fields)
* ``cavity_type: cavitytype``: Standing or travelling wave
* ``norm: float``: Normalization factor

Each field parameter is represented as a :py:class:`FieldParameter <nala.translator.utils.fields.FieldParameter>`
object containing the field values and associated units.

Supported field types:

* ``1DElectroStatic``, ``1DMagnetoStatic``, ``1DElectroDynamic``
* ``2DElectroStatic``, ``2DMagnetoStatic``, ``2DElectroDynamic``
* ``3DElectroStatic``, ``3DMagnetoStatic``, ``3DElectroDynamic``
* ``LongitudinalWake``, ``TransverseWake``, ``3DWake``
* ``1DQuadrupole``

.. _field-io:

Reading and Writing Fields
--------------------------

The field class supports multiple file formats for import and export:

**Supported formats:**

* ASTRA (``.astra``, ``.dat``)
* SDDS (``.sdds``)
* GDF (``.gdf``) for GPT
* OPAL (``.opal``)
* HDF5 (``.hdf5``) - NALA native format

Reading field files:

.. code-block:: python

    from nala.translator.utils.fields import field

    # Read an ASTRA cavity field
    rf_field = field(
        filename="cavity.dat",
        field_type="1DElectroDynamic",
        cavity_type="StandingWave",
        frequency=2.856e9
    )

    # Or read explicitly
    rf_field = field()
    rf_field.read_field_file(
        "solenoid.gdf",
        field_type="2DMagnetoStatic"
    )

Writing field files for specific codes:

.. code-block:: python

    # Convert to different format
    astra_file = rf_field.write_field_file(
        code="astra",
        location="./fields"
    )

    gpt_file = rf_field.write_field_file(code="gdf")

    # Get field data as array
    field_array = rf_field.get_field_data(code="ocelot")

.. _field-parameters:

Field Parameters
----------------

The :py:class:`FieldParameter <nala.translator.utils.fields.FieldParameter>` class encapsulates field
values with their associated units and metadata:

* ``name: str``: Parameter identifier
* ``value: UnitValue``: Numerical values with units
* Methods for unit conversion and data manipulation

Properties for accessing field data:

* ``z_values``: Returns Z coordinate values
* ``t_values``: Returns time values (converts from Z if needed)
* Automatic conversion between time and spatial coordinates

.. _field-integration:

Integration with Element Translation
------------------------------------

Field utilities are integrated into the element translator system for handling:

**RF Cavities:**
  - Standing and travelling wave structures
  - Field amplitude scaling via ``get_field_amplitude``
  - Phase and frequency management

**Magnets:**
  - Static field maps for solenoids, quadrupoles
  - Field gradient definitions
  - Error field representations

**Wakefields:**
  - Longitudinal and transverse wake functions
  - Geometric and resistive wall wakes
  - CSR wakefield support (limited)

The :py:class:`BaseElementTranslator <nala.translator.converters.base.BaseElementTranslator>` uses field
utilities through:

* ``generate_field_file_name(param, code)``: Creates appropriate field filenames
* ``update_field_definition()``: Updates field file references
* ``get_field_amplitude``: Retrieves scaled field values

Example with cavity translator:

.. code-block:: python

    from nala.translator.converters.cavity import RFCavityTranslator
    from nala.translator.utils.fields import field

    # Cavity with field map
    cavity = RFCavityTranslator(
        name="L1_CAV01",
        simulation={
            "field_definition": field(
                filename="l1_cavity.gdf",
                field_type="1DElectroDynamic",
                cavity_type="TravellingWave",
                frequency=2.856e9
            ),
            "field_amplitude": 25e6  # V/m
        }
    )

    # Field file is automatically converted when exporting
    astra_string = cavity.to_astra()  # Field converted to ASTRA format
    ocelot_obj = cavity.to_ocelot()   # Field data embedded in object

.. _field-caveats:

Limitations and Caveats
-----------------------

.. warning::

   Current limitations of the field utilities:

   * 3D field maps are only partially supported
   * Some travelling wave cavity modes may not convert correctly
   * Field interpolation between different grid types is limited
   * Normalization conventions vary between codes and may require manual adjustment