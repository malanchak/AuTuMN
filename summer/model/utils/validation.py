"""
Functions to validate the inputs to a model.
Validation performed using Cerberus: https://docs.python-cerberus.org/en/stable/index.html
"""
from typing import List

from cerberus import Validator
import numpy as np


from summer.constants import (
    Compartment,
    Flow,
    BirthApproach,
    Stratification,
    IntegrationType,
)


def validate_stratify(
    model,
    stratification_name,
    strata_request,
    compartment_types_to_stratify,
    requested_proportions,
    entry_proportions,
    adjustment_requests,
    infectiousness_adjustments,
    mixing_matrix,
    target_props,
):
    schema = get_stratify_schema(
        model, stratification_name, strata_request, compartment_types_to_stratify
    )
    validator = Validator(schema, allow_unknown=True, require_all=True)
    stratify_data = {
        "stratification_name": stratification_name,
        "strata_request": strata_request,
        "compartment_types_to_stratify": compartment_types_to_stratify,
        "requested_proportions": requested_proportions,
        "entry_proportions": entry_proportions,
        "adjustment_requests": adjustment_requests,
        "infectiousness_adjustments": infectiousness_adjustments,
        "mixing_matrix": mixing_matrix,
        "target_props": target_props,
    }
    is_valid = validator.validate(stratify_data)
    if not is_valid:
        errors = validator.errors
        raise ValidationException(errors)


def get_stratify_schema(model, stratification_name, strata_names, compartment_types_to_stratify):
    """
    Schema used to validate model attributes during initialization.
    """
    strata_names_strs = [str(s) for s in strata_names]
    return {
        "stratification_name": {
            "type": "string",
            "forbidden": list(model.all_stratifications.keys()),
        },
        "strata_request": {
            "type": "list",
            "check_with": check_strata_request(stratification_name, compartment_types_to_stratify),
            "schema": {"type": ["string", "integer"]},
        },
        "compartment_types_to_stratify": {
            "type": "list",
            "schema": {"type": "string"},
            "allowed": model.compartment_types,
        },
        "requested_proportions": {
            "type": "dict",
            "valuesrules": {"type": ["integer", "float"]},
            "keysrules": {"allowed": strata_names_strs},
        },
        # TODO: Sanity check the values of entry_proportions somehow
        "entry_proportions": {
            "type": "dict",
            "valuesrules": {
                "type": ["integer", "float", "string"],
                "check_with": check_time_variant_key(model.time_variants),
            },
            "keysrules": {"allowed": strata_names_strs},
        },
        "adjustment_requests": {
            "type": "dict",
            "keysrules": {"allowed": list(model.parameters.keys())},
            "valuesrules": {
                "type": "dict",
                "keysrules": {"allowed": strata_names_strs + [f"{s}W" for s in strata_names_strs]},
                "valuesrules": {
                    "type": ["integer", "float", "string"],
                    "check_with": check_time_variant_key(model.time_variants),
                },
            },
        },
        "infectiousness_adjustments": {
            "type": "dict",
            "valuesrules": {"type": ["integer", "float"]},
            "keysrules": {"allowed": strata_names_strs},
        },
        "mixing_matrix": {"nullable": True, "check_with": check_mixing_matrix(strata_names)},
        "target_props": {
            "nullable": True,
            "type": "dict",
            "keysrules": {"allowed": list(model.parameters.keys())},
            "valuesrules": {
                "type": "dict",
                "keysrules": {"allowed": strata_names_strs},
                "valuesrules": {
                    "type": ["integer", "float", "string"],
                    "check_with": check_time_variant_key(model.time_variants),
                },
            },
        },
    }


def check_strata_request(strat_name, compartment_types_to_stratify):
    """
    Strata requested must be well formed.
    """

    def _check(field, value, error):
        if strat_name == "age":
            if not min([int(s) for s in value]) == 0:
                error(field, "First age strata must be '0'")
            if compartment_types_to_stratify:
                error(field, "Age stratification must be applied to all compartments")

    return _check


def check_time_variant_key(time_variants: dict):
    """
    Ensure value is a key in time variants if it is a string
    """

    def _check(field, value, error):
        if type(value) is str and value not in time_variants:
            error(field, "String value must be found in time variants dict.")

    return _check


def check_mixing_matrix(strata_names: List[str]):
    """
    Ensure mixing matrix is correctly specified
    """
    num_strata = len(strata_names)

    def _check(field, value, error):
        if value is None:
            return  # This is fine

        if not type(value) is np.ndarray:
            error(field, "Mixing matrix must be Numpy array (or None)")
        elif value.shape != (num_strata, num_strata):
            error(field, f"Mixing matrix must have shape ({num_strata}, {num_strata})")

    return _check


