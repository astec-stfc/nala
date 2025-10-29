from nala.models.simulation import ApertureElement
from .base import BaseElementTranslator

class ApertureTranslator(BaseElementTranslator):
    aperture: ApertureElement

    def _write_ASTRA_Common(self, dic: dict) -> dict:
        """
        Creates the part of the ASTRA element dictionary common to all apertures in ASTRA

        Parameters
        ----------
        dic: dict
            Dictionary containing the parameters for the aperture

        Returns
        -------
        dict
            ASTRA dictionary with parameters and values
        """
        if self.aperture.negative_extent is not None:
            dic["Ap_Z1"] = {"value": self.aperture.negative_extent, "default": 0}
            dic["a_pos"] = {"value": self.physical.start.z}
        else:
            dic["Ap_Z1"] = {"value": self.physical.start.z + self.dz, "default": 0}
        if self.aperture.positive_extent is not None:
            dic["Ap_Z2"] = {"value": self.aperture.positive_extent, "default": 0}
            dic["a_pos"] = {"value": self.physical.start.z}
        else:
            end = (
                self.physical.end.z + self.dz
                if self.physical.end.z >= (self.physical.start.z + 1e-3)
                else self.physical.start.z + self.dz + 1e-3
            )
            dic["Ap_Z2"] = {"value": end, "default": 0}
        dic["A_xrot"] = {
            "value": self.x_rot + self.dx_rot,
            "default": 0,
            "type": "not_zero",
        }
        dic["A_yrot"] = {
            "value": self.y_rot + self.dy_rot,
            "default": 0,
            "type": "not_zero",
        }
        dic["A_zrot"] = {
            "value": self.z_rot + self.dz_rot,
            "default": 0,
            "type": "not_zero",
        }
        return dic

    def _write_ASTRA_Circular(self) -> dict:
        """
        Creates the part of the ASTRA element dictionary relevant to circular apertures in ASTRA

        Parameters
        ----------
        dic: dict
            Dictionary containing the parameters for the aperture

        Returns
        -------
        dict
            ASTRA dictionary with parameters and values
        """
        dic = dict()
        dic["File_Aperture"] = {"value": "RAD"}
        if self.aperture.radius is not None:
            radius = self.aperture.radius
        elif self.aperture.horizontal_size > 0 and self.aperture.vertical_size > 0:
            radius = min([self.aperture.horizontal_size, self.aperture.vertical_size])
        elif self.aperture.horizontal_size > 0:
            radius = self.aperture.horizontal_size
        elif self.aperture.vertical_size > 0:
            radius = self.aperture.vertical_size
        else:
            radius = 1
        dic["Ap_R"] = {"value": 1e3 * radius}
        return self._write_ASTRA_Common(dic)

    def _write_ASTRA_Planar(self, plane, width) -> dict:
        """
        Creates the part of the ASTRA element dictionary common to all apertures in ASTRA

        Parameters
        ----------
        dic: dict
            Dictionary containing the parameters for the aperture

        Returns
        -------
        dict
            ASTRA dictionary with parameters and values
        """
        dic = dict()
        dic["File_Aperture"] = {"value": plane}
        dic["Ap_R"] = {"value": width}
        return self._write_ASTRA_Common(dic)

    def to_astra(self, n: int = 0, **kwargs: dict) -> str:
        """
        Writes the aperture element string for ASTRA

        Parameters
        ----------
        n: int
            Element index number
        **kwargs: dict
            Keyword args

        Returns
        -------
        str
            String representation of the element for ASTRA

        Raises:
        -------
        ValueError
            If `shape` is not in the list of allowed values.
        """
        self.start_write()
        self.aperture.number_of_elements = 0
        if self.aperture.shape in ["elliptical", "circular"]:
            self.aperture.number_of_elements += 1
            dic = self._write_ASTRA_Circular()
            return self._write_ASTRA_dictionary(dic, n)
        elif self.aperture.shape in ["planar", "rectangular"]:
            text = ""
            if self.aperture.horizontal_size is not None and self.aperture.horizontal_size > 0:
                dic = self._write_ASTRA_Planar("Col_X", 1e3 * self.aperture.horizontal_size)
                text += self._write_ASTRA_dictionary(dic, n)
                self.aperture.number_of_elements += 1
            if self.aperture.vertical_size is not None and self.aperture.vertical_size > 0:
                dic = self._write_ASTRA_Planar("Col_Y", 1e3 * self.aperture.vertical_size)
                if self.aperture.number_of_elements > 0:
                    self.aperture.number_of_elements += 1
                    n = n + 1
                    text += "\n"
                text += self._write_ASTRA_dictionary(dic, n)
            return text
        elif self.aperture.shape == "scraper":
            text = ""
            if self.aperture.horizontal_size is not None and self.aperture.horizontal_size > 0:
                dic = self._write_ASTRA_Planar("Scr_X", 1e3 * self.aperture.horizontal_size)
                text += self._write_ASTRA_dictionary(dic, n)
                self.aperture.number_of_elements += 1
            if self.aperture.vertical_size is not None and self.aperture.vertical_size > 0:
                dic = self._write_ASTRA_Planar("Scr_Y", 1e3 * self.aperture.vertical_size)
                if self.aperture.number_of_elements > 0:
                    self.aperture.number_of_elements += 1
                    n = n + 1
                    text += "\n"
                text += self._write_ASTRA_dictionary(dic, n)
            return text
        else:
            raise ValueError(
                "shape must be in ['elliptical', 'planar', 'circular', 'rectangular', 'scraper']"
            )
