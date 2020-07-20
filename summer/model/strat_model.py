import copy
import itertools
from functools import lru_cache
from typing import List, Dict

import numpy as np
import numpy

from summer.constants import (
    Compartment,
    Flow,
    BirthApproach,
    Stratification,
    IntegrationType,
)
from .epi_model import EpiModel
from .utils import (
    convert_boolean_list_to_indices,
    create_cumulative_dict,
    create_function_of_function,
    create_multiplicative_function,
    create_stratified_name,
    create_stratum_name,
    create_time_variant_multiplicative_function,
    element_list_multiplication,
    element_list_division,
    extract_reversed_x_positions,
    find_name_components,
    find_stem,
    increment_list_by_index,
)
from summer.model import utils


STRATA_EQUILIBRATION_FACTOR = 0.01
OVERWRITE_CHARACTER = "W"
OVERWRITE_KEY = "overwrite"


class StratifiedModel(EpiModel):
    """
    stratified version of the epidemiological model that inherits from EpiModel above, which is a concrete class and
        could in theory run stratified models independently
    however, this class should make the stratification process more algorithmic, easier and more reliable

    :attribute adaptation_functions: dict
        single stage functions representing each stratified parameter component, from which to build the final functions
            (i.e. final_parameter_functions)
    :attribute all_stratifications: dictionary
        keys are all the stratification names implemented so far. values are the list of strata for each stratification
    :attribute available_death_rates: list
        single strata names for which population_wide mortality will be adjusted (or over-written)
    :attribute compartment_types_to_stratify: list
        the compartments that are being stratified at this round of model stratification
    :attribute final_parameter_functions: dict
        a function representing each parameter that will be implemented during integration,
            constructed recursively for stratification
    :attribute full_stratifications_list: list
        all the stratification names implemented so far that apply to all of the compartment types
    :attribute heterogeneous_mixing: bool
        whether any stratification has requested heterogeneous mixing, such that it will be implemented
    :attribute infectious_compartments: tuple
        all of the compartment stems that represent compartments with some degree of infectiousness
    :attribute infectious_indices: dict
        keys are strains being implemented with "all_strains" an additional standard key, such that models that are not
            stratified by strain will only have the key "all_strains"
        values are lists of the indices of the compartments that are infectious for that strain (or overall)
    :attribute infectious_denominators: float
        total size of the population, which effective infectious population will be divided through by in the case of
            frequency-dependent transmission
    :attribute infectious_populations: dict
        keys are strains
        values are lists with each list element representing a mixing category, so that this can be multiplied through
            by a row of the mixing matrix
    :attribute infectiousness_adjustments: dict
        user-submitted adjustments to infectiousness for the stratification currently being implemented
    :attribute infectiousness_levels: dict
        keys are any strata for any stratification for which infectiousness will be adjusted, which does not need to be
            exhaustive
        values are their relative multipliers
    :attribute infectiousness_multipliers: list
        multipliers for the relative infectiousness of each compartment attributable to stratification, regardless of
            whether they are actually infectious compartments or not and with arbitrary values which start from one and
            are then modified by the user requests
    :attribute mixing_categories: list
        the effective mixing categories, which consists of all the possible combinations of all the strata within the
            model's full stratifications that incorporate heterogeneous mixing
        contents are strings joined with the standard linking character
    :attribute mixing_denominator_indices: dict
        keys are te mixing categories
        values are lists of the indices that should be used to calculate the infectious population for that mixing
            category
    :attribute mixing_matrix: numpy array
        array formed by taking the kronecker product of all the mixing matrices provided for full stratifications for
            which heterogeneous mixing was requested
    :attribute mortality_components: dict
        keys for the name of each compartment, values the list of functions needed to recursively create the functions
            to calculate the mortality rates for each compartment
    :attribute overwrite_character: str
        standard string (usually single character and currently "W") to indicate that a stratum request is intended to
            over-write less stratified parameters
    :attribute overwrite_key: str
        standard string used by model to identify the dictionary element that represents the over-write parameters,
            rather than a request to a particular stratum
    :attribute overwrite_parameters: list
        parameters which will result in all the less stratified parameters closer to the stratification tree's trunk
            being ignored
    :attribute parameter_components: dict
        keys for the name of each transition parameter, values the list of functions needed to recursively create the
            functions to create these parameter values
    :attribute parameters: dict
        same format as for EpiModel (but described here again given the other parameter-related attributes)
        unprocessed parameters, which may be either float values or strings pointing to the keys of time_variants
    :attribute removed_compartments: list
        all unstratified compartments that have been removed through the stratification process
    :attribute overwrite_parameters: list
        any parameters that are intended as absolute values to be applied to that stratum and not multipliers for the
            unstratified parameter further up the tree
    :attribute strain_mixing_elements: dict
        first tier of keys is strains
        second tier of keys is mixing categories
        content of lists at lowest/third tier is the indices of the compartments that are relevant to this strain and
            category
    :attribute strain_mixing_multipliers: dict
        first tier of keys is strains
        second tier of keys is mixing categories
        content of lists at lowest/third tier is the final infectiousness multiplier for the compartments for this
            strain and category
    :attribute strains: list
        the strata to the strains stratification with specific behaviour
    """

    def __init__(
        self,
        times,
        compartment_types,
        initial_conditions,
        parameters,
        requested_flows,
        infectious_compartment=(Compartment.EARLY_INFECTIOUS,),
        birth_approach=BirthApproach.NO_BIRTH,
        verbose=False,
        reporting_sigfigs=4,
        entry_compartment=Compartment.SUSCEPTIBLE,
        starting_population=1,
        output_connections=None,
        death_output_categories=None,
        derived_output_functions=None,
        ticker=False,
    ):
        super().__init__(
            times,
            compartment_types,
            initial_conditions,
            parameters,
            requested_flows,
            infectious_compartment,
            birth_approach,
            verbose,
            reporting_sigfigs,
            entry_compartment,
            starting_population,
            output_connections,
            death_output_categories,
            derived_output_functions,
            ticker,
        )
        self.full_stratification_list = []
        self.removed_compartments = []
        self.overwrite_parameters = []
        self.compartment_types_to_stratify = []
        self.strains = []
        self.mixing_categories = []
        self.unstratified_compartment_names = []
        self.all_stratifications = {}
        self.infectiousness_adjustments = {}
        self.final_parameter_functions = {}
        self.adaptation_functions = {}
        self.infectiousness_levels = {}
        self.infectious_indices = {}
        self.infectious_compartments = {}
        self.infectiousness_multipliers = {}
        self.parameter_components = {}
        self.mortality_components = {}
        self.infectious_populations = {}
        self.strain_mixing_elements = {}
        self.strain_mixing_multipliers = {}
        self.strata_indices = {}
        self.target_props = {}
        self.cumulative_target_props = {}
        self.individual_infectiousness_adjustments = []
        self.heterogeneous_mixing = False
        self.mixing_matrix = None
        self.available_death_rates = [""]
        self.dynamic_mixing_matrix = False
        self.mixing_indices = {}
        self.infectious_denominators = []

    """
    stratification methods
    """

    def stratify(
        self,
        stratification_name: str,
        strata_request: List[str],
        compartment_types_to_stratify: List[str],
        requested_proportions: Dict[str, float] = {},
        entry_proportions: Dict[str, float] = {},
        adjustment_requests: Dict[str, Dict[str, float]] = {},
        infectiousness_adjustments: Dict[str, float] = {},
        mixing_matrix: numpy.ndarray = None,
        target_props: Dict[str, Dict[str, float]] = None,
        verbose: bool = False,
    ):
        """
        calls to initial preparation, checks and methods that stratify the various aspects of the model

        :param stratification_name:
            see prepare_and_check_stratification
        :param strata_request:
            see find_strata_names_from_input
        :param compartment_types_to_stratify:
            see check_compartment_request
        :param adjustment_requests:
            see incorporate_alternative_overwrite_approach and check_parameter_adjustment_requests
        :param requested_proportions:
            see prepare_starting_proportions
        :param entry_proportions:

        :param infectiousness_adjustments:

        :param mixing_matrix:
            see check_mixing
        :param verbose: bool
            whether to report on progress
            note that this can be changed at this stage from what was requested at the original unstratified model
                construction
        :param target_props: dict
            keys are the strata being implemented at this call to stratify
            values are the desired proportions to target
        """
        if not compartment_types_to_stratify:
            # Stratify all compartments.
            self.compartment_types_to_stratify = self.compartment_types
            self.full_stratification_list.append(stratification_name)
        else:
            self.compartment_types_to_stratify = compartment_types_to_stratify
        # Check age stratification
        if stratification_name == "age":
            # Ensure age strata are sorted... for some reason?
            strata_names = sorted(strata_request)
        elif stratification_name == "strain":
            # Track strains. (why?)
            self.strains = strata_request

        strata_names = [str(s) for s in strata_request]
        self.all_stratifications[stratification_name] = strata_names
        requested_proportions = utils.get_all_proportions(strata_names, requested_proportions)
        adjustment_requests = utils.parse_param_adjustment_overwrite(
            strata_names, adjustment_requests
        )

        # Retain copy of compartment names in their stratified form to refer back to during stratification process
        self.unstratified_compartment_names = copy.copy(self.compartment_names)

        # Stratify compartments, split according to split_proportions
        to_add, to_remove = utils.get_stratified_compartments(
            stratification_name,
            strata_names,
            self.compartment_types_to_stratify,
            requested_proportions,
            self.compartment_names,
            self.compartment_values,
        )
        for name, value in to_add.items():
            # Add new stratified compartments
            self.compartment_names.append(name)
            self.compartment_values.append(value)

        for name in to_remove:
            # Remove the original compartments, since they have now been stratified.
            remove_idx = self.compartment_names.index(name)
            del self.compartment_values[remove_idx]
            del self.compartment_names[remove_idx]

        if stratification_name == "age":
            # Work out ageing flows.
            # This comes first, so that the compartment names remain in the unstratified form
            # .... why do we need that?
            ageing_params, ageing_flows = utils.create_ageing_flows(
                strata_names, self.unstratified_compartment_names, len(self.all_stratifications)
            )
            self.transition_flows = self.transition_flows.append(ageing_flows, ignore_index=True)
            self.parameters.update(ageing_params)

        # Stratify the transition flows
        (
            new_flows,
            overwritten_parameter_adjustment_names,
            param_updates,
            adaptation_function_updates,
        ) = utils.stratify_transition_flows(
            stratification_name,
            strata_names,
            adjustment_requests,
            self.compartment_types_to_stratify,
            list(self.transition_flows.T.to_dict().values()),
            len(self.all_stratifications),
        )
        self.overwrite_parameters += overwritten_parameter_adjustment_names
        self.parameters.update(param_updates)
        self.adaptation_functions.update(adaptation_function_updates)

        # Update the customised flow functions.
        num_flows = len(self.transition_flows)
        for idx, new_flow in enumerate(new_flows):
            if new_flow["type"] == Flow.CUSTOM:
                new_idx = num_flows + idx
                self.customised_flow_functions[new_idx] = self.customised_flow_functions[n_flow]

        if new_flows:
            self.transition_flows = self.transition_flows.append(new_flows, ignore_index=True)

        # Stratify the entry flows
        if self.entry_compartment in self.compartment_types_to_stratify:
            param_updates, time_variant_updates = utils.stratify_entry_flows(
                stratification_name, strata_names, entry_proportions, self.time_variants,
            )
            self.parameters.update(param_updates)
            self.time_variants.update(time_variant_updates)

        # =========== UP TO HERE

        if self.death_flows.shape[0] > 0:
            self.stratify_death_flows(stratification_name, strata_names, adjustment_requests)

        self.stratify_universal_death_rate(
            stratification_name, strata_names, adjustment_requests, compartment_types_to_stratify,
        )

        # if stratifying by strain
        self.strains = strata_names if stratification_name == "strain" else self.strains

        # check submitted mixing matrix and combine with existing matrix, if any
        self.prepare_mixing_matrix(mixing_matrix, stratification_name, strata_names)

        # prepare infectiousness levels attribute
        self.prepare_infectiousness_levels(
            stratification_name, strata_names, infectiousness_adjustments
        )

        # prepare strata equilibration target proportions
        if target_props:
            self.prepare_and_check_target_props(target_props, stratification_name, strata_names)

    def add_adjusted_parameter(
        self, _unadjusted_parameter, _stratification_name, _stratum, _adjustment_requests,
    ):
        """
        find the adjustment request that is relevant to a particular unadjusted parameter and stratum and add the
            parameter value (str for function or float) to the parameters dictionary attribute
        otherwise allow return of None

        :param _unadjusted_parameter:
            name of the unadjusted parameter value
        :param _stratification_name:
            see prepare_and_check_stratification
        :param _stratum:
            stratum being considered by the method calling this method
        :param _adjustment_requests:
            see incorporate_alternative_overwrite_approach and check_parameter_adjustment_requests
        :return: parameter_adjustment_name: str or None
            if returned as None, assumption will be that the original, unstratified parameter should be used
            otherwise create a new parameter name and value and store away in the appropriate model structure
        """
        parameter_adjustment_name = None
        relevant_adjustment_request = self.find_relevant_adjustment_request(
            _adjustment_requests, _unadjusted_parameter
        )
        if relevant_adjustment_request is not None:
            parameter_adjustment_name = (
                create_stratified_name(_unadjusted_parameter, _stratification_name, _stratum)
                if _stratum in _adjustment_requests[relevant_adjustment_request]
                else _unadjusted_parameter
            )
            self.output_to_user(
                "\t parameter for %s stratum of %s stratification is called %s"
                % (_stratum, _stratification_name, parameter_adjustment_name)
            )
            if _stratum in _adjustment_requests[relevant_adjustment_request]:
                self.parameters[parameter_adjustment_name] = _adjustment_requests[
                    relevant_adjustment_request
                ][_stratum]

            # record the parameters that over-write the less stratified parameters closer to the trunk of the tree
            if (
                OVERWRITE_KEY in _adjustment_requests[relevant_adjustment_request]
                and _stratum in _adjustment_requests[relevant_adjustment_request][OVERWRITE_KEY]
            ):
                self.overwrite_parameters.append(parameter_adjustment_name)
        return parameter_adjustment_name

    def find_relevant_adjustment_request(self, _adjustment_requests, _unadjusted_parameter):
        """
        find the adjustment requests that are extensions of the base parameter type being considered
        expected behaviour is as follows:
        * if there are no submitted requests (keys to the adjustment requests) that are extensions of the unadjusted
            parameter, will return None
        * if there is one submitted request that is an extension of the unadjusted parameter, will return that parameter
        * if there are multiple submitted requests that are extensions to the unadjusted parameter and one is more
            stratified than any of the others (i.e. more instances of the "X" string), will return this most stratified
            parameter
        * if there are multiple submitted requests that are extensions to the unadjusted parameter and several of them
            are equal in having the greatest extent of stratification, will return the longest string

        :param _unadjusted_parameter:
            see add_adjusted_parameter
        :param _adjustment_requests:
            see prepare_and_check_stratification
        :return: str or None
            the key of the adjustment request that is applicable to the parameter of interest if any, otherwise None
        """

        # find all the requests that start with the parameter of interest and their level of stratification
        applicable_params = [
            param for param in _adjustment_requests if _unadjusted_parameter.startswith(param)
        ]
        applicable_param_n_stratifications = [
            len(find_name_components(param)) for param in applicable_params
        ]
        if applicable_param_n_stratifications:
            max_length_indices = [
                i_p
                for i_p, p in enumerate(applicable_param_n_stratifications)
                if p == max(applicable_param_n_stratifications)
            ]
            candidate_params = [applicable_params[i] for i in max_length_indices]
            return max(candidate_params, key=len)
        else:
            return None

    def sort_absent_transition_parameter(
        self,
        _stratification_name,
        _strata_names,
        _stratum,
        _stratify_from,
        _stratify_to,
        unstratified_name,
    ):
        """
        work out what to do if a specific transition parameter adjustment has not been requested

        :param _stratification_name:
            see prepare_and_check_stratification
        :param _strata_names:
            see find_strata_names_from_input
        :param _stratum:
        :param _stratify_from:
            see add_stratified_flows
        :param _stratify_to:
            see add_stratified_flows
        :param unstratified_name: str
            the name of the parameter before the stratification is implemented
        :return: str
            parameter name for revised parameter than wasn't provided
        """

        # default behaviour if not specified is to split the parameter into equal parts if to compartment is split
        if not _stratify_from and _stratify_to:
            self.output_to_user(
                "\t splitting existing parameter value %s into %s equal parts"
                % (unstratified_name, len(_strata_names))
            )
            parameter_name = create_stratified_name(
                unstratified_name, _stratification_name, _stratum
            )
            self.parameters[parameter_name] = 1.0 / len(_strata_names)
            self.adaptation_functions[parameter_name] = create_multiplicative_function(
                1.0 / len(_strata_names)
            )
            return parameter_name

        # otherwise if no request, retain the existing parameter
        else:
            self.output_to_user("\tretaining existing parameter value %s" % unstratified_name)
            return unstratified_name

    def stratify_death_flows(self, _stratification_name, _strata_names, _adjustment_requests):
        """
        add compartment-specific death flows to death_flows data frame attribute

        :param _stratification_name:
            see prepare_and_check_stratification
        :param _strata_names:
             see find_strata_names_from_input
        :param _adjustment_requests:
            see incorporate_alternative_overwrite_approach and check_parameter_adjustment_requests
        """
        for n_flow in self.find_death_indices_to_implement(back_one=1):

            # if the compartment with an additional death flow is being stratified
            if find_stem(self.death_flows.origin[n_flow]) in self.compartment_types_to_stratify:
                for stratum in _strata_names:

                    # get stratified parameter name if requested to stratify, otherwise use the unstratified one
                    parameter_name = self.add_adjusted_parameter(
                        self.death_flows.parameter[n_flow],
                        _stratification_name,
                        stratum,
                        _adjustment_requests,
                    )
                    if not parameter_name:
                        parameter_name = self.death_flows.parameter[n_flow]

                    # add the stratified flow to the death flows data frame
                    self.death_flows = self.death_flows.append(
                        {
                            "type": self.death_flows.type[n_flow],
                            "parameter": parameter_name,
                            "origin": create_stratified_name(
                                self.death_flows.origin[n_flow], _stratification_name, stratum,
                            ),
                            "implement": len(self.all_stratifications),
                        },
                        ignore_index=True,
                    )

            # otherwise if not part of the stratification, accept the existing flow and increment the implement value
            else:
                new_flow = self.death_flows.loc[n_flow, :].to_dict()
                new_flow["implement"] += 1
                self.death_flows = self.death_flows.append(new_flow, ignore_index=True)

    def stratify_universal_death_rate(
        self,
        _stratification_name,
        _strata_names,
        _adjustment_requests,
        _compartment_types_to_stratify,
    ):
        """
        stratify the approach to universal, population-wide deaths (which can be made to vary by stratum)
        adjust every parameter that refers to the universal death rate, according to user request if submitted and
            otherwise populated with a value of one by default

        :param _stratification_name:
            see prepare_and_check_stratification
        :param _strata_names:
            see find_strata_names_from_input
        :param _adjustment_requests:
            see incorporate_alternative_overwrite_approach and check_parameter_adjustment_requests
        :param _compartment_types_to_stratify:
            see above
        """
        if (
            _stratification_name not in self.full_stratification_list
            and "universal_death_rate" in _adjustment_requests
        ):
            raise ValueError(
                "universal death rate can only be stratified when applied to all compartment types"
            )
        elif _stratification_name not in self.full_stratification_list:
            self.output_to_user(
                "universal death rate not adjusted as stratification not applied to all compartments"
            )
            return

        # ensure baseline function available for modification in universal death rates
        self.adaptation_functions["universal_death_rateX"] = (
            self.time_variants["universal_death_rate"]
            if "universal_death_rate" in self.time_variants
            else lambda time: self.parameters["universal_death_rate"]
        )

        # if stratification applied to all compartment types
        for stratum in _strata_names:
            if (
                "universal_death_rate" in _adjustment_requests
                and stratum in _adjustment_requests["universal_death_rate"]
            ):
                stratum_name = create_stratum_name(_stratification_name, stratum, joining_string="")
                self.available_death_rates.append(stratum_name)

                # use existing function or create new one from constant as needed
                if type(_adjustment_requests["universal_death_rate"][stratum]) == str:
                    self.adaptation_functions[
                        "universal_death_rateX" + stratum_name
                    ] = self.time_variants[_adjustment_requests["universal_death_rate"][stratum]]
                elif isinstance(
                    _adjustment_requests["universal_death_rate"][stratum], (int, float)
                ):
                    self.adaptation_functions[
                        "universal_death_rateX" + stratum_name
                    ] = create_multiplicative_function(
                        self.time_variants[_adjustment_requests["universal_death_rate"][stratum]]
                    )

                # record the parameters that over-write the less stratified parameters closer to the trunk of the tree
                if (
                    OVERWRITE_KEY in _adjustment_requests["universal_death_rate"]
                    and stratum in _adjustment_requests["universal_death_rate"][OVERWRITE_KEY]
                ):
                    self.overwrite_parameters.append(
                        create_stratified_name(
                            "universal_death_rate", _stratification_name, stratum
                        )
                    )

    def prepare_mixing_matrix(self, _mixing_matrix, _stratification_name, _strata_names):
        """
        check that the mixing matrix has been correctly specified and call the other relevant functions

        :param _mixing_matrix: numpy array
            must be square
            represents the mixing of the strata within this stratification
        :param _stratification_name: str
            the name of the stratification - i.e. the reason for implementing this type of stratification
        :param _strata_names: list
            see find_strata_names_from_input
        """
        if _mixing_matrix is None:
            return
        elif type(_mixing_matrix) != numpy.ndarray:
            raise ValueError("submitted mixing matrix is wrong data type")
        elif len(_mixing_matrix.shape) != 2:
            raise ValueError("submitted mixing matrix is not two-dimensional")
        elif _mixing_matrix.shape[0] != _mixing_matrix.shape[1]:
            raise ValueError("submitted mixing is not square")
        elif _mixing_matrix.shape[0] != len(_strata_names):
            raise ValueError("mixing matrix does not sized to number of strata being implemented")
        self.combine_new_mixing_matrix_with_existing(
            _mixing_matrix, _stratification_name, _strata_names
        )

    def combine_new_mixing_matrix_with_existing(
        self, _mixing_matrix, _stratification_name, _strata_names
    ):
        """
        master mixing matrix function to take in a new mixing matrix and combine with the existing ones

        :param _mixing_matrix: numpy array
            array, which must be square representing the mixing of the strata within this stratification
        :param _stratification_name: str
            the name of the stratification - i.e. the reason for implementing this type of stratification
        :param _strata_names: list
            see find_strata_names_from_input
        """

        # if no mixing matrix yet, just convert the existing one to a dataframe
        if self.mixing_matrix is None:
            self.mixing_categories = [_stratification_name + "_" + i for i in _strata_names]
            self.mixing_matrix = _mixing_matrix

        # otherwise take the kronecker product to get the new mixing matrix
        else:
            self.mixing_categories = [
                old_strata + "X" + _stratification_name + "_" + new_strata
                for old_strata, new_strata in itertools.product(
                    self.mixing_categories, _strata_names
                )
            ]
            self.mixing_matrix = numpy.kron(self.mixing_matrix, _mixing_matrix)

    def prepare_infectiousness_levels(
        self, _stratification_name, _strata_names, _infectiousness_adjustments
    ):
        """
        store infectiousness adjustments as dictionary attribute to the model object, with first tier of keys the
            stratification and second tier the strata to be modified

        :param _stratification_name:
            see prepare_and_check_stratification
        :param _strata_names:
             see find_strata_names_from_input
        :param _infectiousness_adjustments: dict
            requested adjustments to infectiousness for this stratification
        """
        if type(_infectiousness_adjustments) != dict:
            raise ValueError("infectiousness adjustments not submitted as dictionary")
        elif not all(key in _strata_names for key in _infectiousness_adjustments.keys()):
            raise ValueError("infectiousness adjustment key not in strata being implemented")
        else:
            for stratum in _infectiousness_adjustments:
                self.infectiousness_levels[
                    create_stratum_name(_stratification_name, stratum, joining_string="")
                ] = _infectiousness_adjustments[stratum]

    def prepare_and_check_target_props(self, _target_props, _stratification_name, _strata_names):
        """
        create the dictionary of dictionaries that contains the target values for equlibration

        :parameters:
            _target_props: dict
                user submitted dictionary with keys the restrictions by previously implemented strata that apply
            _stratification_name: str
                name of stratification process currently being implemented
            _strata_names: list
                list of the names of the strata being implemented under the current stratification process
        """
        self.target_props[_stratification_name] = {}
        for restriction in _target_props:
            self.target_props[_stratification_name][restriction] = {}

            # only need parameter values for the first n-1 strata, as the last one will be the remainder
            for stratum in _strata_names[:-1]:
                if stratum not in _target_props[restriction]:
                    raise ValueError(
                        "one or more of first n-1 strata being applied not in the target prop request"
                    )
                elif isinstance(_target_props[restriction][stratum], (float, int, str)):
                    self.target_props[_stratification_name][restriction][stratum] = _target_props[
                        restriction
                    ][stratum]
                else:
                    raise ValueError("target proportions specified with incorrect format for value")
                if (
                    type(_target_props[restriction][stratum]) == str
                    and _target_props[restriction][stratum] not in self.time_variants
                ):
                    raise ValueError("function for prevalence of %s not found" % stratum)
            if _strata_names[-1] in self.target_props:
                self.output_to_user(
                    "target proportion requested for stratum %s, but as last stratum"
                    % _strata_names[-1]
                    + " in request, this will be ignored and assigned the remainder to ensure sum to one"
                )

            # add the necessary flows to the transition data frame
            self.link_strata_with_flows(_stratification_name, _strata_names, restriction)

    def link_strata_with_flows(self, _stratification_name, _strata_names, _restriction):
        """
        add in sequential series of flows between neighbouring strata that transition people between the strata being
            implemented in this stratification stage

        :parameters:
            _stratification_name: str
                name of stratification currently being implemented
            _strata_names: list
                list of the strata being implemented in this stratification process
            _restriction: str
                name of previously implemented stratum that this equilibration flow applies to, if any, otherwise "all"
        """
        for compartment in self.unstratified_compartment_names:
            if _restriction in find_name_components(compartment) or _restriction == "all":
                for n_stratum in range(len(_strata_names[:-1])):
                    self.transition_flows = self.transition_flows.append(
                        {
                            "type": Flow.STRATA_CHANGE,
                            "parameter": _stratification_name
                            + "X"
                            + _restriction
                            + "X"
                            + _strata_names[n_stratum]
                            + "_"
                            + _strata_names[n_stratum + 1],
                            "origin": create_stratified_name(
                                compartment, _stratification_name, _strata_names[n_stratum],
                            ),
                            "to": create_stratified_name(
                                compartment, _stratification_name, _strata_names[n_stratum + 1],
                            ),
                            "implement": len(self.all_stratifications),
                            "strain": float("nan"),
                        },
                        ignore_index=True,
                    )

    """
    pre-integration methods
    """

    def prepare_to_run(self):
        """
        methods that can be run prior to integration to save various function calls being made at every time step
        """
        self.prepare_stratified_parameter_calculations()
        self.prepare_infectiousness_calculations()
        self.transition_indices_to_implement = self.find_transition_indices_to_implement()
        self.death_indices_to_implement = self.find_death_indices_to_implement()
        self.change_indices_to_implement = self.find_change_indices_to_implement()

        # ensure there is a universal death rate available even if the model hasn't been stratified at all
        if len(self.all_stratifications) == 0 and isinstance(
            self.parameters["universal_death_rate"], (float, int)
        ):
            self.final_parameter_functions["universal_death_rate"] = lambda time: self.parameters[
                "universal_death_rate"
            ]
        elif (
            len(self.all_stratifications) == 0
            and type(self.parameters["universal_death_rate"]) == str
        ):
            self.final_parameter_functions["universal_death_rate"] = self.adaptation_functions[
                "universal_death_rate"
            ]

        self.find_strata_indices()
        self.prepare_lookup_tables()

    def find_strata_indices(self):
        for stratif in self.all_stratifications:
            self.strata_indices[stratif] = {}
            for i_stratum, stratum in enumerate(self.all_stratifications[stratif]):
                self.strata_indices[stratif][stratum] = [
                    i_comp
                    for i_comp in range(len(self.compartment_names))
                    if create_stratum_name(
                        stratif, self.all_stratifications[stratif][i_stratum], joining_string="",
                    )
                    in find_name_components(self.compartment_names[i_comp])
                ]

    def prepare_stratified_parameter_calculations(self):
        """
        prior to integration commencing, work out what the components are of each parameter being implemented
        populates self.parameter_components even though it is not needed elsewhere, to allow that the components that
            were used to create each given parameter can be determined later
        """

        # create list of all the parameters that we need to find the set of adjustment functions for
        parameters_to_adjust = []

        transition_flow_indices = [
            n_flow
            for n_flow, flow in enumerate(self.transition_flows.type)
            if "change" not in flow
            and self.transition_flows.implement[n_flow] == len(self.all_stratifications)
        ]

        for n_flow in transition_flow_indices:
            if (
                self.transition_flows.implement[n_flow] == len(self.all_stratifications)
                and self.transition_flows.parameter[n_flow] not in parameters_to_adjust
            ):
                parameters_to_adjust.append(self.transition_flows.parameter[n_flow])
        for n_flow in range(self.death_flows.shape[0]):
            if (
                self.death_flows.implement[n_flow] == len(self.all_stratifications)
                and self.death_flows.parameter[n_flow] not in parameters_to_adjust
            ):
                parameters_to_adjust.append(self.death_flows.parameter[n_flow])

        # and adjust
        for parameter in parameters_to_adjust:
            self.parameter_components[parameter] = self.find_transition_components(parameter)
            self.create_transition_functions(parameter, self.parameter_components[parameter])

        # similarly for all model compartments
        for compartment in self.compartment_names:
            self.mortality_components[compartment] = self.find_mortality_components(compartment)
            if len(self.all_stratifications) > 0:
                self.create_mortality_functions(compartment, self.mortality_components[compartment])

    def find_mortality_components(self, _compartment):
        """
        find the sub-parameters for population-wide natural mortality that are relevant to a particular compartment
        used in prepare_stratified_parameter_calculations for creating functions to find the mortality rate for each
            compartment
        similar to find_transition_components, except being applied by compartment rather than parameter

        :param _compartment: str
            name of the compartment of interest
        :return: all_sub_parameters: list
            list of all the mortality-related sub-parameters for the compartment of interest
        """
        all_sub_parameters = []
        compartments_strata = find_name_components(_compartment)[1:]
        compartments_strata.reverse()
        compartments_strata.append("")

        # loop through each stratification of the parameter and adapt if the parameter is available
        for stratum in compartments_strata:
            if stratum in self.available_death_rates:
                all_sub_parameters.append("universal_death_rateX" + stratum)
            if "universal_death_rateX" + stratum in self.overwrite_parameters:
                break
        all_sub_parameters.reverse()
        return all_sub_parameters

    def create_mortality_functions(self, _compartment, _sub_parameters):
        """
        loop through all the components to the population-wide mortality and create the recursive functions

        :param _compartment: str
            name of the compartment of interest
        :param _sub_parameters: list
            the names of the functions that need to update the upstream parameters
        :return:
        """
        self.final_parameter_functions[
            "universal_death_rateX" + _compartment
        ] = self.adaptation_functions[_sub_parameters[0]]
        for component in _sub_parameters[1:]:

            # get the new function to act on the less stratified function (closer to the "tree-trunk")
            if component not in self.parameters:
                raise ValueError(
                    "parameter component %s not found in parameters attribute" % component
                )
            elif type(self.parameters[component]) == float:
                self.adaptation_functions[component] = create_multiplicative_function(
                    self.parameters[component]
                )
            elif type(self.parameters[component]) == str:
                self.adaptation_functions[component] = create_time_variant_multiplicative_function(
                    self.adaptation_functions[component]
                )
            else:

                raise ValueError("parameter component %s not appropriate format" % component)

            # create the composite function
            self.final_parameter_functions[
                "universal_death_rateX" + _compartment
            ] = create_function_of_function(
                self.adaptation_functions[component],
                self.final_parameter_functions["universal_death_rateX" + _compartment],
            )

    def find_transition_components(self, _parameter):
        """
        finds each of the strings for the functions acting on the next function in the sequence

        :param _parameter: str
            full name of the parameter of interest
        """
        sub_parameters = []

        # work backwards to allow stopping for overwriting requests, then reverse in preparation for function creation
        for x_instance in extract_reversed_x_positions(_parameter):
            component = _parameter[:x_instance]
            sub_parameters.append(component)
            if component in self.overwrite_parameters:
                break
        sub_parameters.reverse()
        return sub_parameters

    def create_transition_functions(self, _parameter, _sub_parameters):
        """
        builds up each parameter to be implemented as a function, recursively creating an outer function that calls the
            inner function

        :param _parameter: str
            full name of the parameter of interest
        :param _sub_parameters: list
            list of the strings representing the sub-parameters, including the base parameter as the stem and with all
                of the relevant strata in the stratification sequence following
        """

        # start from base value as a function of time, even if the time argument is ignored
        if isinstance(self.parameters[_sub_parameters[0]], (float, int)):
            self.final_parameter_functions[_parameter] = lambda time: self.parameters[
                _sub_parameters[0]
            ]
        elif type(self.parameters[_sub_parameters[0]]) == str:
            self.final_parameter_functions[_parameter] = self.adaptation_functions[
                _sub_parameters[0]
            ]

        # then cycle through other applicable components and extend function recursively, only if component available
        for component in _sub_parameters[1:]:

            # get the new function to act on the less stratified function (closer to the "tree-trunk")
            if component not in self.parameters:
                raise ValueError(
                    "parameter component %s not found in parameters attribute" % component
                )
            elif isinstance(self.parameters[component], float) or isinstance(
                self.parameters[component], int
            ):
                self.adaptation_functions[component] = create_multiplicative_function(
                    self.parameters[component]
                )
            elif type(self.parameters[component]) == str:
                self.adaptation_functions[component] = create_time_variant_multiplicative_function(
                    self.time_variants[self.parameters[component]]
                )
            else:
                raise ValueError("parameter component %s not appropriate format" % component)

            # create the composite function
            self.final_parameter_functions[_parameter] = create_function_of_function(
                self.adaptation_functions[component], self.final_parameter_functions[_parameter],
            )

    def prepare_infectiousness_calculations(self):
        """
        master method to run all the code concerned with preparation for force of infection calculations
        """

        # infectiousness preparations
        self.prepare_all_infectiousness_multipliers()
        self.find_infectious_indices()

        # mixing preparations
        if self.mixing_matrix is not None:
            self.add_force_indices_to_transitions()
        self.find_mixing_denominators()

        # reconciling the strains and the mixing attributes together into one structure
        self.find_strain_mixing_multipliers()

    def prepare_all_infectiousness_multipliers(self):
        """
        find the infectiousness multipliers for each compartment being implemented in the model
        """

        # start from assumption that each compartment is fully and equally infectious
        self.infectiousness_multipliers = [1.0] * len(self.compartment_names)

        # if infectiousness modification requested for the compartment type, multiply through by the current value
        for n_comp, compartment in enumerate(self.compartment_names):
            for modifier in self.infectiousness_levels:
                if modifier in find_name_components(compartment):
                    self.infectiousness_multipliers[n_comp] *= self.infectiousness_levels[modifier]

        self.make_further_infectiousness_adjustments()

    def make_further_infectiousness_adjustments(self):
        """
        Work through specific requests for specific adjustments, to escape the requirement to only adjust compartment
        infectiousness according to stratification process - with all infectious compartments having the same
        adjustment.
        """
        for i_adjustment in range(len(self.individual_infectiousness_adjustments)):
            for i_comp, comp in enumerate(self.compartment_names):
                if all(
                    [
                        component in find_name_components(comp)
                        for component in self.individual_infectiousness_adjustments[i_adjustment][0]
                    ]
                ):
                    self.infectiousness_multipliers[
                        i_comp
                    ] = self.individual_infectiousness_adjustments[i_adjustment][1]

    def find_infectious_indices(self):
        """
        find the infectious indices by strain and overall, as opposed to just overall in EpiModel
        note that this changes the structure by one hierarchical level compared to EpiModel - in that previously we had
            self.infectious_indices a list of infectious indices and now it is has a dictionary structure at the highest
            level, followed by keys for each strain with values being lists that are equivalent to the
            self.infectious_indices list for the unstratified version
        """

        # find the indices for the compartments that are infectious across all strains
        self.infectious_indices["all_strains"] = self.find_all_infectious_indices()

        # then find the infectious compartment for each strain separately
        for strain in self.strains:
            self.infectious_indices[strain] = convert_boolean_list_to_indices(
                [
                    create_stratum_name("strain", strain, joining_string="")
                    in find_name_components(comp)
                    and i_comp in self.infectious_indices["all_strains"]
                    for i_comp, comp in enumerate(self.compartment_names)
                ]
            )

    def add_force_indices_to_transitions(self):
        """
        find the indices from the force of infection vector to be applied for each infection flow and populate to the
            force_index column of the flows frame
        """

        # identify the indices of all the infection-related flows to be implemented
        infection_flow_indices = [
            n_flow
            for n_flow, flow in enumerate(self.transition_flows.type)
            if "infection" in flow
            and self.transition_flows.implement[n_flow] == len(self.all_stratifications)
        ]

        # loop through and find the index of the mixing matrix applicable to the flow, of which there should be only one
        for n_flow in infection_flow_indices:
            found = False
            for i_group, force_group in enumerate(self.mixing_categories):
                if all(
                    stratum in find_name_components(self.transition_flows.origin[n_flow])
                    for stratum in find_name_components(force_group)
                ):
                    self.transition_flows.force_index[n_flow] = i_group
                    if found:
                        raise ValueError(
                            "mixing group found twice for transition flow number %s" % n_flow
                        )
                    found = True
                    continue
            if not found:
                raise ValueError("mixing group not found for transition flow number %s" % n_flow)

    def find_mixing_denominators(self):
        """
        for each mixing category, create a list of the compartment numbers that are relevant

        :return mixing_indices: list
            indices of the compartments that are applicable to a particular mixing category
        """
        if self.mixing_matrix is None:
            self.mixing_indices = {"all_population": range(len(self.compartment_names))}
        else:
            for category in self.mixing_categories:
                self.mixing_indices[category] = [
                    i_comp
                    for i_comp, compartment in enumerate(self.compartment_names)
                    if all(
                        [
                            component in find_name_components(compartment)
                            for component in find_name_components(category)
                        ]
                    )
                ]

        self.mixing_indices_arr = np.array(list(self.mixing_indices.values()))

    def find_strain_mixing_multipliers(self):
        """
        find the relevant indices to be used to calculate the force of infection contribution to each strain from each
            mixing category as a list of indices - and separately find multipliers as a list of the same length for
            their relative infectiousness extracted from self.infectiousness_multipliers
        """
        for strain in self.strains + ["all_strains"]:
            (self.strain_mixing_elements[strain], self.strain_mixing_multipliers[strain],) = (
                {},
                {},
            )
            for category in (
                ["all_population"] if self.mixing_matrix is None else self.mixing_categories
            ):
                self.strain_mixing_elements[strain][category] = numpy.array(
                    [
                        index
                        for index in self.mixing_indices[category]
                        if index in self.infectious_indices[strain]
                    ]
                )
                self.strain_mixing_multipliers[strain][category] = numpy.array(
                    [
                        self.infectiousness_multipliers[i_comp]
                        for i_comp in self.strain_mixing_elements[strain][category]
                    ]
                )

    def find_transition_indices_to_implement(
        self, back_one: int = 0, include_change: bool = False
    ) -> List[int]:
        """
        Finds all the indices of the transition flows that need to be stratified,
        Overrides the version in the unstratified EpiModel

        :parameters:
            back_one: int
                number to subtract from self.all_stratification, which will be one if this method is being called after the
                    stratification has been added
            include_change: bool
                whether to include the strata_change transition flows
        :return: list
            list of indices of the flows that need to be stratified
        """
        return [
            idx
            for idx, flow in self.transition_flows.iterrows()
            if (flow.type != Flow.STRATA_CHANGE or include_change)
            and flow.implement == len(self.all_stratifications) - back_one
        ]

    def find_change_indices_to_implement(self, back_one=0):
        """
        find the indices of the equilibration flows to be applied in the transitions data frame

        :parameters:
            back_one: int
             see find_transition_indices_to_implement
        """
        return [
            idx
            for idx, flow in self.transition_flows.iterrows()
            if flow.type == Flow.STRATA_CHANGE
            and flow.implement == len(self.all_stratifications) - back_one
        ]

    def find_death_indices_to_implement(self, back_one=0):
        """
        find all the indices of the death flows that need to be stratified
        separated out as very short method in order that it can over-ride the version in the unstratified EpiModel

        :param back_one: int
            number to subtract from self.all_stratification, which will be one if this method is being called after the
                stratification has been added
        :return: list
            list of indices of the flows that need to be stratified
        """
        return self.death_flows[
            self.death_flows.implement == len(self.all_stratifications) - back_one
        ].index

    """
    methods to be called during the process of model running
    """

    # Cache return values to prevent wasteful re-computation - cache size is huge.
    # Floating point return type is 8 bytes, meaning 2**17 values is ~1MB of memory.
    # N.B this will leak memory, which is fine.
    @lru_cache(maxsize=2 ** 17)
    def get_parameter_value(self, _parameter, _time):
        """
        returns a parameter value by calling the function represented by its string within the parameter_functions
            attribute

        :param _parameter: str
            name of the parameter to be called (key to the parameter_functions dictionary)
        :param _time: float
            current time of model integration
        :return: float
            the parameter value needed
        """
        return self.final_parameter_functions[_parameter](_time)

    def find_infectious_population(self, compartment_values):
        """
        find vectors for the total infectious populations and the total population that is needed in the case of
            frequency-dependent transmission

        :param compartment_values: numpy array
            current values for the compartment sizes
        """
        strains = self.strains if self.strains else ["all_strains"]
        if self.mixing_matrix is None:
            mixing_categories = ["all_population"]
        else:
            mixing_categories = self.mixing_categories

        self.infectious_denominators = compartment_values[self.mixing_indices_arr].sum(axis=1)
        self.infectious_populations = find_infectious_populations(
            compartment_values,
            strains,
            mixing_categories,
            self.strain_mixing_elements,
            self.strain_mixing_multipliers,
        )

    def find_infectious_multiplier(self, n_flow):
        """
        find the multiplier to account for the infectious population in dynamic flows

        :param n_flow: int
            index for the row of the transition_flows data frame
        :return:
            the total infectious quantity, whether that is the number or proportion of infectious persons
            needs to return as one for flows that are not transmission dynamic infectiousness flows
        """
        flow_type = self.transition_flows_dict["type"][n_flow]
        strain = self.transition_flows_dict["strain"][n_flow]
        force_index = self.transition_flows_dict["force_index"][n_flow]

        if "infection" not in flow_type:
            return 1.0
        strain = "all_strains" if not self.strains else strain
        mixing_elements = (
            [1.0] if self.mixing_matrix is None else self.mixing_matrix[force_index, :]
        )
        denominator = (
            [1.0] * len(self.infectious_denominators)
            if "_density" in flow_type
            else self.infectious_denominators
        )

        return sum(
            element_list_division(
                element_list_multiplication(self.infectious_populations[strain], mixing_elements),
                denominator,
            )
        )

    def prepare_time_step(self, _time):
        """
        Perform any tasks needed for execution of each integration time step
        """
        if self.dynamic_mixing_matrix:
            self.mixing_matrix = self.find_dynamic_mixing_matrix(_time)

    def find_dynamic_mixing_matrix(self, _time):
        """
        Function for overwriting in application to create time-variant mixing matrix
        """
        return self.mixing_matrix

    def get_compartment_death_rate(self, _compartment, _time):
        """
        find the universal or population-wide death rate for a particular compartment

        :param _compartment: str
            name of the compartment
        :param _time: float
            current integration time
        :return: float
            death rate
        """
        return (
            self.get_parameter_value("universal_death_rateX" + _compartment, _time)
            if len(self.all_stratifications) > 0
            else self.get_parameter_value("universal_death_rate", _time)
        )

    def apply_birth_rate(self, _ode_equations, _compartment_values, _time):
        """
        apply a population-wide death rate to all compartments
        all the entry_fraction proportions should be present in either parameters or time_variants given how they are
            created in the process of implementing stratification

        :parameters: all parameters have come directly from the apply_all_flow_types_to_odes method unchanged
        """

        # find the total number of births entering the system at the current time point
        total_births = self.find_total_births(_compartment_values, _time)

        # split the total births across entry compartments
        for compartment in [
            comp for comp in self.compartment_names if find_stem(comp) == self.entry_compartment
        ]:

            # calculate adjustment to original stem entry rate
            entry_fraction = 1.0
            for stratum in find_name_components(compartment)[1:]:
                entry_fraction *= self.get_single_parameter_component(
                    "entry_fractionX%s" % stratum, _time
                )

            # apply to that compartment
            _ode_equations = increment_list_by_index(
                _ode_equations,
                self.compartment_names.index(compartment),
                total_births * entry_fraction,
            )
        return _ode_equations

    def apply_change_rates(self, _ode_equations, _compartment_values, _time):
        """
        apply the transition rates that relate to equilibrating prevalence values for a particular stratification

        :parameters:
            _ode_equations: list
                working ode equations, to which transitions are being applied
            _compartment_values: list
                working compartment values
            _time: float
                current integration time value
        """

        # for each change flow being implemented
        for i_change in self.change_indices_to_implement:

            # split out the components of the transition string, which follow the standard 6-character string "change"
            stratification, restriction, transition = find_name_components(
                self.transition_flows.parameter[i_change]
            )
            origin_stratum, _ = transition.split("_")

            # find the distribution of the population across strata to be targeted
            _cumulative_target_props = self.find_target_strata_props(
                _time, restriction, stratification
            )

            # find the proportional distribution of the population across strata at the current time point
            _cumulative_strata_props = self.find_current_strata_props(
                _compartment_values, stratification, restriction
            )

            # work out which stratum and compartment transitions should be going from and to
            if _cumulative_strata_props[origin_stratum] > _cumulative_target_props[origin_stratum]:
                take_compartment, give_compartment, numerator, denominator = (
                    self.transition_flows.origin[i_change],
                    self.transition_flows.to[i_change],
                    _cumulative_strata_props[origin_stratum],
                    _cumulative_target_props[origin_stratum],
                )

            else:
                take_compartment, give_compartment, numerator, denominator = (
                    self.transition_flows.to[i_change],
                    self.transition_flows.origin[i_change],
                    1.0 - _cumulative_strata_props[origin_stratum],
                    1.0 - _cumulative_target_props[origin_stratum],
                )

            # calculate net flow
            net_flow = (
                numpy.log(numerator / denominator)
                / STRATA_EQUILIBRATION_FACTOR
                * _compartment_values[self.compartment_names.index(take_compartment)]
            )

            # update equations
            _ode_equations = increment_list_by_index(
                _ode_equations, self.compartment_names.index(take_compartment), -net_flow,
            )
            _ode_equations = increment_list_by_index(
                _ode_equations, self.compartment_names.index(give_compartment), net_flow
            )
        return _ode_equations

    def find_target_strata_props(self, _time, _restriction, _stratification):
        """
        calculate the requested distribution of the population over the stratification that needs to be equilibrated
            over

        :parameters:
            _time: float
                current time value in integration
            _stratification: str
                name of the stratification over which the distribution of population is to be calculated
            _restriction: str
                name of the restriction stratification and the stratum joined with "_", if this is being applied
                if this is submitted as "all", the equilibration will be applied across all other strata
        """

        # for each applicable stratification, find target value for all strata, except the last one
        target_prop_values = {}
        for stratum in self.target_props[_stratification][_restriction]:
            target_prop_values[stratum] = (
                self.target_props[_stratification][_restriction][stratum]
                if type(self.target_props[_stratification][_restriction][stratum]) == float
                else self.time_variants[self.target_props[_stratification][_restriction][stratum]](
                    _time
                )
            )

        # check that prevalence values (including time-variant values) fall between zero and one
        if sum(target_prop_values.values()) > 1.0:
            raise ValueError(
                "total prevalence of first n-1 strata sums to more than one at time %s" % _time
            )
        elif any(target_prop_values.values()) < 0.0:
            raise ValueError("prevalence request of less than zero at time %s" % _time)

        # convert to dictionary of cumulative totals
        cumulative_target_props = create_cumulative_dict(target_prop_values)

        # add in a cumulative value of one for the last stratum
        cumulative_target_props.update({self.all_stratifications[_stratification][-1]: 1.0})
        return cumulative_target_props

    def find_current_strata_props(self, _compartment_values, _stratification, _restriction):
        """
        find the current distribution of the population across a particular stratification, which may or may not be
            restricted to a stratum of a previously implemented stratification process

        :parameters:
            _compartment_values: list
                current compartment values achieved during integration
            _stratification: str
                name of the stratification over which the distribution of population is to be calculated
            _restriction: str
                name of the restriction stratification and the stratum joined with "_", if this is being applied
                if this is submitted as "all", the equilibration will be applied across all other strata
        """

        # find the compartment indices applicable to the cross-stratification of interest (which may be all of them)
        if _restriction == "all":
            restriction_compartments = list(range(len(self.compartment_names)))
        else:
            restrict_stratification, restrict_stratum = _restriction.split("_")
            restriction_compartments = self.strata_indices[restrict_stratification][
                restrict_stratum
            ]

        # find current values of prevalence for the stratification for which prevalence values targeted
        current_strata_props = {}
        for stratum in self.all_stratifications[_stratification]:
            current_strata_props[stratum] = sum(
                [
                    _compartment_values[i_comp]
                    for i_comp in restriction_compartments
                    if i_comp in self.strata_indices[_stratification][stratum]
                ]
            ) / sum([_compartment_values[i_comp] for i_comp in restriction_compartments])

        return create_cumulative_dict(current_strata_props)


from numba import jit


def find_infectious_populations(
    compartment_values: np.ndarray,
    strains: List[str],
    mixing_categories: List[str],
    strain_mixing_elements: Dict[str, Dict[str, List[int]]],
    strain_mixing_multipliers: Dict[str, Dict[str, np.ndarray]],
):
    infectious_populations = {}
    num_mixing_categories = len(mixing_categories)
    for strain in strains:
        infectious_populations[strain] = []
        for idx in range(num_mixing_categories):
            category = mixing_categories[idx]
            weighted_sum = _find_infectious_populations_weighted_sum(
                compartment_values,
                strain_mixing_elements[strain][category],
                strain_mixing_multipliers[strain][category],
            )
            infectious_populations[strain].append(weighted_sum)

    return infectious_populations


@jit(nopython=True)
def _find_infectious_populations_weighted_sum(
    compartment_values: np.ndarray, mixing_element_idxs: np.ndarray, mixing_multipliers: np.ndarray,
):
    mixing_elements = compartment_values[mixing_element_idxs]
    return (mixing_elements * mixing_multipliers).sum()
