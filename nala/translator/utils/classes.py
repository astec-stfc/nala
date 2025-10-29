import numpy as np
from pydantic import PositiveInt

class getGrids(object):
    """
    Class defining the appropriate number of space charge bins given the number of particles,
    defined as the closest power of 8 to the cube root of the number of particles.
    """

    def __init__(self):
        self.powersof8 = np.asarray([2**j for j in range(1, 20)])

    def getGridSizes(self, x: PositiveInt) -> int:
        """
        Calculate the 3D space charge grid size given the number of particles, minimum of 4

        Parameters
        ----------
        x: PositiveInt
            Number of particles

        Returns
        -------
        int
            The number of space charge grids
        """
        x = abs(x)
        cuberoot = int(round(x ** (1.0 / 3)))
        return max([4, self.find_nearest(self.powersof8, cuberoot)])

    def find_nearest(self, array: np.ndarray | list, value: int) -> int:
        """
        Get the nearest value in an array to the value provided; in this case the array should be a list of
        powers of 8.

        Parameters
        ----------
        array: np.ndarray or list
            Array of values to be checked
        value: Value to be found in the array

        Returns
        -------
        int
            The closest value in `array` to `value`
        """
        idx = (np.abs(array - value)).argmin()
        return array[idx]
