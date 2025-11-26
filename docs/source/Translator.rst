.. _translator:

Translator Module
=================

The :mod:`NALA` translator module provides functionality for converting accelerator elements and lattice structures
into formats compatible with various particle simulation codes. The translation system supports export to multiple
simulation codes including:

* `ASTRA <https://www.desy.de/~mpyflo/>`_ :cite:`ASTRA`
* `GPT <https://www.pulsar.nl/gpt/>`_ :cite:`GPT`
* `Elegant <https://www.aps.anl.gov/Accelerator-Operations-Physics/Software#elegant>`_ :cite:`Elegant`
* `CSRTrack <https://www.desy.de/xfel-beam/csrtrack/>`_ :cite:`CSRTrack`
* `Ocelot <https://github.com/ocelot-collab/ocelot>`_ :cite:`OCELOT`
* `Xsuite <https://github.com/xsuite>`_ :cite:`Xsuite`
* `Wake-T <https://github.com/AngelFP/Wake-T/>`_ :cite:`WakeT`
* `Genesis <https://github.com/svenreiche/Genesis-1.3-Version4>`_ :cite:`Genesis`

The translator module uses a hierarchical approach: individual elements are translated first, then combined into
sections that can be exported as complete input files or objects for each simulation code.

.. warning::

   :mod:`NALA` in its current state does not support export of **all possible** element types and **all possible**
   simulation configurations for all codes.
   
   If an important feature is missing, then please raise an issue `here <https://github.com/astec-stfc/nala/issues>`_.

.. _base-element-translator:

Base Element Translator
-----------------------

The :py:class:`BaseElementTranslator <nala.translator.converters.base.BaseElementTranslator>` class extends
:py:class:`PhysicalBaseElement <nala.models.element.PhysicalBaseElement>` and provides the core functionality for
translating individual elements into simulation-specific formats.

Key attributes include:

* ``type_conversion_rules: Dict``: Rules for converting element types between :mod:`NALA` and target codes.
* ``conversion_rules: Dict``: Rules for converting element keywords/parameters.
* ``counter: int``: Counter for numbering elements of the same type.
* ``master_lattice_location: str``: Directory containing lattice and data files.
* ``directory: str``: Output directory for generated files.
* ``ccs: gpt_ccs``: Coordinate system definition for GPT elements.

Translation methods for each supported code:

* ``to_elegant()``: Generates Elegant lattice format strings.
* ``to_ocelot()``: Creates Ocelot element objects.
* ``to_cheetah()``: Creates Cheetah accelerator objects.
* ``to_xsuite(beam_length)``: Generates Xsuite line components.
* ``to_genesis()``: Produces Genesis v4 lattice format.
* ``to_astra(n)``: Creates ASTRA input format.
* ``to_csrtrack(n)``: Generates CSRTrack input format.
* ``to_gpt(Brho, ccs)``: Produces GPT element definitions.
* ``to_wake_t()``: Creates Wake-T beamline objects.
* ``to_opal(sval, designenergy)``: Generates OPAL lattice format.

Utility methods for field and file management:

* ``full_dump()``: Returns a flattened dictionary of all element attributes.
* ``update_field_definition()``: Updates field file references.
* ``generate_field_file_name(param, code)``: Creates appropriate field file names.
* ``get_field_amplitude``: Returns scaled field amplitude values.

Example usage:

.. code-block:: python

    from nala.translator.converters.base import BaseElementTranslator

    translator = BaseElementTranslator.model_validate(element.model_dump())
    translator.directory = "./output"

    elegant_string = translator.to_elegant()
    ocelot_obj = translator.to_ocelot()

.. _element-translation:

Element Translation
-------------------

The :py:func:`translate_elements <nala.translator.converters.converter.translate_elements>` function converts
lists of :py:class:`Element <nala.models.element.Element>` objects into their appropriate translator classes.

Parameters:

* ``elements: List[Element]``: List of NALA elements to translate.
* ``master_lattice_location: str``: Directory containing reference files.
* ``directory: str``: Output directory for generated files.

Returns:

* ``Dict[str, BaseElementTranslator]``: Dictionary of translator objects, keyed by element name.

The function automatically selects the appropriate translator class based on element type:

* Magnets → :py:class:`MagnetTranslator`, :py:class:`SolenoidTranslator`, :py:class:`DipoleTranslator`, etc.
* RF Cavities → :py:class:`RFCavityTranslator`
* Drifts → :py:class:`DriftTranslator`
* Diagnostics → :py:class:`DiagnosticTranslator`
* Apertures → :py:class:`ApertureTranslator`
* Plasma elements → :py:class:`PlasmaTranslator`
* Laser elements → :py:class:`LaserTranslator`

