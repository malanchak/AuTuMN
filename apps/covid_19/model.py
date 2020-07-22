import os
from summer.model import StratifiedModel
from summer.model.utils.string import find_all_strata, find_name_components

from autumn.tool_kit.utils import normalise_sequence
from autumn import constants
from autumn.constants import Compartment, BirthApproach
from autumn.tb_model import list_all_strata_for_mortality
from autumn.tool_kit.scenarios import get_model_times_from_inputs
from autumn import inputs
from autumn.environment.seasonality import get_seasonal_forcing

from . import outputs, preprocess
from .stratification import stratify_by_clinical
from .validate import validate_params


def build_model(params: dict) -> StratifiedModel:
    """
    Build the master function to run the TB model for Covid-19
    """
    validate_params(params)

    # Get the agegroup strata breakpoints.
    agegroup_max = params["agegroup_breaks"][0]
    agegroup_step = params["agegroup_breaks"][1]
    agegroup_strata = list(range(0, agegroup_max, agegroup_step))

    # Look up the country population size by age-group, using UN data
    country_iso3 = params["iso3"]
    region = params["region"]
    total_pops = inputs.get_population_by_agegroup(agegroup_strata, country_iso3, region, year=2020)
    life_expectancy = inputs.get_life_expectancy_by_agegroup(agegroup_strata, country_iso3)[0]
    life_expectancy_latest = [life_expectancy[agegroup][-1] for agegroup in life_expectancy]

    # Define compartments
    compartments = [
        Compartment.SUSCEPTIBLE,
        Compartment.EXPOSED,
        Compartment.PRESYMPTOMATIC,
        Compartment.EARLY_INFECTIOUS,
        Compartment.LATE_INFECTIOUS,
        Compartment.RECOVERED,
    ]

    # Indicate whether the compartments representing active disease are infectious
    is_infectious = {
        Compartment.EXPOSED: False,
        Compartment.PRESYMPTOMATIC: True,
        Compartment.EARLY_INFECTIOUS: True,
        Compartment.LATE_INFECTIOUS: True,
    }

    # Calculate compartment periods
    # FIXME: Needs tests.
    base_compartment_periods = params["compartment_periods"]
    compartment_periods_calc = params["compartment_periods_calculated"]
    compartment_periods = preprocess.compartments.calc_compartment_periods(
        base_compartment_periods, compartment_periods_calc
    )

    # Get progression rates from sojourn times, distinguishing to_infectious in order to split this parameter later
    compartment_exit_flow_rates = {}
    for compartment in compartment_periods:
        param_key = f"within_{compartment}"
        compartment_exit_flow_rates[param_key] = 1.0 / compartment_periods[compartment]

    # Distribute infectious seed across infectious compartments
    infectious_seed = params["infectious_seed"]
    total_disease_time = sum([compartment_periods[c] for c in is_infectious])
    init_pop = {
        c: infectious_seed * compartment_periods[c] / total_disease_time for c in is_infectious
    }

    # Force the remainder starting population to go to S compartment (Required as entry_compartment is late_infectious)
    init_pop[Compartment.SUSCEPTIBLE] = sum(total_pops) - sum(init_pop.values())

    # Set integration times
    start_time = params["start_time"]
    end_time = params["end_time"]
    time_step = params["time_step"]
    integration_times = get_model_times_from_inputs(round(start_time), end_time, time_step,)

    # Add inter-compartmental transition flows
    flows = preprocess.flows.DEFAULT_FLOWS

    # Choose a birth approach
    is_importation_active = params["implement_importation"]
    birth_approach = BirthApproach.ADD_CRUDE if is_importation_active else BirthApproach.NO_BIRTH

    # Build mixing matrix.
    static_mixing_matrix = preprocess.mixing_matrix.build_static(country_iso3)
    dynamic_mixing_matrix = None
    dynamic_location_mixing_params = params["mixing"]
    dynamic_age_mixing_params = params["mixing_age_adjust"]
    microdistancing = params["microdistancing"]

    if dynamic_location_mixing_params or dynamic_age_mixing_params:
        npi_effectiveness_params = params["npi_effectiveness"]
        google_mobility_locations = params["google_mobility_locations"]
        is_periodic_intervention = params.get("is_periodic_intervention")
        periodic_int_params = params.get("periodic_intervention")
        dynamic_mixing_matrix = preprocess.mixing_matrix.build_dynamic(
            country_iso3,
            region,
            dynamic_location_mixing_params,
            dynamic_age_mixing_params,
            npi_effectiveness_params,
            google_mobility_locations,
            is_periodic_intervention,
            periodic_int_params,
            end_time,
            microdistancing,
        )

    # FIXME: Remove params from model_parameters
    model_parameters = {**params, **compartment_exit_flow_rates}
    model_parameters["to_infectious"] = model_parameters["within_presympt"]

    # Instantiate SUMMER model
    model = StratifiedModel(
        integration_times,
        compartments,
        init_pop,
        model_parameters,
        flows,
        birth_approach=birth_approach,
        entry_compartment=Compartment.LATE_INFECTIOUS,  # to model imported cases
        starting_population=sum(total_pops),
        infectious_compartment=[i_comp for i_comp in is_infectious if is_infectious[i_comp]],
    )
    if dynamic_mixing_matrix:
        model.find_dynamic_mixing_matrix = dynamic_mixing_matrix
        model.dynamic_mixing_matrix = True

    # Implement seasonal forcing if requested, making contact rate a time-variant rather than constant
    if model_parameters["seasonal_force"]:
        seasonal_forcing_function = get_seasonal_forcing(
            365.0, 173.0, model_parameters["seasonal_force"], model_parameters["contact_rate"]
        )
        model.time_variants["contact_rate"] = seasonal_forcing_function
        model.adaptation_functions["contact_rate"] = seasonal_forcing_function
        model.parameters["contact_rate"] = "contact_rate"

    # Stratify model by age
    # Coerce age breakpoint numbers into strings - all strata are represented as strings
    agegroup_strata = [str(s) for s in agegroup_strata]
    # Create parameter adjustment request for age stratifications
    age_based_susceptibility = params["age_based_susceptibility"]
    adjust_requests = {
        # No change, but distinction is required for later stratification by clinical status
        "to_infectious": {s: 1 for s in agegroup_strata},
        "infect_death": {s: 1 for s in agegroup_strata},
        "within_late": {s: 1 for s in agegroup_strata},
        # Adjust susceptibility across age groups
        "contact_rate": age_based_susceptibility,
    }
    if is_importation_active:
        adjust_requests[
            "import_secondary_rate"
        ] = preprocess.mixing_matrix.get_total_contact_rates_by_age(
            static_mixing_matrix, direction="horizontal"
        )

    # Distribute starting population over agegroups
    requested_props = {
        agegroup: prop for agegroup, prop in zip(agegroup_strata, normalise_sequence(total_pops))
    }

    # We use "agegroup" instead of "age" for this model, to avoid triggering automatic demography features
    # (which work on the assumption that the time unit is years, so would be totally wrong)
    model.stratify(
        "agegroup",
        agegroup_strata,
        compartments_to_stratify=[],  # Apply to all compartments
        requested_proportions=requested_props,
        mixing_matrix=static_mixing_matrix,
        adjustment_requests=adjust_requests,
        # FIXME: This seems awfully a lot like a parameter that should go in a YAML file.
        entry_proportions=preprocess.importation.IMPORTATION_PROPS_BY_AGE,
    )

    model_parameters["all_stratifications"] = {"agegroup": agegroup_strata}
    modelled_abs_detection_proportion_imported = stratify_by_clinical(
        model, model_parameters, compartments
    )

    # Set time-variant importation rate
    if is_importation_active:
        import_times = params["data"]["times_imported_cases"]
        import_cases = params["data"]["n_imported_cases"]
        import_rate_func = preprocess.importation.get_importation_rate_func_as_birth_rates(
            import_times, import_cases, modelled_abs_detection_proportion_imported, total_pops,
        )
        model.parameters["crude_birth_rate"] = "crude_birth_rate"
        model.time_variants["crude_birth_rate"] = import_rate_func

    # Define output connections to collate
    # Track compartment output connections.
    stratum_names = list(set([find_all_strata(x) for x in model.compartment_names]))
    incidence_connections = outputs.get_incidence_connections(stratum_names)
    progress_connections = outputs.get_progress_connections(stratum_names)
    model.output_connections = {
        **incidence_connections,
        **progress_connections,
    }

    # Add notifications to derived_outputs
    implement_importation = model.parameters["implement_importation"]
    model.derived_output_functions["notifications"] = outputs.get_calc_notifications_covid(
        implement_importation, modelled_abs_detection_proportion_imported,
    )
    model.derived_output_functions["incidence_icu"] = outputs.calculate_incidence_icu_covid
    model.derived_output_functions["prevXlateXclinical_icuXamong"] = outputs.calculate_icu_prev

    model.derived_output_functions["hospital_occupancy"] = outputs.calculate_hospital_occupancy
    model.derived_output_functions[
        "proportion_seropositive"
    ] = outputs.calculate_proportion_seropositive

    model.death_output_categories = list_all_strata_for_mortality(model.compartment_names)
    model.derived_output_functions["years_of_life_lost"] = outputs.get_calculate_years_of_life_lost(
        life_expectancy_latest
    )

    return model
