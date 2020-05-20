import numpy as np

from autumn.tool_kit.utils import (
    find_rates_and_complements_from_ifr,
    repeat_list_elements,
    repeat_list_elements_average_last_two,
    element_wise_list_division,
)
from autumn.constants import Compartment
from autumn.summer_related.parameter_adjustments import adjust_upstream_stratified_parameter
from autumn.curve import scale_up_function, tanh_based_scaleup


def stratify_by_clinical(model, model_parameters, compartments):
    """
    Stratify the infectious compartments of the covid model (not including the pre-symptomatic compartments, which are
    actually infectious)

    - notifications are derived from progress from early to late for some strata
    - the proportion of people moving from presymt to early infectious, conditioned on age group
    - rate of which people flow through these compartments (reciprocal of time, using within_* which is a rate of ppl / day)
    - infectiousness levels adjusted by early/late and for clinical strata
    - we start with an age stratified infection fatality rate
        - 50% of deaths for each age bracket die in ICU
        - the other deaths go to hospital, assume no-one else can die from COVID
        - should we ditch this?

    """
    # General stratification
    agegroup_strata = model_parameters["all_stratifications"]["agegroup"]
    all_stratifications = model_parameters["all_stratifications"]
    clinical_strata = model_parameters["clinical_strata"]
    # Infection rate multiplication
    infection_rate_multiplier = model_parameters["ifr_multiplier"]
    hospital_inflate = model_parameters["hospital_inflate"]
    # Importation
    implement_importation = model_parameters["implement_importation"]
    imported_cases_explict = model_parameters["imported_cases_explict"]
    symptomatic_props_imported = model_parameters["symptomatic_props_imported"]
    traveller_quarantine = model_parameters["traveller_quarantine"]
    # Time variant case detection
    prop_detected_among_symptomatic = model_parameters["prop_detected_among_symptomatic"]
    # FIXME: Make it clear that this for tahn
    tv_detection_b = model_parameters["tv_detection_b"]
    tv_detection_c = model_parameters["tv_detection_c"]
    tv_detection_sigma = model_parameters["tv_detection_sigma"]
    # ???
    within_hospital_early = model_parameters["within_hospital_early"]
    within_icu_early = model_parameters["within_icu_early"]
    # Strata entry and infection death proportions
    icu_prop = model_parameters["icu_prop"]
    icu_mortality_prop = model_parameters["icu_mortality_prop"]
    infection_fatality_props_10_year = model_parameters["infection_fatality_props"]
    hospital_props_10_year = model_parameters["hospital_props"]
    symptomatic_props_10_year = model_parameters["symptomatic_props"]

    # Define stratification - only stratify infected compartments
    strata_to_implement = clinical_strata
    model_parameters["all_stratifications"]["clinical"] = strata_to_implement
    compartments_to_split = [
        comp
        for comp in compartments
        if comp.startswith(Compartment.EARLY_INFECTIOUS)
        or comp.startswith(Compartment.LATE_INFECTIOUS)
    ]

    # Adjust infection for relative all-cause mortality compared to China, using the infection-rate multiplier
    if infection_rate_multiplier:
        # Adjust infection fatality proprtions by multiplier
        infection_fatality_props_10_year = [
            p * infection_rate_multiplier for p in infection_fatality_props_10_year
        ]
        if hospital_inflate:
            # Not sure what this is doing.
            hospital_props_10_year = [
                min(h_prop * infection_rate_multiplier, 1.0 - symptomatic_props_imported)
                for h_prop in hospital_props_10_year
            ]

    # FIXME: Set params to make comparison happy
    model_parameters["infection_fatality_props"] = infection_fatality_props_10_year
    model_parameters["hospital_props"] = hospital_props_10_year

    # Age dependent proportions of infected people who become symptomatic.
    # This is defined 8x10 year bands, 0-70+, which we transform into 16x5 year bands 0-75+
    symptomatic_props = repeat_list_elements(2, symptomatic_props_10_year)
    # Age dependent proportions of symptomatic people who become hospitalised.
    # This is defined 9x10 year bands, 0-80+, which we trransform into 16x5 year bands 0-75+
    # Calculate 75+ age bracket as half 75-79 and half 80+
    hospital_props = repeat_list_elements_average_last_two(hospital_props_10_year)
    # Infection fatality rate by age group.
    # Data in props used 10 year bands 0-80+, but we want 5 year bands from 0-75+
    # Calculate 75+ age bracket as half 75-79 and half 80+
    infection_fatality_props = repeat_list_elements_average_last_two(
        infection_fatality_props_10_year
    )

    # Find the absolute progression proportions.
    symptomatic_props_arr = np.array(symptomatic_props)
    hospital_props_arr = np.array(hospital_props)
    # Determine the absolute proportion of presymptomatic who become sympt vs non-sympt.
    sympt, non_sympt = subdivide_props(1, symptomatic_props_arr)
    # Determine the absolute proportion of sympt who become hospitalized vs non-hospitalized.
    sympt_hospital, sympt_non_hospital = subdivide_props(sympt, hospital_props_arr)
    # Determine the absolute proportion of hospitalized who become icu vs non-icu.
    sympt_hospital_icu, sympt_hospital_non_icu = subdivide_props(sympt_hospital, icu_prop)
    # FIXME: Some of these proprotions are overidden by time-varying proprotions later and are never used.
    abs_props = {
        "sympt": sympt.tolist(),
        "non_sympt": non_sympt.tolist(),
        "hospital": sympt_hospital.tolist(),
        "sympt_non_hospital": sympt_non_hospital.tolist(),
        "icu": sympt_hospital_icu.tolist(),
        "hospital_non_icu": sympt_hospital_non_icu.tolist(),
    }

    # Calculate the absolute proportion of all patients who should eventually reach hospital death or ICU death.
    # Find IFR that needs to be contributed by ICU and non-ICU hospital deaths
    hospital_death, icu_death = [], []
    for age_idx, agegroup in enumerate(agegroup_strata):
        # If IFR for age group is greater than absolute proportion hospitalised, increased hospitalised proportion
        if infection_fatality_props[age_idx] > abs_props["hospital"][age_idx]:
            abs_props["hospital"][age_idx] = infection_fatality_props[age_idx]

        # Find the target absolute ICU mortality and the amount left over from IFRs to go to hospital, if any
        target_icu_abs_mort = abs_props["icu"][age_idx] * icu_mortality_prop
        left_over_mort = infection_fatality_props[age_idx] - target_icu_abs_mort

        # If some IFR will be left over for the hospitalised
        if left_over_mort > 0.0:
            hospital_death_prop = left_over_mort
            icu_death_prop = target_icu_abs_mort
        # Otherwise if all IFR taken up by ICU
        else:
            hospital_death_prop = 0.0
            icu_death_prop = infection_fatality_props[age_idx]

        hospital_death.append(hospital_death_prop)
        icu_death.append(icu_death_prop)

    abs_props.update({"hospital_death": hospital_death, "icu_death": icu_death})

    # FIXME: These depend on static variables which have been made time-variant.
    # fatality rate for hospitalised patients
    rel_props = {
        "hospital_death": element_wise_list_division(
            abs_props["hospital_death"], abs_props["hospital_non_icu"]
        ),
        "icu_death": element_wise_list_division(abs_props["icu_death"], abs_props["icu"]),
    }

    # Progression rates into the infectious compartment(s)
    # Define progresion rates into non-symptomatic compartments using parameter adjustment.
    stratification_adjustments = {}
    for age_idx, age in enumerate(agegroup_strata):
        key = f"to_infectiousXagegroup_{age}"
        stratification_adjustments[key] = {"non_sympt": non_sympt[age_idx]}

    # Create a function for the proprotion of symptomatic people who are detected at timestep `t`.
    scale_up_multiplier = tanh_based_scaleup(tv_detection_b, tv_detection_c, tv_detection_sigma)

    def prop_detect_among_sympt_func(t):
        return prop_detected_among_symptomatic * scale_up_multiplier(t)

    # Set time-varying isolation proprotions
    for age_idx, agegroup in enumerate(agegroup_strata):
        # Pass the functions to summer
        tv_props = TimeVaryingProprotions(
            age_idx, abs_props, icu_prop, prop_detect_among_sympt_func, hospital_props
        )
        time_variants = [
            [f"prop_sympt_non_hospital_{agegroup}", tv_props.abs_prop_sympt_non_hosp_func],
            [f"prop_sympt_isolate_{agegroup}", tv_props.abs_prop_isolate_func],
            [f"prop_hospital_non_icu_{agegroup}", tv_props.abs_prop_hosp_non_icu_func],
            [f"prop_icu_{agegroup}", tv_props.abs_prop_icu_func],
        ]
        for name, func in time_variants:
            model.time_variants[name] = func

        for clinical_stratum in ["sympt_non_hospital", "sympt_isolate", "hospital_non_icu", "icu"]:
            # Tell summer to use these time varying functions for the stratification adjustments.
            stratification_adjustments[f"to_infectiousXagegroup_{agegroup}"][
                clinical_stratum
            ] = f"prop_{clinical_stratum}_{agegroup}"

    # Calculate death rates and progression rates for hospitalised and ICU patients
    progression_death_rates = {}
    for stratum in ("hospital", "icu"):
        (
            progression_death_rates[stratum + "_infect_death"],
            progression_death_rates[stratum + "_within_late"],
        ) = find_rates_and_complements_from_ifr(
            rel_props[stratum + "_death"],
            1,
            [model_parameters["within_" + stratum + "_late"]] * 16,
        )

    # Death and non-death progression between infectious compartments towards the recovered compartment
    for param in ("within_late", "infect_death"):
        stratification_adjustments.update(
            adjust_upstream_stratified_parameter(
                param,
                strata_to_implement[3:],
                "agegroup",
                model_parameters["all_stratifications"]["agegroup"],
                [
                    progression_death_rates["hospital_" + param],
                    progression_death_rates["icu_" + param],
                ],
                overwrite=True,
            )
        )

    # Over-write rate of progression for early compartments for hospital and ICU
    # FIXME: Ask Romain if he knows why we bother doing this.
    stratification_adjustments.update(
        {
            "within_infectious": {
                "hospital_non_icuW": model_parameters["within_hospital_early"],
                "icuW": model_parameters["within_icu_early"],
            },
        }
    )

    # Sort out all infectiousness adjustments for entire model here
    """
    Sort out all infectiousness adjustments for all compartments of the model.
    """

    # Make adjustment for hospitalisation and ICU admission
    strata_infectiousness = {}
    for stratum in strata_to_implement:
        if stratum + "_infect_multiplier" in model_parameters:
            strata_infectiousness[stratum] = model_parameters[stratum + "_infect_multiplier"]

    # Make adjustment for isolation/quarantine
    model.individual_infectiousness_adjustments = [
        [[Compartment.LATE_INFECTIOUS, "clinical_sympt_isolate"], 0.2]
    ]

    # FIXME: Ask Romain about importation
    # work out time-variant clinical proportions for imported cases accounting for quarantine
    if model_parameters["implement_importation"] and model_parameters["imported_cases_explict"]:
        rep_age_group = (
            "35"  # the clinical split will be defined according to this representative age-group
        )
        tvs = model.time_variants  # to reduce verbosity

        quarantine_scale_up = scale_up_function(
            model_parameters["traveller_quarantine"]["times"],
            model_parameters["traveller_quarantine"]["values"],
            method=4,
        )

        tv_prop_imported_non_sympt = lambda t: stratification_adjustments[
            "to_infectiousXagegroup_" + rep_age_group
        ]["non_sympt"] * (1.0 - quarantine_scale_up(t))

        tv_prop_imported_sympt_non_hospital = lambda t: tvs[
            stratification_adjustments["to_infectiousXagegroup_" + rep_age_group][
                "sympt_non_hospital"
            ]
        ](t) * (1.0 - quarantine_scale_up(t))

        tv_prop_imported_sympt_isolate = lambda t: tvs[
            stratification_adjustments["to_infectiousXagegroup_" + rep_age_group]["sympt_isolate"]
        ](t) + quarantine_scale_up(t) * (
            tvs[
                stratification_adjustments["to_infectiousXagegroup_" + rep_age_group][
                    "sympt_non_hospital"
                ]
            ](t)
            + stratification_adjustments["to_infectiousXagegroup_" + rep_age_group]["non_sympt"]
        )

        tv_prop_imported_hospital_non_icu = lambda t: tvs[
            stratification_adjustments["to_infectiousXagegroup_" + rep_age_group][
                "hospital_non_icu"
            ]
        ](t)

        tv_prop_imported_icu = lambda t: tvs[
            stratification_adjustments["to_infectiousXagegroup_" + rep_age_group]["icu"]
        ](t)

        model.time_variants["tv_prop_imported_non_sympt"] = tv_prop_imported_non_sympt
        model.time_variants[
            "tv_prop_imported_sympt_non_hospital"
        ] = tv_prop_imported_sympt_non_hospital
        model.time_variants["tv_prop_imported_sympt_isolate"] = tv_prop_imported_sympt_isolate
        model.time_variants["tv_prop_imported_hospital_non_icu"] = tv_prop_imported_hospital_non_icu
        model.time_variants["tv_prop_imported_icu"] = tv_prop_imported_icu

        importation_props_by_clinical = {}
        for stratum in strata_to_implement:
            importation_props_by_clinical[stratum] = "tv_prop_imported_" + stratum
    else:
        importation_props_by_clinical = {}

    # Stratify the model using the SUMMER stratification function
    model.stratify(
        "clinical",
        strata_to_implement,
        compartments_to_split,
        infectiousness_adjustments=strata_infectiousness,
        requested_proportions={
            stratum: 1.0 / len(strata_to_implement) for stratum in strata_to_implement
        },
        adjustment_requests=stratification_adjustments,
        entry_proportions=importation_props_by_clinical,
        verbose=False,
    )


