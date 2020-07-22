from typing import List, Tuple, Dict, Callable

import numpy as np

from .age_stratification import add_zero_to_age_breakpoints, split_age_parameter
from .data_structures import (
    convert_boolean_list_to_indices,
    create_cumulative_dict,
    element_list_division,
    element_list_multiplication,
    increment_list_by_index,
    normalise_dict,
    order_dict_by_keys,
)
from .flowchart import create_flowchart
from .stratification_funcs import (
    create_additive_function,
    create_function_of_function,
    create_multiplicative_function,
    create_sloping_step_function,
    create_time_variant_multiplicative_function,
)
from .string import (
    create_stratified_name,
    create_stratum_name,
    extract_reversed_x_positions,
    extract_x_positions,
    find_name_components,
    find_stem,
    find_stratum_index_from_string,
)
from .validation import validate_stratify, validate_model


def get_all_proportions(names, proportions):
    """
    Determine what % of population get assigned to the different groups.
    """
    proportion_allocated = sum(proportions.values())
    remaining_names = [n for n in names if n not in proportions]
    count_remaining = len(remaining_names)
    assert set(proportions.keys()).issubset(names), "Invalid proprotion keys"
    assert proportion_allocated <= 1, "Sum of proportions must not exceed 1.0"
    if not remaining_names:
        eps = 1e-12
        assert 1 - proportion_allocated < eps, "Sum of proportions must be 1.0"
        return proportions
    else:
        # Divide the remaining proprotions equally
        starting_proportion = (1 - proportion_allocated) / count_remaining
        remaining_proportions = {name: starting_proportion for name in remaining_names}
        return {**proportions, **remaining_proportions}


def get_stratified_compartments(
    stratification_name: str,
    strata_names: List[str],
    stratified_compartments: List[str],
    requested_proportions: Dict[str, float],
    current_names: List[str],
    current_values: List[float],
) -> Tuple[Dict[str, float], List[str]]:
    """
    Stratify the model compartments into sub-compartments, based on the strata names provided,
    Split the population according to the provided proprotions.
    Stratification will be applied  to compartment_names and compartment_values.
    Only compartments specified in `stratified_compartments` will be stratified.
    """
    to_add = {}
    to_remove = []
    # Find the existing compartments that need stratification
    compartments_to_stratify = [c for c in current_names if find_stem(c) in stratified_compartments]
    for compartment in compartments_to_stratify:
        # Add new stratified compartment.
        for stratum in strata_names:
            name = create_stratified_name(compartment, stratification_name, stratum)
            idx = current_names.index(compartment)
            value = current_values[idx] * requested_proportions[stratum]
            to_add[name] = value

        # Remove the original compartment, since it has now been stratified.
        to_remove.append(compartment)

    return to_add, to_remove


OVERWRITE_CHARACTER = "W"
OVERWRITE_KEY = "overwrite"
from summer.constants import Flow


def create_ageing_flows(ages: List[str], unstratified_compartment_names: str, implement_count: int):
    """
    Create inter-compartmental flows for ageing from one stratum to the next.
    The ageing rate is proportional to the width of the age bracket.
    It's assumed that both ages and model timesteps are in years.
    """
    ageing_params = {}
    ageing_flows = []
    for age_idx in range(len(ages) - 1):
        start_age = int(ages[age_idx])
        end_age = int(ages[age_idx + 1])
        param_name = f"ageing{start_age}to{end_age}"
        ageing_rate = 1.0 / (end_age - start_age)
        ageing_params[param_name] = ageing_rate
        # Why do we need the unstratified_compartment_names
        for compartment in unstratified_compartment_names:
            ageing_flow = {
                "type": Flow.STANDARD,
                "parameter": param_name,
                "origin": create_stratified_name(compartment, "age", start_age),
                "to": create_stratified_name(compartment, "age", end_age),
                "implement": implement_count,
            }
            ageing_flows.append(ageing_flow)

    return ageing_params, ageing_flows


def parse_param_adjustment_overwrite(
    strata_names: List[str], adjustment_requests: Dict[str, Dict[str, float]]
):
    # Alternative approach to working out which parameters to overwrite
    # can put a capital W at the string's end to indicate that it is an overwrite parameter, as an alternative to
    # submitting a separate dictionary key to represent the strata which need to be overwritten
    revised_adjustments = {}
    for parameter in adjustment_requests.keys():
        param_adjs = {}
        revised_adjustments[parameter] = param_adjs
        adjusted_strata = adjustment_requests[parameter]

        for stratum in adjusted_strata:
            if stratum == OVERWRITE_KEY:
                # Skip overwrite key
                continue

            elif stratum[-1] == OVERWRITE_CHARACTER:
                # if the parameter ends in W, interpret as an overwrite parameter and added to this key
                if OVERWRITE_KEY not in param_adjs:
                    param_adjs[OVERWRITE_KEY] = []

                param_adjs[stratum[:-1]] = adjusted_strata[stratum]
                param_adjs[OVERWRITE_KEY].append(stratum[:-1])

            else:
                # Copy across
                param_adjs[stratum] = adjusted_strata[stratum]

        if OVERWRITE_KEY not in revised_adjustments:
            # FIXME: This seems kind of pointless
            revised_adjustments[OVERWRITE_KEY] = []

    return revised_adjustments


