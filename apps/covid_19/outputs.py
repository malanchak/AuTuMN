from autumn.constants import Compartment

from datetime import date
from summer.model import StratifiedModel
from summer.model.utils.string import find_name_components

NOTIFICATION_STRATUM = ["sympt_isolate", "hospital_non_icu", "icu"]


def get_calc_notifications_covid(
    implement_importation,
    imported_cases_explict,
    symptomatic_props_imported,
    prop_detected_among_symptomatic_imported,
):
    def calculate_notifications_covid(model: StratifiedModel, time: float):
        """
        Returns the number of notifications for a given time.
        The fully stratified incidence outputs must be available before calling this function
        """
        notifications_count = 0.0
        time_idx = model.times.index(time)
        for key, value in model.derived_outputs.items():
            is_progress = "progressX" in key
            is_notify_stratum = any([stratum in key for stratum in NOTIFICATION_STRATUM])
            if is_progress and is_notify_stratum:
                notifications_count += value[time_idx]

        if implement_importation and imported_cases_explict:
            prop_imported_detected = (
                symptomatic_props_imported * prop_detected_among_symptomatic_imported
            )

            notifications_count += (
                model.time_variants["crude_birth_rate"](time)
                * sum(model.compartment_values)
                * prop_imported_detected
            )

        return notifications_count

    return calculate_notifications_covid


def calculate_incidence_icu_covid(model, time):
    time_idx = model.times.index(time)
    incidence_icu = 0.0
    for key, value in model.derived_outputs.items():
        if "incidence" in find_name_components(key) and "clinical_icu" in find_name_components(key):
            incidence_icu += value[time_idx]
    return incidence_icu


def get_progress_connections(stratum_names: str):
    """
    Track "progress": flow from early infectious cases to late infectious cases.
    """
    progress_connections = {
        "progress": {
            "origin": Compartment.EARLY_INFECTIOUS,
            "to": Compartment.LATE_INFECTIOUS,
            "origin_condition": "",
            "to_condition": "",
        }
    }
    for stratum_name in stratum_names:
        output_key = f"progressX{stratum_name}"
        progress_connections[output_key] = {
            "origin": Compartment.EARLY_INFECTIOUS,
            "to": Compartment.LATE_INFECTIOUS,
            "origin_condition": "",
            "to_condition": stratum_name,
        }

    return progress_connections


def get_incidence_connections(stratum_names: str):
    """
    Track "incidence": flow from presymptomatic cases to infectious cases.
    """
    incidence_connections = {
        "incidence": {
            "origin": Compartment.PRESYMPTOMATIC,
            "to": Compartment.EARLY_INFECTIOUS,
            "origin_condition": "",
            "to_condition": "",
        }
    }
    for stratum_name in stratum_names:
        output_key = f"incidenceX{stratum_name}"
        incidence_connections[output_key] = {
            "origin": Compartment.PRESYMPTOMATIC,
            "to": Compartment.EARLY_INFECTIOUS,
            "origin_condition": "",
            "to_condition": stratum_name,
        }

    return incidence_connections
