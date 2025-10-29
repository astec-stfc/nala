from typing import Dict, Any
from nala.models.elementList import MachineModel
from .converter import translate_elements
from .layout import MachineLayoutTranslator

class MachineModelTranslator(MachineModel):
    directory: str = '.'

    @classmethod
    def from_machine(cls, machine: MachineModel) -> "MachineModelTranslator":
        return cls.model_validate(
            {
                "layout": machine.model_copy().layout,
                "section": machine.model_copy().section,
                "elements": machine.model_copy().elements,
                "sections": machine.model_copy().sections,
                "lattices": machine.model_copy().lattices,
                "master_lattice_location": machine.model_copy().master_lattice_location,
            }
        )

    def to_astra(self) -> Dict[str, Dict[str, str]]:
        model = {}
        for name, latt in self.lattices.items():
            model.update(
                {
                    name: MachineLayoutTranslator.from_layout(latt).to_astra()
                }
            )
        return model

    def to_elegant(self, string: str = "", charge: float = None) -> str:
        for latt in self.lattices.values():
            for section in latt.sections.values():
                section_with_drifts = section.createDrifts()
                elem_dict = translate_elements(
                    section_with_drifts.values(),
                    master_lattice_location=self.master_lattice_location,
                    directory=self.directory,
                )
                if charge:
                    string += f"{section.name}_Q: CHARGE, TOTAL = {charge};\n"

                for d in elem_dict.values():
                    string += d.to_elegant()

                string += f"\n{section.name}: LINE = ("
                if charge:
                    string += f"{section.name}_Q, "
                for elem in section_with_drifts.keys():
                    string += f"{elem}, "
                string = f"{string[:-2]})" + "\n\n\n"

        for name, latt in self.lattices.items():
            string += f"{name}: LINE = ("
            for l in list(latt.keys()):
                string += f"{l}, "
            string = f"{string[:-2]})" + "\n\n"
        return string

    def to_genesis(self, string: str = "") -> str:
        for latt in self.lattices.values():
            for section in latt.sections.values():
                section_with_drifts = section.createDrifts()
                elem_dict = translate_elements(
                    section_with_drifts.values(),
                    master_lattice_location=self.master_lattice_location,
                    directory=self.directory,
                )

                for d in elem_dict.values():
                    string += d.to_genesis()

                string += f"\n{section.name}: LINE = " + "{"
                for elem in section_with_drifts.keys():
                    string += f"{elem}, "
                string = f"{string[:-2]}" + "}\n\n\n"

        for name, latt in self.lattices.items():
            string += f"{name}: LINE = " + "{"
            for l in list(latt.keys()):
                string += f"{l}, "
            string = f"{string[:-2]}" + "}\n\n"
        return string

    def to_ocelot(self, save=False) -> Dict[str, Dict[str, "MagneticLattice"]]:
        model = {}
        for name, latt in self.lattices.items():
            model.update(
                {
                    name: MachineLayoutTranslator.from_layout(latt).to_ocelot(save=save)
                }
            )
        return model

    def to_cheetah(self, save=False) -> Dict[str, Dict[str, "Segment"]]:
        model = {}
        for name, latt in self.lattices.items():
            model.update(
                {
                    name: MachineLayoutTranslator.from_layout(latt).to_cheetah(save=save)
                }
            )
        return model

    def to_xsuite(
            self,
            beam_length: int,
            env: Any = None,
            particle_ref: Any = None,
            save=False
    ) -> Dict[str, Dict[str, object]]:
        model = {}
        for name, latt in self.lattices.items():
            model.update(
                {
                    name: MachineLayoutTranslator.from_layout(latt).to_xsuite(
                        beam_length=beam_length,
                        env=env,
                        particle_ref=particle_ref,
                        save=save,
                    )
                }
            )
        return model