def stratify_transition_flows(
    stratification_name: str,
    strata_names: List[str],
    adjustment_requests: Dict[str, Dict[str, float]],
    compartments_to_stratify: List[str],
    transition_flows: List[dict],
    implement_count: int,
):
    """
    Stratify flows depending on whether inflow, outflow or both need replication
    """

    flow_idxs = [
        idx for idx, flow in enumerate(transition_flows) if flow["implement"] == implement_count - 1
    ]
    new_flows = []
    overwritten_parameter_adjustment_names = []
    param_updates = {}
    adaptation_function_updates = {}
    for n_flow in flow_idxs:
        flow = transition_flows[n_flow]
        stratify_from = find_stem(flow["origin"]) in compartments_to_stratify
        stratify_to = find_stem(flow["to"]) in compartments_to_stratify
        if stratify_from or stratify_to:
            # find all the requests that start with the parameter of interest and their level of stratification
            param_name = flow["parameter"]
            for stratum in strata_names:
                adjusted_param_name = get_adjusted_parameter(
                    flow["parameter"],
                    stratification_name,
                    stratum,
                    adjustment_requests,
                    param_updates,
                    overwritten_parameter_adjustment_names,
                )

                # Find the flow's parameter name
                if not adjusted_param_name:
                    # default behaviour if not specified is to split the parameter into equal parts if to compartment is split
                    if not (stratify_from and stratify_to):
                        adjusted_param_name = create_stratified_name(
                            param_name, stratification_name, stratum
                        )
                        fraction = 1.0 / len(strata_names)
                        param_updates[adjusted_param_name] = fraction
                        adaptation_function_updates[adjusted_param_name] = lambda v, t: fraction * v
                    else:
                        # Otherwise if no request, retain the existing parameter
                        adjusted_param_name = param_name

                # Determine whether to and/or from compartments are stratified
                if stratify_from:
                    from_compartment = create_stratified_name(
                        flow["origin"], stratification_name, stratum
                    )
                else:
                    from_compartment = flow["origin"]

                if stratify_to:
                    to_compartment = create_stratified_name(
                        flow["to"], stratification_name, stratum
                    )
                else:
                    to_compartment = flow["to"]

                # Add the new flow
                if stratification_name == "strain" and flow["type"] != Flow.STRATA_CHANGE:
                    strain = stratum
                else:
                    strain = flow.get("strain")

                new_flow = {
                    "type": flow["type"],
                    "parameter": adjusted_param_name,
                    "origin": from_compartment,
                    "to": to_compartment,
                    "implement": implement_count,
                }
                if strain:
                    new_flow["strain"] = strain

                force_index = flow.get("force_index")
                if force_index:
                    new_flow["force_index"] = force_index

                new_flows.append(new_flow)

        else:
            # If flow applies to a transition not involved in the stratification,
            # still increment to ensure that it is implemented.
            new_flow = {**flow}
            new_flow["implement"] += 1
            new_flows.append(new_flow)

    return (
        new_flows,
        overwritten_parameter_adjustment_names,
        param_updates,
        adaptation_function_updates,
    )


def stratify_entry_flows(
    stratification_name: str,
    strata_names: List[str],
    entry_proportions: Dict[str, float],
    time_variant_funcs: Dict[str, Callable[[float], float]],
):
    """
    Stratify entry/recruitment/birth flows according to requested entry proportion adjustments
    again, may need to revise behaviour for what is done if some strata are requested but not others
    """
    param_updates = {}
    time_variant_func_updates = {}
    for stratum in strata_names:
        entry_fraction_name = create_stratified_name("entry_fraction", stratification_name, stratum)
        stratum_prop = entry_proportions.get(stratum)
        stratum_prop_type = type(stratum_prop)
        time_variant_func = time_variant_funcs.get(stratum_prop)
        if stratum_prop_type is str and not time_variant_func:
            msg = f"Requested entry fraction function for {entry_fraction_name} not available in time variants"
            raise ValueError(msg)

        if stratification_name == "age" and stratum == "0":
            # Babies get born as age 0
            param_updates[entry_fraction_name] = 1.0
        elif stratification_name == "age":
            # Babies can't get born older than age 0
            param_updates[entry_fraction_name] = 0.0
        elif stratum_prop_type is float:
            # Entry rates have been manually specified
            param_updates[entry_fraction_name] = entry_proportions[stratum]
        elif stratum_prop_type is str:
            # Use the specified time-varying function to calculate the entry fraction.
            time_variant_func_updates[entry_fraction_name] = time_variant_funcs[stratum_prop]
        else:
            # Otherwise just equally divide entry population between all strata.
            param_updates[entry_fraction_name] = 1.0 / len(strata_names)

    return param_updates, time_variant_func_updates