def subdivide_props(base_props: np.ndarray, split_props: np.ndarray):
    """
    Split an array (base_array) of proportions into two arrays (split_arr, complement_arr)
    according to the split proportions provided (split_prop).
    """
    split_arr = base_props * split_props
    complement_arr = base_props * (1 - split_props)
    return split_arr, complement_arr


class TimeVaryingProprotions:
    """
    Provides time-varying proportions for a given age group.
    The proportions determine which clinical stratum people transition into when they go
    from being presymptomatic to early infectious.
    """

    def __init__(self, age_idx, abs_props, icu_prop, prop_detect_among_sympt_func, hospital_props):
        self.age_idx = age_idx
        self.abs_props = abs_props
        self.icu_prop = icu_prop
        self.prop_detect_among_sympt = prop_detect_among_sympt_func
        self.hospital_props = hospital_props

    def abs_prop_sympt_non_hosp_func(self, t):
        """
        Returns the absolute proportion of infected not entering the hospital.
        This also does not count people who are isolated.
        This is only people who are not detected.
        """
        prop_symptomatic = self.abs_props["sympt"][self.age_idx]
        rel_prop_not_detected_among_symptomatic = 1.0 - self.prop_detect_among_sympt(t)
        prop_symptomatic_not_detected = prop_symptomatic * rel_prop_not_detected_among_symptomatic
        return prop_symptomatic_not_detected

    def adjusted_prop_hospital_among_sympt_func(self, t):
        """
        Returns the relative proportion of infected entering the hospital.
        """
        prop_hospitalized_among_symptomatic = self.hospital_props[self.age_idx]
        prop_symptomatic_detected = self.prop_detect_among_sympt(t)
        if prop_symptomatic_detected >= prop_hospitalized_among_symptomatic:
            # This is fine because it is less than the proportion detected.
            return prop_hospitalized_among_symptomatic
        else:
            # Higher prop is being hospitalised than is being detected, which doesn't work.
            # So we set a lower bowund to the number detected.
            return prop_symptomatic_detected

    def abs_prop_isolate_func(self, t):
        """
        Returns the absolute proportion of infected becoming isolated at home.
        """
        prop_symptomatic = self.abs_props["sympt"][self.age_idx]
        prop_symptomatic_and_detected = prop_symptomatic * self.prop_detect_among_sympt(t)
        prop_detected_going_to_hospital = self.adjusted_prop_hospital_among_sympt_func(
            t
        ) / self.prop_detect_among_sympt(t)
        prop_detected_not_going_to_hospital = 1 - prop_detected_going_to_hospital
        return prop_symptomatic_and_detected * prop_detected_not_going_to_hospital

    def abs_prop_hosp_non_icu_func(self, t):
        """
        Returns the absolute proprotion of infected people entering the
        hospital but not the ICU.
        """
        prop_symptomatic = self.abs_props["sympt"][self.age_idx]
        prop_hospitalised = prop_symptomatic * self.adjusted_prop_hospital_among_sympt_func(t)
        prop_hospitalised_not_in_icu = prop_hospitalised * (1.0 - self.icu_prop)
        return prop_hospitalised_not_in_icu

    def abs_prop_icu_func(self, t):
        """
        Returns the absolute proprotion of infected people entering the ICU.
        """
        prop_symptomatic = self.abs_props["sympt"][self.age_idx]
        prop_hospitalised = prop_symptomatic * self.adjusted_prop_hospital_among_sympt_func(t)
        prop_hospitalised_in_icu = prop_hospitalised * self.icu_prop
        return prop_hospitalised_in_icu