Example:

.. code-block:: python

    from nala.translator.converters.converter import translate_elements

    translated = translate_elements(
        elements=element_list,
        master_lattice_location="/path/to/data",
        directory="./output"
    )

.. _section-lattice-translator:

Section Lattice Translator
--------------------------

The :py:class:`SectionLatticeTranslator <nala.translator.converters.section.SectionLatticeTranslator>` extends
:py:class:`SectionLattice <nala.models.elementList.SectionLattice>` to provide complete lattice section translation
capabilities.

Additional attributes for code-specific configuration:

* ``directory: str``: Output directory for generated files.
* ``astra_headers: Dict``: Configuration headers for ASTRA input files.
* ``csrtrack_headers: Dict``: Configuration headers for CSRTrack input files.
* ``gpt_headers: Dict``: Configuration headers for GPT input files.
* ``opal_headers: Dict``: Configuration headers for OPAL input files.
* ``csr_enable: bool``: Flag to enable calculation of CSR.
* ``lsc_enable: bool``: Flag to enable calculation of LSC.
* ``lsc_bins: PositiveInt``: Number of LSC bins.

Translation methods for complete lattice sections:

* ``to_astra()``: Creates complete ASTRA input files with headers.
* ``to_gpt(startz, endz, Brho)``: Generates GPT lattice definitions with coordinate systems.
* ``to_opal(energy, breakstr)``: Produces OPAL beamline definitions.
* ``to_elegant(charge)``: Creates Elegant lattice files.
* ``to_genesis()``: Generates Genesis v4 lattice format.
* ``to_ocelot(save)``: Creates Ocelot :py:class:`MagneticLattice` objects.
* ``to_cheetah(save)``: Produces Cheetah :py:class:`Segment` objects.
* ``to_xsuite(beam_length, env, particle_ref, save)``: Generates Xsuite :py:class:`Line` objects.
* ``to_csrtrack()``: Creates CSRTrack input files.
* ``to_wake_t()``: Produces Wake-T :py:class:`Beamline` objects.

The translator automatically:

* Inserts drift spaces between elements using ``createDrifts()``
* Handles sub-elements and overlapping components
* Manages field file references and wakefield definitions
* Updates energy/rigidity for sections with acceleration

Example workflow:

.. code-block:: python

    from nala.translator.converters.section import SectionLatticeTranslator

    # Create translator from existing section
    translator = SectionLatticeTranslator.from_section(section)
    translator.directory = "./simulations"

    # Export to different formats
    elegant_lattice = translator.to_elegant(charge=1e-9)

    ocelot_lattice = translator.to_ocelot(save=True)

    xsuite_line = translator.to_xsuite(
        beam_length=1000,
        save=True
    )

    # For codes requiring additional parameters
    gpt_input = translator.to_gpt(
        startz=0.0,
        endz=10.0,
        Brho=0.5
    )

    opal_input = translator.to_opal(
        energy=250.0e6,
        breakstr="//==============="
    )

.. note::

   Some simulation codes require additional parameters for proper translation:

   * GPT requires magnetic rigidity (``Brho``) for dipole elements
   * OPAL requires beam energy for proper dipole field calculations
   * Xsuite requires the number of particles for monitor elements
   * ASTRA and CSRTrack use specialized headers for configuration

.. warning::

   OPAL / GPT translation have not been fully benchmarked and tested. Use with caution.

The translator module ensures consistency across different simulation codes while preserving the physics
and geometry defined in the NALA lattice model. Field maps, wakefields, and other external data files
are automatically referenced and managed during the translation process -- provided they are in the correct
format.

.. _machine-layout-translator:

Machine Layout Translator
-------------------------

The :py:class:`MachineLayoutTranslator <nala.translator.converters.layout.MachineLayoutTranslator>` extends
:py:class:`MachineLayout <nala.models.elementList.MachineLayout>` to translate complete beam paths consisting
of multiple sections.

Attributes:

* ``directory: str``: Output directory for generated files.

The class provides a factory method for creating translators from existing layouts:

* ``from_layout(layout)``: Creates a translator instance from an existing :py:class:`MachineLayout`.

Translation methods produce complete beamline definitions:

* ``to_astra()``: Returns a dictionary of ASTRA input files, keyed by section name.
* ``to_elegant(string, charge)``: Generates a complete Elegant lattice file with LINE definitions.
* ``to_genesis(string)``: Creates Genesis v4 lattice format with beamline structure.
* ``to_ocelot(save)``: Returns a dictionary of Ocelot :py:class:`MagneticLattice` objects.
* ``to_cheetah(save)``: Produces a dictionary of Cheetah :py:class:`Segment` objects.
* ``to_xsuite(beam_length, env, particle_ref, save)``: Generates a dictionary of Xsuite :py:class:`Line` objects.

The translator automatically:

* Processes all sections within the layout
* Maintains section ordering and relationships
* Generates appropriate LINE definitions for codes that support them
* Handles drift insertion for each section

Example usage:

.. code-block:: python

    from nala.translator.converters.layout import MachineLayoutTranslator

    # Create translator from existing layout
    translator = MachineLayoutTranslator.from_layout(machine_layout)
    translator.directory = "./output"

    # Export entire layout to Elegant
    elegant_file = translator.to_elegant(charge=1e-9)

    # Generate section-wise ASTRA files
    astra_sections = translator.to_astra()
    for section_name, astra_input in astra_sections.items():
        with open(f"{section_name}.in", "w") as f:
            f.write(astra_input)

    # Create Ocelot lattices for all sections
    ocelot_lattices = translator.to_ocelot(save=True)

.. _machine-model-translator:

Machine Model Translator
------------------------

The :py:class:`MachineModelTranslator <nala.translator.converters.model.MachineModelTranslator>` extends
:py:class:`MachineModel <nala.models.elementList.MachineModel>` to provide translation capabilities for
the complete accelerator model, including all defined beam paths and sections.

Attributes:

* ``directory: str``: Output directory for generated files.

Factory method:

* ``from_machine(machine)``: Creates a translator from an existing :py:class:`MachineModel`.

Translation methods handle the full machine hierarchy:

* ``to_astra()``: Returns nested dictionaries of ASTRA files (by layout, then section).
* ``to_elegant(string, charge)``: Generates complete Elegant lattice with all paths.
* ``to_genesis(string)``: Creates full Genesis v4 lattice structure.
* ``to_ocelot(save)``: Returns nested dictionaries of :py:class:`MagneticLattice` objects.
* ``to_cheetah(save)``: Produces nested dictionaries of :py:class:`Segment` objects.
* ``to_xsuite(beam_length, env, particle_ref, save)``: Generates nested dictionaries of :py:class:`Line` objects.

The translator provides:

* Complete machine model export with all beam paths
* Hierarchical organization of sections and layouts
* Automatic generation of composite LINE definitions
* Consistent naming across all exported formats

Example workflow:

.. code-block:: python


    from nala.translator.converters.model import MachineModelTranslator

    # Create translator from machine model
    translator = MachineModelTranslator.from_machine(machine_model)
    translator.directory = "./simulations"

    # Export complete machine to Elegant
    with open("machine.lte", "w") as f:
        f.write(translator.to_elegant(charge=250e-12))

    # Generate all ASTRA configurations
    astra_model = translator.to_astra()
    for layout_name, sections in astra_model.items():
        for section_name, content in sections.items():
            filename = f"{layout_name}_{section_name}.in"
            with open(filename, "w") as f:
                f.write(content)

    # Create Xsuite models for all beam paths
    xsuite_model = translator.to_xsuite(
        beam_length=10000,
        save=True
    )

    # Access specific layout/section
    main_beam_injector = xsuite_model["main_beam"]["injector"]

Output structure for nested translations:

* ASTRA: ``Dict[layout_name, Dict[section_name, str]]``
* Ocelot: ``Dict[layout_name, Dict[section_name, MagneticLattice]]``
* Cheetah: ``Dict[layout_name, Dict[section_name, Segment]]``
* Xsuite: ``Dict[layout_name, Dict[section_name, Line]]``

For string-based formats (Elegant, Genesis), the translator generates:

1. Individual element definitions
2. Section LINE definitions
3. Layout LINE definitions composing sections
4. Complete beamline hierarchies

.. note::

   The layout and model translators support a subset of simulation codes compared to individual
   element translators. Currently supported formats are:

   * ASTRA (dictionary output)
   * Elegant (string format)
   * Genesis v4 (string format)
   * Ocelot (object dictionaries)
   * Cheetah (object dictionaries)
   * Xsuite (object dictionaries)

   For GPT, OPAL, CSRTrack, and Wake-T translations, use the
   :py:class:`SectionLatticeTranslator <nala.translator.converters.section.SectionLatticeTranslator>` directly.

The hierarchical translation system ensures that complex machine models with multiple beam paths
can be efficiently exported while maintaining the relationships between elements, sections, and layouts
defined in the NALA model.