def stratify_death_flows(
    stratification_name: str,
    strata_names: List[str],
    adjustment_requests: Dict[str, Dict[str, float]],
    compartment_types_to_stratify: List[str],
    death_flows: List[dict],
    implement_count: int,
):
    """
    Add compartment-specific death flows
    """
    new_flows = []
    overwritten_parameter_adjustment_names = []
    param_updates = {}
    for flow in death_flows:
        is_prev_implement = flow["implement"] == implement_count - 1
        if not is_prev_implement:
            continue

        if find_stem(flow["origin"]) in compartment_types_to_stratify:
            # if the compartment with an additional death flow is being stratified
            for stratum in strata_names:

                # get stratified parameter name if requested to stratify, otherwise use the unstratified one
                parameter_name = get_adjusted_parameter(
                    flow["parameter"],
                    stratification_name,
                    stratum,
                    adjustment_requests,
                    param_updates,
                    overwritten_parameter_adjustment_names,
                )

                if not parameter_name:
                    parameter_name = flow["parameter"]

                new_flow = {
                    "type": flow["type"],
                    "parameter": parameter_name,
                    "origin": create_stratified_name(flow["origin"], stratification_name, stratum),
                    "implement": implement_count,
                }
                new_flows.append(new_flow)
        else:
            # otherwise if not part of the stratification, accept the existing flow and increment the implement value
            new_flow = {**flow, "implement": flow["implement"] + 1}
            new_flows.append(new_flow)

    return new_flows, param_updates, overwritten_parameter_adjustment_names


def get_adjusted_parameter(
    param_name: str,
    stratification_name: str,
    stratum: str,
    adjustment_requests: Dict[str, Dict[str, float]],
    param_updates: dict,
    overwritten_parameter_adjustment_names: list,
):
    """
    Find the adjustment requests that are extensions of the base parameter type being considered
    expected behaviour is as follows:
    - if there are no submitted requests (keys to the adjustment requests) that are extensions of the unadjusted
        parameter, will return None
    - if there is one submitted request that is an extension of the unadjusted parameter, will return that parameter
    - if there are multiple submitted requests that are extensions to the unadjusted parameter and one is more
        stratified than any of the others (i.e. more instances of the "X" string), will return this most stratified
        parameter
    - if there are multiple submitted requests that are extensions to the unadjusted parameter and several of them
        are equal in having the greatest extent of stratification, will return the longest string
    """
    adjustment_request_param = None
    applicable_params = [p for p in adjustment_requests.keys() if param_name.startswith(p)]
    applicable_param_n_stratifications = [len(find_name_components(p)) for p in applicable_params]
    if applicable_param_n_stratifications:
        max_thing = max(applicable_param_n_stratifications)
        max_length_idxs = [
            idx for idx, p in enumerate(applicable_param_n_stratifications) if p == max_thing
        ]
        candidate_params = [applicable_params[i] for i in max_length_idxs]
        adjustment_request_param = max(candidate_params, key=len)

    param_adjust_requests = adjustment_requests.get(adjustment_request_param)
    adjusted_param_name = None
    if param_adjust_requests:
        if stratum in param_adjust_requests:
            adjusted_param_name = create_stratified_name(param_name, stratification_name, stratum)
        else:
            adjusted_param_name = param_name

        if stratum in param_adjust_requests:
            param_updates[adjusted_param_name] = param_adjust_requests[stratum]

        # Record the parameters that over-write the less stratified parameters closer to the trunk of the tree
        is_overwrite = (
            OVERWRITE_KEY in param_adjust_requests
            and stratum in param_adjust_requests[OVERWRITE_KEY]
        )
        if is_overwrite:
            overwritten_parameter_adjustment_names.append(adjusted_param_name)

    return adjusted_param_name


