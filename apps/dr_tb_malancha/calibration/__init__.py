from autumn.constants import Region
from . import (
    vietnam,
    philippines,
)

CALIBRATIONS = {
    Region.VIETNAM: vietnam.run_calibration_chain,
    Region.PHILIPPINES: philippines.run_calibration_chain,
}


def get_calibration_func(region: str):
    return CALIBRATIONS[region]