def validate_model(model):
    """
    Throws an error if the model's initial data is invalid.
    """
    schema = get_model_schema(model)
    validator = Validator(schema, allow_unknown=True, require_all=True)
    model_data = model.__dict__
    is_valid = validator.validate(model_data)
    if not is_valid:
        errors = validator.errors
        raise ValidationException(errors)


def get_model_schema(model):
    """
    Schema used to validate model attributes during initialization.
    """
    return {
        "ticker": {"type": "boolean"},
        "reporting_sigfigs": {"type": "integer"},
        "starting_population": {"type": "integer"},
        "entry_compartment": {"type": "string"},
        "birth_approach": {
            "type": "string",
            "allowed": [
                BirthApproach.ADD_CRUDE,
                BirthApproach.REPLACE_DEATHS,
                BirthApproach.NO_BIRTH,
            ],
        },
        "times": {
            "type": "list",
            "schema": {"anyof_type": ["integer", "float"]},
            "check_with": check_times,
        },
        "compartment_types": {"type": "list", "schema": {"type": "string"}},
        "infectious_compartment": {
            "type": "list",
            "schema": {"type": "string"},
            "allowed": model.compartment_types,
        },
        "initial_conditions": {
            "type": "dict",
            "valuesrules": {"anyof_type": ["integer", "float"]},
            "check_with": check_initial_conditions(model),
        },
        "requested_flows": {
            "type": "list",
            "check_with": check_flows(model),
            "schema": {
                "type": "dict",
                "schema": {
                    "type": {
                        "type": "string",
                        "allowed": [
                            Flow.CUSTOM,
                            Flow.STANDARD,
                            Flow.INFECTION_FREQUENCY,
                            Flow.INFECTION_DENSITY,
                            Flow.COMPARTMENT_DEATH,
                        ],
                    },
                    "parameter": {"type": "string"},
                    "origin": {"type": "string"},
                    "to": {"type": "string", "required": False},
                },
            },
        },
        "output_connections": {
            "type": "dict",
            "valuesrules": {
                "type": "dict",
                "schema": {
                    "origin": {"type": "string"},
                    "to": {"type": "string"},
                    "origin_condition": {"type": "string", "required": False},
                    "to_condition": {"type": "string", "required": False},
                },
            },
        },
        "death_output_categories": {
            "type": "list",
            "schema": {"type": "list", "schema": {"type": "string"}},
        },
        "derived_output_functions": {"type": "dict", "check_with": check_derived_output_functions,},
    }


def check_flows(model):
    """
    Validate flows
    """

    def _check(field, value, error):
        # Validate flows
        for flow in value:
            is_missing_params = (
                flow["parameter"] not in model.parameters
                and flow["parameter"] not in model.time_variants
            )
            if is_missing_params:
                error(field, "Flow parameter not found in parameter list")
            if flow["origin"] not in model.compartment_types:
                error(field, "From compartment name not found in compartment types")
            if "to" in flow and flow["to"] not in model.compartment_types:
                error(field, "To compartment name not found in compartment types")

            # Customized flows must have functions
            if flow["type"] == Flow.CUSTOM:
                if "function" not in flow.keys():
                    error(
                        field,
                        "A customised flow requires a function to be specified in user request dictionary.",
                    )
                elif not callable(flow["function"]):
                    error(field, "value of 'function' key must be a function")

    return _check


def check_initial_conditions(model):
    """
    Ensure initial conditions are well formed, and do not exceed population numbers.
    """

    def _check(field, value, error):
        try:
            is_pop_too_small = sum(value.values()) > model.starting_population
            if is_pop_too_small:
                error(
                    field, "Initial condition population exceeds total starting population.",
                )

            if not all([c in model.compartment_types for c in value.keys()]):
                error(
                    field,
                    "Initial condition compartment name is not one of the listed compartment types",
                )
        except TypeError:
            error(field, "Could not check initial conditions.")

    return _check


def check_times(field, value, error):
    """
    Ensure times are sorted in ascending order.
    """
    if sorted(value) != value:
        error(field, "Integration times are not in order")


def check_derived_output_functions(field, value, error):
    """
    Ensure every item in dict is a function.
    """
    if not all([callable(f) for f in value.values()]):
        error(field, "Must be a dict of functions.")


class ValidationException(Exception):
    """
    Raised when user-defined data is found to be invalid.
    """

    pass