def stratify_universal_death_rate(
    stratification_name: str,
    strata_names: List[str],
    compartment_types_to_stratify: List[str],
    adjustment_requests: Dict[str, Dict[str, float]],
    time_variants: dict,
    parameters: dict,
):
    """
    stratify the approach to universal, population-wide deaths (which can be made to vary by stratum)
    adjust every parameter that refers to the universal death rate, according to user request if submitted and
        otherwise populated with a value of one by default
    """
    available_death_rates = []
    overwritten_parameter_adjustment_names = []
    adaptation_function_updates = {}

    # ensure baseline function available for modification in universal death rates
    if "universal_death_rate" in time_variants:
        adaptation_function_updates["universal_death_rateX"] = time_variants["universal_death_rate"]
    else:
        adaptation_function_updates["universal_death_rateX"] = lambda time: parameters[
            "universal_death_rate"
        ]

    for stratum in strata_names:
        if (
            "universal_death_rate" in adjustment_requests
            and stratum in adjustment_requests["universal_death_rate"]
        ):
            stratum_name = create_stratum_name(stratification_name, stratum, joining_string="")
            available_death_rates.append(stratum_name)

            # use existing function or create new one from constant as needed
            if type(adjustment_requests["universal_death_rate"][stratum]) == str:
                adaptation_function_updates["universal_death_rateX" + stratum_name] = time_variants[
                    adjustment_requests["universal_death_rate"][stratum]
                ]
            elif isinstance(adjustment_requests["universal_death_rate"][stratum], (int, float)):
                adaptation_function_updates[
                    "universal_death_rateX" + stratum_name
                ] = create_multiplicative_function(
                    time_variants[adjustment_requests["universal_death_rate"][stratum]]
                )

            # record the parameters that over-write the less stratified parameters closer to the trunk of the tree
            if (
                OVERWRITE_KEY in adjustment_requests["universal_death_rate"]
                and stratum in adjustment_requests["universal_death_rate"][OVERWRITE_KEY]
            ):
                overwritten_parameter_adjustment_names.append(
                    create_stratified_name("universal_death_rate", stratification_name, stratum)
                )

    return (
        available_death_rates,
        adaptation_function_updates,
        overwritten_parameter_adjustment_names,
    )


def combine_mixing_matrix(
    old_mixing_categories, old_mixing_matrix, new_mixing_matrix, stratification_name, strata_names
):
    """
    master mixing matrix function to take in a new mixing matrix and combine with the existing ones
    """

    # if no mixing matrix yet, just convert the existing one to a dataframe
    if old_mixing_matrix is None:
        mixing_categories = [stratification_name + "_" + i for i in strata_names]
        combined_mixing_matrix = new_mixing_matrix

    # otherwise take the kronecker product to get the new mixing matrix
    else:
        mixing_categories = [
            old_strata + "X" + stratification_name + "_" + new_strata
            for old_strata, new_strata in itertools.product(old_mixing_categories, strata_names)
        ]
        combined_mixing_matrix = numpy.kron(old_mixing_matrix, new_mixing_matrix)

    return combined_mixing_matrix, mixing_categories


def prepare_target_props(
    target_props: Dict[str, Dict[str, float]],
    stratification_name: str,
    strata_names: List[str],
    unstratified_compartment_names: List[str],
    implement_count: int,
):
    """
    create the dictionary of dictionaries that contains the target values for equlibration

    :parameters:
        target_props: dict
            user submitted dictionary with keys the restrictions by previously implemented strata that apply
        stratification_name: str
            name of stratification process currently being implemented
        strata_names: list
            list of the names of the strata being implemented under the current stratification process
    """
    new_flows = []
    strat_target_props = {}
    for restriction in target_props:
        strat_target_props[restriction] = {}

        # only need parameter values for the first n-1 strata, as the last one will be the remainder
        for stratum in strata_names[:-1]:
            strat_target_props[restriction][stratum] = target_props[restriction][stratum]

        # add in sequential series of flows between neighbouring strata that transition people between the strata being
        # implemented in this stratification stage
        # restriction: name of previously implemented stratum that this equilibration flow applies to, if any, otherwise "all"
        for compartment in unstratified_compartment_names:
            if restriction in find_name_components(compartment) or restriction == "all":
                for n_stratum in range(len(strata_names[:-1])):
                    new_flow = {
                        "type": Flow.STRATA_CHANGE,
                        "parameter": stratification_name
                        + "X"
                        + restriction
                        + "X"
                        + strata_names[n_stratum]
                        + "_"
                        + strata_names[n_stratum + 1],
                        "origin": create_stratified_name(
                            compartment, stratification_name, strata_names[n_stratum],
                        ),
                        "to": create_stratified_name(
                            compartment, stratification_name, strata_names[n_stratum + 1],
                        ),
                        "implement": implement_count,
                    }
                    new_flows.append(new_flow)

        return strat_target_props, new_flows
