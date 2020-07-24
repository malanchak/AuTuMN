"""
Constants used in building the AuTuMN / SUMMER models.
"""
import os

# Import summer constants here for convenience
from summer.constants import (
    BirthApproach,
    IntegrationType,
    Stratification,
    Compartment,
    Flow,
)

# Filesystem paths
file_path = os.path.abspath(__file__)
separator = "\\" if "\\" in file_path else "/"
BASE_PATH = separator.join(file_path.split(separator)[:-2])
DATA_PATH = os.path.join(BASE_PATH, "data")
INPUT_DATA_PATH = os.path.join(DATA_PATH, "inputs")
OUTPUT_DATA_PATH = os.path.join(DATA_PATH, "outputs")
APPS_PATH = os.path.join(BASE_PATH, "apps")
EXCEL_PATH = os.path.join(DATA_PATH, "xls")


class Region:
    AUSTRALIA = "australia"
    PHILIPPINES = "philippines"
    VIETNAM = "vietnam"
    MALAYSIA = "malaysia"
    VICTORIA = "victoria"
    NSW = "nsw"
    LIBERIA = "liberia"
    MANILA = "manila"
    CALABARZON = "calabarzon"
    BICOL = "bicol"
    CENTRAL_VISAYAS = "central-visayas"
    UNITED_KINGDOM = "united-kingdom"
    BELGIUM = "belgium"
    ITALY = "italy"
    SWEDEN = "sweden"
    FRANCE = "france"
    SPAIN = "spain"

    REGIONS = [
        AUSTRALIA,
        PHILIPPINES,
        MALAYSIA,
        VICTORIA,
        NSW,
        LIBERIA,
        MANILA,
        CALABARZON,
        BICOL,
        CENTRAL_VISAYAS,
        UNITED_KINGDOM,
        BELGIUM,
        ITALY,
        SWEDEN,
        FRANCE,
        SPAIN,
    ]
