# -*- coding: utf-8 -*-


"""

Base Population Model to handle different type of models.

Implicit time unit: years

"""

import random

from scipy import exp, log

from autumn.base import BaseModel
from autumn.settings import default, philippines
from curve import make_sigmoidal_curve, make_two_step_curve


def label_intersects_tags(label, tags):
    for tag in tags:
        if tag in label:
            return True
    return False


class UnstratifiedModel(BaseModel):

    """
    A harmonised model that can run any number of strains
    and organ statuses
    """

    def __init__(self,
                 input_parameters=None,
                 input_compartments=None):

        BaseModel.__init__(self)

        self.define_model_structure()

        self.initialise_compartments(input_compartments)

        self.set_parameters(input_parameters)

    def define_model_structure(self):

        self.compartment_types = [
            "susceptible_fully",
            "susceptible_vac",
            "susceptible_treated",
            "latent_early",
            "latent_late",
            "active",
            "detect",
            "missed",
            "treatment_infect",
            "treatment_noninfect"]

        self.broad_compartment_types = [
            "susceptible",
            "latent",
            "active",
            "missed",
            "treatment"]

        self.treatment_stages = [
            "_infect",
            "_noninfect"]

        self.infectious_tags = [
            "active",
            "missed",
            "detect",
            "treatment_infect"]

    def initialise_compartments(self, input_compartments):

        if input_compartments is None:
            input_compartments = {
                "susceptible_fully":
                    2e7,
                "active":
                    3.}

        # Initialise all compartments to zero
        for compartment in self.compartment_types:
            if "susceptible" in compartment:
                self.set_compartment(compartment, 0.)
            elif "latent" in compartment:
                self.set_compartment(compartment, 0.)
            else:
                self.set_compartment(compartment, 0.)

        # Put in values from input_compartments - now initialise to DS-TB only
        for compartment in self.compartment_types:
            if compartment in input_compartments:
                if "susceptible" in compartment:
                    self.set_compartment(compartment,
                                         input_compartments[compartment])
                elif "latent" in compartment:
                    self.set_compartment(compartment,
                                         input_compartments[compartment])
                else:
                    self.set_compartment(compartment,
                                         input_compartments[compartment])

    def set_parameters(self, input_parameters):

        # Extract default parameters from our database
        # of parameters in settings
        if input_parameters is None:

            # Estimate some parameters
            input_parameters = {
                "demo_rate_birth":
                    24. / 1e3,
                "demo_rate_death":
                    1. / 69.,
                "epi_proportion_cases_smearpos":
                    (92991. + 6277.) / 243379.,  # Total bacteriologically confirmed
                "epi_proportion_cases_smearneg":
                    139950. / 243379.,  # Clinically diagnosed
                "epi_proportion_cases_extrapul":
                    4161. / 243379.,  # Bacteriologically confirmed
                "tb_multiplier_force_smearpos":
                    1.,
                "tb_multiplier_force_smearneg":
                    0.24,
                "tb_multiplier_force_extrapul":
                    0.,
                "tb_multiplier_force":
                    1.,
                "tb_n_contact":
                    9.,
                "tb_proportion_early_progression":
                    0.12,
                "tb_timeperiod_early_latent":
                    0.4,
                "tb_rate_late_progression":
                    0.007,
                "tb_proportion_casefatality_untreated_smearpos":
                    0.7,
                "tb_proportion_casefatality_untreated_smearneg":
                    0.2,
                "tb_proportion_casefatality_untreated":
                    0.4,
                "tb_timeperiod_activeuntreated":
                    4.,
                "tb_multiplier_bcg_protection":
                    0.5,
                "program_prop_vac":
                    0.88,
                "program_prop_unvac":
                    1. - 0.88,
                "program_proportion_detect":
                    0.7,
                "program_algorithm_sensitivity":
                    0.9,
                "program_rate_start_treatment":
                    26.,
                "tb_timeperiod_treatment_ds":
                    0.5,
                "tb_timeperiod_treatment_mdr":
                    2.,
                "tb_timeperiod_treatment_xdr":
                    3.,
                "tb_timeperiod_treatment_inappropriate":
                    2.,
                "tb_timeperiod_infect_ontreatment_ds":
                    0.035,
                "tb_timeperiod_infect_ontreatment_mdr":
                    1. / 12.,
                "tb_timeperiod_infect_ontreatment_xdr":
                    2. / 12.,
                "tb_timeperiod_infect_ontreatment_inappropriate":
                    1.9,
                "program_proportion_success_ds":
                    0.9,
                "program_proportion_success_mdr":
                    0.6,
                "program_proportion_success_xdr":
                    0.4,
                "program_proportion_success_inappropriate":
                    0.3,
                "program_rate_restart_presenting":
                    4.,
                "proportion_amplification":
                    1. / 15.,
                "timepoint_introduce_mdr":
                    1960.,
                "timepoint_introduce_xdr":
                    2050.,
                "treatment_available_date":
                    1940.,
                "dots_start_date":
                    1990,
                "finish_scaleup_date":
                    2010,
                "pretreatment_available_proportion":
                    0.6,
                "dots_start_proportion":
                    0.85,
                "program_prop_assign_mdr":
                    0.6,
                "program_prop_assign_xdr":
                    .4,
                "program_prop_lowquality":
                    0.1,
                "program_rate_leavelowquality":
                    2.,
                "program_prop_nonsuccessoutcomes_death":
                    0.25
            }

        for parameter in input_parameters:
            self.set_param(parameter, input_parameters[parameter])

    def process_params(self):
        
        self.split_default_death_proportions()

        self.find_natural_history_flows()

        self.find_detection_rates()

        self.find_programmatic_rates()

        self.find_treatment_rates()

    def calculate_birth_rates(self):

        self.vars["rate_birth"] = \
            self.params["demo_rate_birth"] * self.vars["population"]
        self.vars["births_unvac"] = \
            self.params["program_prop_unvac"] * self.vars["rate_birth"]
        self.vars["births_vac"] = \
            self.params["program_prop_vac"] * self.vars["rate_birth"]

    def set_birth_flows(self):

        self.set_var_entry_rate_flow(
            "susceptible_fully", "births_unvac")
        self.set_var_entry_rate_flow(
            "susceptible_vac", "births_vac")

    def calculate_force_infection(self):

        self.vars["infectious_population"] = 0.0
        for label in self.labels:
            if not label_intersects_tags(label, self.infectious_tags):
                continue
            self.vars["infectious_population"] += \
                self.params["tb_multiplier_force"] \
                * self.compartments[label]
        self.vars["rate_force"] = \
            self.params["tb_n_contact"] \
              * self.vars["infectious_population"] \
              / self.vars["population"]
        self.vars["rate_force_weak"] = \
            self.params["tb_multiplier_bcg_protection"] \
              * self.vars["rate_force"]

    def set_infection_flows(self):

        self.set_var_transfer_rate_flow(
            "susceptible_fully",
            "latent_early",
            "rate_force")
        self.set_var_transfer_rate_flow(
            "susceptible_vac",
            "latent_early",
            "rate_force_weak")
        self.set_var_transfer_rate_flow(
            "susceptible_treated",
            "latent_early",
            "rate_force_weak")
        self.set_var_transfer_rate_flow(
            "latent_late",
            "latent_early",
            "rate_force_weak")

    def find_natural_history_flows(self):

        # If extrapulmonary case-fatality not stated
        if "tb_proportion_casefatality_untreated_extrapul" not in self.params:
            self.set_param(
                "tb_proportion_casefatality_untreated_extrapul",
                self.params["tb_proportion_casefatality_untreated_smearneg"])

        # Progression and stabilisation rates
        self.set_param("tb_rate_early_progression",  # Overall
                       self.params["tb_proportion_early_progression"]
                       / self.params["tb_timeperiod_early_latent"])
        self.set_param("tb_rate_stabilise",  # Stabilisation rate
                       (1 - self.params["tb_proportion_early_progression"])
                       / self.params["tb_timeperiod_early_latent"])
        self.set_param(
            "tb_rate_early_progression",
            self.params["tb_proportion_early_progression"]
              / self.params["tb_timeperiod_early_latent"])
        self.set_param(
            "tb_rate_late_progression",
            self.params["tb_rate_late_progression"])
        self.set_param(
            "tb_rate_death",
            self.params["tb_proportion_casefatality_untreated"]
            / self.params["tb_timeperiod_activeuntreated"])
        self.set_param(
            "tb_rate_recover",
            (1 - self.params["tb_proportion_casefatality_untreated"])
            / self.params["tb_timeperiod_activeuntreated"])

    def set_natural_history_flows(self):

        self.set_fixed_transfer_rate_flow(
            "latent_early",
            "latent_late",
            "tb_rate_stabilise")
        self.set_fixed_transfer_rate_flow(
            "latent_early",
            "active",
            "tb_rate_early_progression")
        self.set_fixed_transfer_rate_flow(
            "latent_late",
            "active",
            "tb_rate_late_progression")
        self.set_fixed_transfer_rate_flow(
            "active",
            "latent_late",
            "tb_rate_recover")
        self.set_fixed_transfer_rate_flow(
            "missed",
            "latent_late",
            "tb_rate_recover")
        self.set_infection_death_rate_flow(
            "active",
            "tb_rate_death")
        self.set_infection_death_rate_flow(
            "missed",
            "tb_rate_death")

        self.set_fixed_transfer_rate_flow(
            "detect",
            "latent_late",
            "tb_rate_recover")
        self.set_infection_death_rate_flow(
            "detect",
            "tb_rate_death")

    def find_detection_rates(self):

        # Rates of detection and failure of detection
        self.set_param(
            "program_rate_detect",
            self.params["program_proportion_detect"]
            * (self.params["tb_rate_recover"] + self.params["tb_rate_death"])
            / (1. - self.params["program_proportion_detect"]
               * (1. + (1. - self.params["program_algorithm_sensitivity"])
                       / self.params["program_algorithm_sensitivity"])))

        self.set_param(
            "program_rate_missed",
            self.params["program_rate_detect"]
            * (1. - self.params["program_algorithm_sensitivity"])
            / self.params["program_algorithm_sensitivity"]
        )
        # Derived from original formulas of:
        #   algorithm sensitivity = detection rate / (detection rate + missed rate)
        #   - and -
        #   detection proportion = detection rate / (detection rate + missed rate + spont recover rate + death rate)

    def find_programmatic_rates(self):

        for detect_or_missed in ["_detect", "_missed"]:
            self.set_scaleup_var(
                "program_rate" + detect_or_missed,
                make_two_step_curve(
                    self.params["pretreatment_available_proportion"] * self.params["program_rate" + detect_or_missed],
                    self.params["dots_start_proportion"] * self.params["program_rate" + detect_or_missed],
                    self.params["program_rate" + detect_or_missed],
                    self.params["treatment_available_date"], self.params["dots_start_date"], self.params["finish_scaleup_date"]))

    def set_programmatic_flows(self):

        self.set_var_transfer_rate_flow(
            "active",
            "detect",
            "program_rate_detect")
        self.set_var_transfer_rate_flow(
            "active",
            "missed",
            "program_rate_missed")
        self.set_fixed_transfer_rate_flow(
            "detect",
            "treatment_infect",
            "program_rate_start_treatment")
        self.set_fixed_transfer_rate_flow(
            "missed",
            "active",
            "program_rate_restart_presenting")

    def split_default_death_proportions(self):

        # Temporary code
        # to define default and death proportions
        self.params["program_proportion_default"] =\
            (1. - self.params["program_proportion_success_ds"])\
            * (1. - self.params["program_prop_nonsuccessoutcomes_death"])
        self.params["program_proportion_death"] =\
            (1. - self.params["program_proportion_success_ds"])\
            * self.params["program_prop_nonsuccessoutcomes_death"]

    def find_treatment_rates(self):

        outcomes = ["_success", "_death", "_default"]
        non_success_outcomes = outcomes[1: 3]

        # Find the non-infectious period
        self.set_param(
            "tb_timeperiod_noninfect_ontreatment_ds",
            self.params["tb_timeperiod_treatment_ds"]
              - self.params["tb_timeperiod_infect_ontreatment_ds"])

        # Find the proportion of deaths/defaults during the infectious and non-infectious stages
        for outcome in non_success_outcomes:
            early_proportion, late_proportion = self.find_flow_proportions_by_period(
                self.params["program_proportion" + outcome],
                self.params["tb_timeperiod_infect_ontreatment_ds"],
                self.params["tb_timeperiod_treatment_ds"])
            self.set_param(
                "program_proportion" + outcome + "_infect",
                early_proportion)
            self.set_param(
                "program_proportion" + outcome + "_noninfect",
                late_proportion)

        # Find the success proportions
        for treatment_stage in self.treatment_stages:
            self.set_param(
                "program_proportion_success" + treatment_stage,
                1. - self.params["program_proportion_default" + treatment_stage]
                  - self.params["program_proportion_death" + treatment_stage])
            # Find the corresponding rates from the proportions
            for outcome in outcomes:
                self.set_param(
                    "program_rate" + outcome + treatment_stage,
                    1. / self.params["tb_timeperiod" + treatment_stage + "_ontreatment_ds"]
                    * self.params["program_proportion" + outcome + treatment_stage])

    def set_treatment_flows(self):

        self.set_fixed_transfer_rate_flow(
            "treatment_infect",
            "treatment_noninfect",
            "program_rate_success_infect")
        self.set_fixed_transfer_rate_flow(
            "treatment_noninfect",
            "susceptible_treated",
            "program_rate_success_noninfect")
        self.set_infection_death_rate_flow(
            "treatment_infect",
            "program_rate_death_infect")
        self.set_infection_death_rate_flow(
            "treatment_noninfect",
            "program_rate_death_noninfect")
        self.set_fixed_transfer_rate_flow(
            "treatment_infect",
            "active",
            "program_rate_default_infect")
        self.set_fixed_transfer_rate_flow(
            "treatment_noninfect",
            "active",
            "program_rate_default_noninfect")

    def set_flows(self):

        self.set_birth_flows()

        self.set_infection_flows()

        self.set_natural_history_flows()

        self.set_programmatic_flows()

        self.set_treatment_flows()

        self.set_population_death_rate("demo_rate_death")

    def additional_diagnostics(self):

        self.broad_compartment_soln, broad_compartment_denominator\
            = self.sum_over_compartments(self.broad_compartment_types)
        self.broad_fraction_soln\
            = self.get_fraction_soln(
            self.broad_compartment_types,
            self.broad_compartment_soln,
            broad_compartment_denominator)

        self.compartment_type_soln, compartment_type_denominator\
            = self.sum_over_compartments(self.compartment_types)
        self.compartment_type_fraction_soln\
            = self.get_fraction_soln(
            self.compartment_types,
            self.compartment_type_soln,
            compartment_type_denominator)

        self.subgroup_diagnostics()

    def subgroup_diagnostics(self):

        self.groups = {
            "ever_infected": ["susceptible_treated", "latent", "active", "missed", "detect", "treatment"],
            "infected": ["latent", "active", "missed", "detect", "treatment"],
            "active": ["active", "missed", "detect", "treatment"],
            "infectious": ["active", "missed", "detect", "treatment_infect"],
            "identified": ["detect", "treatment"],
            "treatment": ["treatment_infect", "treatment_noninfect"]}
        for key in self.groups:
            compartment_soln, compartment_denominator\
                = self.sum_over_compartments(self.groups[key])
            setattr(self, key + "_compartment_soln", compartment_soln)
            setattr(self, key + "_compartment_denominator", compartment_denominator)
            setattr(self, key + "_fraction_soln",
                    self.get_fraction_soln(
                        self.groups[key],
                        compartment_soln,
                        compartment_denominator))

    def find_flow_proportions_by_period(
            self, proportion, early_period, total_period):
        early_proportion\
            = 1. - exp( log(1. - proportion) * early_period / total_period)
        late_proportion\
            = proportion - early_proportion
        return early_proportion, late_proportion

    def calculate_variable_rates(self):

        self.vars["population"] = sum(self.compartments.values())

        self.calculate_birth_rates()

        self.calculate_force_infection()

    def get_fraction_soln(self, numerator_labels, numerators, denominator):
        fraction = {}
        for label in numerator_labels:
            fraction[label] = [
                v / t
                for v, t
                in zip(
                    numerators[label],
                    denominator)]
        return fraction

    def sum_over_compartments(self, compartment_types):
        summed_soln = {}
        summed_denominator\
            = [0] * len(random.sample(self.compartment_soln.items(), 1)[0][1])
        for compartment_type in compartment_types:
            summed_soln[compartment_type]\
                = [0] * len(random.sample(self.compartment_soln.items(), 1)[0][1])
            for label in self.labels:
                if compartment_type in label:
                    summed_soln[compartment_type] = [
                        a + b
                        for a, b
                        in zip(
                            summed_soln[compartment_type],
                            self.compartment_soln[label])]
                    summed_denominator += self.compartment_soln[label]
        return summed_soln, summed_denominator

    def sum_over_compartments_bycategory(self, compartment_types, categories):
        summed_soln = {}
        # HELP BOSCO
        # The following line of code works, but I'm sure this isn't the best approach:
        summed_denominator\
            = [0] * len(random.sample(self.compartment_soln.items(), 1)[0][1])
        compartment_types_bycategory = []
        # HELP BOSCO
        # I think there is probably a more elegant way to do the following, but perhaps not.
        # Also, it could possibly be better generalised. That is, rather than insisting that
        # strain applies to all compartments except for the susceptible, it might be possible
        # to say that strain applies to all compartments except for those that have any
        # strain in their label.
        if categories == "strain":
            working_categories = self.strains
        elif categories == "organ":
            working_categories = self.organ_status
        for compartment_type in compartment_types:
            if (categories == "strain" and "susceptible" in compartment_type) \
                    or (categories == "organ" and \
                            ("susceptible" in compartment_type or "latent" in compartment_type)):
                summed_soln[compartment_type]\
                    = [0] * len(random.sample(self.compartment_soln.items(), 1)[0][1])
                for label in self.labels:
                    if compartment_type in label:
                        summed_soln[compartment_type] = [
                            a + b
                            for a, b
                            in zip(
                                summed_soln[compartment_type],
                                self.compartment_soln[label])]
                        summed_denominator += self.compartment_soln[label]
                    if compartment_type in label \
                            and compartment_type not in compartment_types_bycategory:
                        compartment_types_bycategory.append(compartment_type)
            else:
                for working_category in working_categories:
                    compartment_types_bycategory.append(compartment_type + working_category)
                    summed_soln[compartment_type + working_category]\
                        = [0] * len(random.sample(self.compartment_soln.items(), 1)[0][1])
                    for label in self.labels:
                        if compartment_type in label and working_category in label:
                            summed_soln[compartment_type + working_category] = [
                                a + b
                                for a, b
                                in zip(
                                    summed_soln[compartment_type + working_category],
                                    self.compartment_soln[label])]
                            summed_denominator += self.compartment_soln[label]

        return summed_soln, summed_denominator, compartment_types_bycategory

    def calculate_outputs(self):

        rate_incidence = 0.
        rate_mortality = 0.
        rate_notifications = 0.
        for from_label, to_label, rate in self.fixed_transfer_rate_flows:
            if 'latent' in from_label and 'active' in to_label:
                rate_incidence += self.compartments[from_label] * rate
        self.vars["incidence"] = \
            rate_incidence \
            / self.vars["population"] * 1E5
        for from_label, to_label, rate in self.var_transfer_rate_flows:
            if 'active' in from_label and\
                    ('detect' in to_label or 'treatment_infect' in to_label):
                rate_notifications += self.compartments[from_label] * self.vars[rate]
        self.vars["notifications"] = \
            rate_notifications / self.vars["population"] * 1E5
        for from_label, rate in self.infection_death_rate_flows:
            rate_mortality \
                += self.compartments[from_label] * rate
        self.vars["mortality"] = \
            rate_mortality \
            / self.vars["population"] * 1E5

        self.vars["prevalence"] = 0.0
        for label in self.labels:
            if "susceptible" not in label and "latent" not in label:
                self.vars["prevalence"] += (
                    self.compartments[label]
                     / self.vars["population"] * 1E5)


class MultiOrganStatusModel(UnstratifiedModel):

    """
    A harmonised model that can run any number of strains
    and organ statuses
    """

    def __init__(self,
                 number_of_organs=3,
                 input_parameters=None,
                 input_compartments=None):

        BaseModel.__init__(self)

        self.define_model_structure(number_of_organs)

        self.initialise_compartments(input_compartments)

        self.set_parameters(input_parameters)

        self.split_default_death_proportions()

        self.ensure_all_progressions_go_somewhere()

        self.find_natural_history_flows()

        self.find_detection_rates()

        self.find_programmatic_rates()

        self.find_treatment_rates()

    def define_model_structure(self, number_of_organs):

        self.compartment_types = [
            "susceptible_fully",
            "susceptible_vac",
            "susceptible_treated",
            "latent_early",
            "latent_late",
            "active",
            "detect",
            "missed",
            "treatment_infect",
            "treatment_noninfect"]

        self.broad_compartment_types = [
            "susceptible",
            "latent",
            "active",
            "missed",
            "treatment"]

        available_organs = [
            "_smearpos",
            "_smearneg",
            "_extrapul"]
        self.organ_status =\
            available_organs[0: number_of_organs]

        self.treatment_stages = [
            "_infect",
            "_noninfect"]

        self.infectious_tags = [
            "active",
            "missed",
            "detect",
            "treatment_infect"]

    def initialise_compartments(self, input_compartments):

        if input_compartments is None:
            input_compartments = {
                "susceptible_fully":
                    2e7,
                "active":
                    3.}

        # Initialise all compartments to zero
        for compartment in self.compartment_types:
            if "susceptible" in compartment:
                self.set_compartment(compartment, 0.)
            elif "latent" in compartment:
                self.set_compartment(compartment, 0.)
            else:
                for organ in self.organ_status:
                    self.set_compartment(compartment + organ, 0.)

        # Put in values from input_compartments - now initialise to DS-TB only
        for compartment in self.compartment_types:
            if compartment in input_compartments:
                if "susceptible" in compartment:
                    self.set_compartment(compartment,
                                         input_compartments[compartment])
                elif "latent" in compartment:
                    self.set_compartment(compartment,
                                         input_compartments[compartment])
                else:
                    for organ in self.organ_status:
                        self.set_compartment(compartment + organ,
                                             input_compartments[compartment]
                                             / len(self.organ_status))

    def ensure_all_progressions_go_somewhere(self):

        # Make sure all progressions go somewhere, regardless of number of organ statuses
        if len(self.organ_status) == 1:
            self.params["epi_proportion_cases_smearpos"] = 1.
        elif len(self.organ_status) == 2:
            self.params["epi_proportion_cases_smearneg"] = \
                self.params["epi_proportion_cases_smearneg"] \
                + self.params["epi_proportion_cases_extrapul"]

    def find_natural_history_flows(self):

        # If extrapulmonary case-fatality not stated
        if "tb_proportion_casefatality_untreated_extrapul" not in self.params:
            self.set_param(
                "tb_proportion_casefatality_untreated_extrapul",
                self.params["tb_proportion_casefatality_untreated_smearneg"])

        # Progression and stabilisation rates
        self.set_param("tb_rate_early_progression",  # Overall
                       self.params["tb_proportion_early_progression"]
                       / self.params["tb_timeperiod_early_latent"])
        self.set_param("tb_rate_stabilise",  # Stabilisation rate
                       (1 - self.params["tb_proportion_early_progression"])
                       / self.params["tb_timeperiod_early_latent"])
        for organ in self.organ_status:
            self.set_param(
                "tb_rate_early_progression" + organ,
                self.params["tb_proportion_early_progression"]
                  / self.params["tb_timeperiod_early_latent"]
                  * self.params["epi_proportion_cases" + organ])
            self.set_param(
                "tb_rate_late_progression" + organ,
                self.params["tb_rate_late_progression"]
                * self.params["epi_proportion_cases" + organ])
            self.set_param(
                "tb_rate_death" + organ,
                self.params["tb_proportion_casefatality_untreated" + organ]
                / self.params["tb_timeperiod_activeuntreated"])
            self.set_param(
                "tb_rate_recover" + organ,
                (1 - self.params["tb_proportion_casefatality_untreated" + organ])
                / self.params["tb_timeperiod_activeuntreated"])

    def set_natural_history_flows(self):

        self.set_fixed_transfer_rate_flow(
            "latent_early",
            "latent_late",
            "tb_rate_stabilise")
        for organ in self.organ_status:
            self.set_fixed_transfer_rate_flow(
                "latent_early",
                "active" + organ,
                "tb_rate_early_progression" + organ)
            self.set_fixed_transfer_rate_flow(
                "latent_late",
                "active" + organ,
                "tb_rate_late_progression" + organ)
            self.set_fixed_transfer_rate_flow(
                "active" + organ,
                "latent_late",
                "tb_rate_recover" + organ)
            self.set_fixed_transfer_rate_flow(
                "missed" + organ,
                "latent_late",
                "tb_rate_recover" + organ)
            self.set_infection_death_rate_flow(
                "active" + organ,
                "tb_rate_death" + organ)
            self.set_infection_death_rate_flow(
                "missed" + organ,
                "tb_rate_death" + organ)

            self.set_fixed_transfer_rate_flow(
                "detect" + organ,
                "latent_late",
                "tb_rate_recover" + organ)
            self.set_infection_death_rate_flow(
                "detect" + organ,
                "tb_rate_death" + organ)

    def find_detection_rates(self):

        # Rates of detection and failure of detection
        self.set_param(
            "program_rate_detect",
            self.params["program_proportion_detect"]
            * (self.params["tb_rate_recover_smearpos"] + self.params["tb_rate_death_smearpos"])
            / (1. - self.params["program_proportion_detect"]
               * (1. + (1. - self.params["program_algorithm_sensitivity"])
                       / self.params["program_algorithm_sensitivity"])))

        self.set_param(
            "program_rate_missed",
            self.params["program_rate_detect"]
            * (1. - self.params["program_algorithm_sensitivity"])
            / self.params["program_algorithm_sensitivity"]
        )
        # Derived from original formulas of:
        #   algorithm sensitivity = detection rate / (detection rate + missed rate)
        #   - and -
        #   detection proportion = detection rate / (detection rate + missed rate + spont recover rate + death rate)

    def set_programmatic_flows(self):

        for organ in self.organ_status:
            self.set_var_transfer_rate_flow(
                "active" + organ,
                "detect" + organ,
                "program_rate_detect")
            self.set_var_transfer_rate_flow(
                "active" + organ,
                "missed" + organ,
                "program_rate_missed")
            self.set_fixed_transfer_rate_flow(
                "detect" + organ,
                "treatment_infect" + organ,
                "program_rate_start_treatment")
            self.set_fixed_transfer_rate_flow(
                "missed" + organ,
                "active" + organ,
                "program_rate_restart_presenting")

    def set_treatment_flows(self):

        for organ in self.organ_status:
            self.set_fixed_transfer_rate_flow(
                "treatment_infect" + organ,
                "treatment_noninfect" + organ,
                "program_rate_success_infect")
            self.set_fixed_transfer_rate_flow(
                "treatment_noninfect" + organ,
                "susceptible_treated",
                "program_rate_success_noninfect")
            self.set_infection_death_rate_flow(
                "treatment_infect" + organ,
                "program_rate_death_infect")
            self.set_infection_death_rate_flow(
                "treatment_noninfect" + organ,
                "program_rate_death_noninfect")
            self.set_fixed_transfer_rate_flow(
                "treatment_infect" + organ,
                "active" + organ,
                "program_rate_default_infect")
            self.set_fixed_transfer_rate_flow(
                "treatment_noninfect" + organ,
                "active" + organ,
                "program_rate_default_noninfect")

    def additional_diagnostics(self):

        self.broad_compartment_soln, broad_compartment_denominator\
            = self.sum_over_compartments(self.broad_compartment_types)
        self.broad_fraction_soln\
            = self.get_fraction_soln(
            self.broad_compartment_types,
            self.broad_compartment_soln,
            broad_compartment_denominator)

        self.compartment_type_soln, compartment_type_denominator\
            = self.sum_over_compartments(self.compartment_types)
        self.compartment_type_fraction_soln\
            = self.get_fraction_soln(
            self.compartment_types,
            self.compartment_type_soln,
            compartment_type_denominator)

        self.broad_compartment_type_byorgan_soln, broad_compartment_type_byorgan_denominator,\
        self.broad_compartment_types_byorgan\
            = self.sum_over_compartments_bycategory(self.broad_compartment_types, "organ")
        self.broad_compartment_type_byorgan_fraction_soln\
            = self.get_fraction_soln(
            self.broad_compartment_types_byorgan,
            self.broad_compartment_type_byorgan_soln,
            broad_compartment_type_byorgan_denominator)

        self.subgroup_diagnostics()

    def find_flow_proportions_by_period(
            self, proportion, early_period, total_period):
        early_proportion\
            = 1. - exp( log(1. - proportion) * early_period / total_period)
        late_proportion\
            = proportion - early_proportion
        return early_proportion, late_proportion


class MultiOrganStatusLowQualityModel(MultiOrganStatusModel):

    """
    A harmonised model that can run any number of strains
    and organ statuses
    """

    def __init__(self,
                 number_of_organs=3,
                 input_parameters=None,
                 input_compartments=None):

        BaseModel.__init__(self)

        self.define_model_structure(number_of_organs)

        self.initialise_compartments(input_compartments)

        self.set_parameters(input_parameters)

        self.split_default_death_proportions()

        self.ensure_all_progressions_go_somewhere()

        self.find_natural_history_flows()

        self.find_detection_rates()

        self.find_lowquality_detections()

        self.find_programmatic_rates()

        self.find_treatment_rates()

    def define_model_structure(self, number_of_organs):

        self.compartment_types = [
            "susceptible_fully",
            "susceptible_vac",
            "susceptible_treated",
            "latent_early",
            "latent_late",
            "active",
            "detect",
            "missed",
            "lowquality",
            "treatment_infect",
            "treatment_noninfect"]

        self.broad_compartment_types = [
            "susceptible",
            "latent",
            "active",
            "missed",
            "treatment"]

        available_organs = [
            "_smearpos",
            "_smearneg",
            "_extrapul"]
        self.organ_status =\
            available_organs[0: number_of_organs]

        self.treatment_stages = [
            "_infect",
            "_noninfect"]

        self.infectious_tags = [
            "active",
            "missed",
            "detect",
            "lowquality",
            "treatment_infect"]

    def set_natural_history_flows(self):

        self.set_fixed_transfer_rate_flow(
            "latent_early",
            "latent_late",
            "tb_rate_stabilise")
        for organ in self.organ_status:
            self.set_fixed_transfer_rate_flow(
                "latent_early",
                "active" + organ,
                "tb_rate_early_progression" + organ)
            self.set_fixed_transfer_rate_flow(
                "latent_late",
                "active" + organ,
                "tb_rate_late_progression" + organ)
            self.set_fixed_transfer_rate_flow(
                "active" + organ,
                "latent_late",
                "tb_rate_recover" + organ)
            self.set_fixed_transfer_rate_flow(
                "missed" + organ,
                "latent_late",
                "tb_rate_recover" + organ)
            self.set_infection_death_rate_flow(
                "active" + organ,
                "tb_rate_death" + organ)
            self.set_infection_death_rate_flow(
                "missed" + organ,
                "tb_rate_death" + organ)

            self.set_fixed_transfer_rate_flow(
                "lowquality" + organ,
                "latent_late",
                "tb_rate_recover" + organ)
            self.set_infection_death_rate_flow(
                "lowquality" + organ,
                "tb_rate_death" + organ)

            self.set_fixed_transfer_rate_flow(
                "detect" + organ,
                "latent_late",
                "tb_rate_recover" + organ)
            self.set_infection_death_rate_flow(
                "detect" + organ,
                "tb_rate_death" + organ)

    def find_lowquality_detections(self):
        self.set_param(
            "program_rate_enterlowquality",
            self.params["program_rate_detect"] \
            * self.params["program_prop_lowquality"] \
            / (1. - self.params["program_prop_lowquality"]))

    def find_programmatic_rates(self):

        for detect_or_missed in ["_detect", "_missed", "_enterlowquality"]:
            self.set_scaleup_var(
                "program_rate" + detect_or_missed,
                make_two_step_curve(
                    self.params["pretreatment_available_proportion"] * self.params["program_rate" + detect_or_missed],
                    self.params["dots_start_proportion"] * self.params["program_rate" + detect_or_missed],
                    self.params["program_rate" + detect_or_missed],
                    self.params["treatment_available_date"], self.params["dots_start_date"],
                    self.params["finish_scaleup_date"]))

    def set_programmatic_flows(self):

        for organ in self.organ_status:
            self.set_var_transfer_rate_flow(
                "active" + organ,
                "detect" + organ,
                "program_rate_detect")
            self.set_var_transfer_rate_flow(
                "active" + organ,
                "missed" + organ,
                "program_rate_missed")
            self.set_fixed_transfer_rate_flow(
                "detect" + organ,
                "treatment_infect" + organ,
                "program_rate_start_treatment")
            self.set_fixed_transfer_rate_flow(
                "missed" + organ,
                "active" + organ,
                "program_rate_restart_presenting")
            self.set_var_transfer_rate_flow(
                "active" + organ,
                "lowquality" + organ,
                "program_rate_enterlowquality")
            self.set_fixed_transfer_rate_flow(
                "lowquality" + organ,
                "active" + organ,
                "program_rate_leavelowquality")


class MultistrainModel(MultiOrganStatusModel):

    """
    A harmonised model that can run any number of strains
    and organ statuses
    """

    def __init__(self,
                 number_of_organs=3,
                 number_of_strains=1,
                 input_parameters=None,
                 input_compartments=None):

        BaseModel.__init__(self)

        self.define_model_structure(number_of_organs, number_of_strains)

        self.initialise_compartments(input_compartments)

        self.set_parameters(input_parameters)

        self.split_default_death_proportions()

        self.ensure_all_progressions_go_somewhere()

        self.find_natural_history_flows()

        self.find_detection_rates()

        self.find_programmatic_rates()

        self.find_equal_detection_rates()

        self.find_treatment_rates()

    def define_model_structure(self, number_of_organs, number_of_strains):

        self.compartment_types = [
            "susceptible_fully",
            "susceptible_vac",
            "susceptible_treated",
            "latent_early",
            "latent_late",
            "active",
            "detect",
            "missed",
            "treatment_infect",
            "treatment_noninfect"]

        self.broad_compartment_types = [
            "susceptible",
            "latent",
            "active",
            "missed",
            "treatment"]

        available_organs = [
            "_smearpos",
            "_smearneg",
            "_extrapul"]
        self.organ_status =\
            available_organs[0: number_of_organs]

        available_strains = [
            "_ds",
            "_mdr",
            "_xdr"]
        self.strains\
            = available_strains[0: number_of_strains]

        self.treatment_stages = [
            "_infect",
            "_noninfect"]

        self.infectious_tags = [
            "active",
            "missed",
            "detect",
            "treatment_infect"]

    def initialise_compartments(self, input_compartments):

        if input_compartments is None:
            input_compartments = {
                "susceptible_fully":
                    2e7,
                "active":
                    3.}

        # Initialise all compartments to zero
        for compartment in self.compartment_types:
            if "susceptible" in compartment:  # Replicate for comorbidities only
                self.set_compartment(compartment, 0.)
            elif "latent" in compartment:  # Replicate for comorbidities and strains
                for strain in self.strains:
                    self.set_compartment(compartment + strain, 0.)
            else:
                for strain in self.strains:
                    for organ in self.organ_status:
                        self.set_compartment(compartment + organ + strain, 0.)

        # Put in values from input_compartments - now initialise to DS-TB only
        for compartment in self.compartment_types:
            if compartment in input_compartments:
                if "susceptible" in compartment:
                    self.set_compartment(compartment,
                                         input_compartments[compartment])
                elif "latent" in compartment:
                    self.set_compartment(compartment + "_ds",
                                         input_compartments[compartment])
                else:
                    for organ in self.organ_status:
                        self.set_compartment(compartment + organ + "_ds",
                                             input_compartments[compartment]
                                             / len(self.strains)
                                             / len(self.organ_status))

    def calculate_force_infection(self):

        for strain in self.strains:
            self.vars["infectious_population" + strain] = 0.0
            for organ in self.organ_status:
                for label in self.labels:
                    if strain not in label:
                        continue
                    if organ not in label:
                        continue
                    if not label_intersects_tags(label, self.infectious_tags):
                        continue
                    self.vars["infectious_population" + strain] += \
                        self.params["tb_multiplier_force" + organ] \
                        * self.compartments[label]
            self.vars["rate_force" + strain] = \
                self.params["tb_n_contact"] \
                  * self.vars["infectious_population" + strain] \
                  / self.vars["population"]
            self.vars["rate_force_weak" + strain] = \
                self.params["tb_multiplier_bcg_protection"] \
                  * self.vars["rate_force" + strain]

    def set_infection_flows(self):

        for strain in self.strains:
            self.set_var_transfer_rate_flow(
                "susceptible_fully",
                "latent_early" + strain,
                "rate_force" + strain)
            self.set_var_transfer_rate_flow(
                "susceptible_vac",
                "latent_early" + strain,
                "rate_force_weak" + strain)
            self.set_var_transfer_rate_flow(
                "susceptible_treated",
                "latent_early" + strain,
                "rate_force_weak" + strain)
            self.set_var_transfer_rate_flow(
                "latent_late" + strain,
                "latent_early" + strain,
                "rate_force_weak" + strain)

    def set_natural_history_flows(self):

        for strain in self.strains:
            self.set_fixed_transfer_rate_flow(
                "latent_early" + strain,
                "latent_late" + strain,
                "tb_rate_stabilise")
            for organ in self.organ_status:
                self.set_fixed_transfer_rate_flow(
                    "latent_early" + strain,
                    "active" + organ + strain,
                    "tb_rate_early_progression" + organ)
                self.set_fixed_transfer_rate_flow(
                    "latent_late" + strain,
                    "active" + organ + strain,
                    "tb_rate_late_progression" + organ)
                self.set_fixed_transfer_rate_flow(
                    "active" + organ + strain,
                    "latent_late" + strain,
                    "tb_rate_recover" + organ)
                self.set_fixed_transfer_rate_flow(
                    "missed" + organ + strain,
                    "latent_late" + strain,
                    "tb_rate_recover" + organ)
                self.set_infection_death_rate_flow(
                    "active" + organ + strain,
                    "tb_rate_death" + organ)
                self.set_infection_death_rate_flow(
                    "missed" + organ + strain,
                    "tb_rate_death" + organ)

                self.set_fixed_transfer_rate_flow(
                    "detect" + organ + strain,
                    "latent_late" + strain,
                    "tb_rate_recover" + organ)
                self.set_infection_death_rate_flow(
                    "detect" + organ + strain,
                    "tb_rate_death" + organ)

    def find_equal_detection_rates(self):

        # Set detection rates equal for all strains (probably temporary)
        for strain in self.strains:
            self.set_param(
                "program_rate_detect" + strain,
                self.params["program_rate_detect"])
            self.set_param(
                "program_rate_missed" + strain,
                self.params["program_rate_missed"])
            self.set_param(
                "program_rate_start_treatment" + strain,
                self.params["program_rate_start_treatment"])
            self.set_param(
                "program_rate_restart_presenting" + strain,
                self.params["program_rate_restart_presenting"])

    def set_programmatic_flows(self):

        for strain in self.strains:
            for organ in self.organ_status:

                self.set_var_transfer_rate_flow(
                    "active" + organ + strain,
                    "detect" + organ + strain,
                    "program_rate_detect")
                self.set_var_transfer_rate_flow(
                    "active" + organ + strain,
                    "missed" + organ + strain,
                    "program_rate_missed")
                self.set_fixed_transfer_rate_flow(
                    "detect" + organ + strain,
                    "treatment_infect" + organ + strain,
                    "program_rate_start_treatment")
                self.set_fixed_transfer_rate_flow(
                    "missed" + organ + strain,
                    "active" + organ + strain,
                    "program_rate_restart_presenting")

    def split_default_death_proportions(self):

        # Temporary code
        # to define default and death proportions
        for strain in self.strains:
            self.params["program_proportion_default" + strain] =\
                (1. - self.params["program_proportion_success" + strain])\
                * (1. - self.params["program_prop_nonsuccessoutcomes_death"])
            self.params["program_proportion_death" + strain] =\
                (1. - self.params["program_proportion_success" + strain])\
                * self.params["program_prop_nonsuccessoutcomes_death"]
        self.params["program_proportion_default_inappropriate"] =\
            (1. - self.params["program_proportion_success_inappropriate"])\
            * (1. - self.params["program_prop_nonsuccessoutcomes_death"])
        self.params["program_proportion_death_inappropriate"] = \
            (1. - self.params["program_proportion_success_inappropriate"])\
            * self.params["program_prop_nonsuccessoutcomes_death"]

    def find_treatment_rates(self):
        outcomes = ["_success", "_death", "_default"]
        non_success_outcomes = outcomes[1: 3]

        for strain in self.strains + ["_inappropriate"]:
            # Find the non-infectious period
            self.set_param(
                "tb_timeperiod_noninfect_ontreatment" + strain,
                self.params["tb_timeperiod_treatment" + strain]
                  - self.params["tb_timeperiod_infect_ontreatment" + strain])

            # Find the proportion of deaths/defaults during the infectious and non-infectious stages
            for outcome in non_success_outcomes:
                early_proportion, late_proportion = self.find_flow_proportions_by_period(
                    self.params["program_proportion" + outcome + strain],
                    self.params["tb_timeperiod_infect_ontreatment" + strain],
                    self.params["tb_timeperiod_treatment" + strain])
                self.set_param(
                    "program_proportion" + outcome + "_infect" + strain,
                    early_proportion)
                self.set_param(
                    "program_proportion" + outcome + "_noninfect" + strain,
                    late_proportion)

            # Find the success proportions
            for treatment_stage in self.treatment_stages:
                self.set_param(
                    "program_proportion_success" + treatment_stage + strain,
                    1. - self.params["program_proportion_default" + treatment_stage + strain]
                      - self.params["program_proportion_death" + treatment_stage + strain])
                # Find the corresponding rates from the proportions
                for outcome in outcomes:
                    self.set_param(
                        "program_rate" + outcome + treatment_stage + strain,
                        1. / self.params["tb_timeperiod" + treatment_stage + "_ontreatment" + strain]
                          * self.params["program_proportion" + outcome + treatment_stage + strain])

    def set_treatment_flows(self):

        for strain in self.strains:
            for organ in self.organ_status:
                self.set_fixed_transfer_rate_flow(
                    "treatment_infect" + organ + strain,
                    "treatment_noninfect" + organ + strain,
                    "program_rate_success_infect" + strain)
                self.set_fixed_transfer_rate_flow(
                    "treatment_noninfect" + organ + strain,
                    "susceptible_treated",
                    "program_rate_success_noninfect" + strain)
                self.set_infection_death_rate_flow(
                    "treatment_infect" + organ + strain,
                    "program_rate_death_infect" + strain)
                self.set_infection_death_rate_flow(
                    "treatment_noninfect" + organ + strain,
                    "program_rate_death_noninfect" + strain)
                self.set_fixed_transfer_rate_flow(
                    "treatment_infect" + organ + strain,
                    "active" + organ + strain,
                    "program_rate_default_infect" + strain)
                self.set_fixed_transfer_rate_flow(
                    "treatment_noninfect" + organ + strain,
                    "active" + organ + strain,
                    "program_rate_default_noninfect" + strain)

    def additional_diagnostics(self):

        self.broad_compartment_soln, broad_compartment_denominator\
            = self.sum_over_compartments(self.broad_compartment_types)
        self.broad_fraction_soln\
            = self.get_fraction_soln(
            self.broad_compartment_types,
            self.broad_compartment_soln,
            broad_compartment_denominator)

        self.compartment_type_soln, compartment_type_denominator\
            = self.sum_over_compartments(self.compartment_types)
        self.compartment_type_fraction_soln\
            = self.get_fraction_soln(
            self.compartment_types,
            self.compartment_type_soln,
            compartment_type_denominator)

        self.broad_compartment_type_bystrain_soln, broad_compartment_type_bystrain_denominator,\
        self.broad_compartment_types_bystrain\
            = self.sum_over_compartments_bycategory(self.broad_compartment_types, "strain")
        self.broad_compartment_type_bystrain_fraction_soln\
            = self.get_fraction_soln(
            self.broad_compartment_types_bystrain,
            self.broad_compartment_type_bystrain_soln,
            broad_compartment_type_bystrain_denominator)

        self.broad_compartment_type_byorgan_soln, broad_compartment_type_byorgan_denominator,\
        self.broad_compartment_types_byorgan\
            = self.sum_over_compartments_bycategory(self.broad_compartment_types, "organ")
        self.broad_compartment_type_byorgan_fraction_soln\
            = self.get_fraction_soln(
            self.broad_compartment_types_byorgan,
            self.broad_compartment_type_byorgan_soln,
            broad_compartment_type_byorgan_denominator)

        self.compartment_type_bystrain_soln, compartment_type_bystrain_denominator,\
        self.compartment_types_bystrain\
            = self.sum_over_compartments_bycategory(self.compartment_types, "strain")
        self.compartment_type_bystrain_fraction_soln\
            = self.get_fraction_soln(
            self.compartment_types_bystrain,
            self.compartment_type_bystrain_soln,
            compartment_type_bystrain_denominator)

        self.subgroup_diagnostics()

    def calculate_outputs_bystrain(self):

        # Now by strain:
        rate_incidence = {}
        rate_mortality = {}
        rate_notifications = {}

        for strain in self.strains:
            rate_incidence[strain] = 0.
            rate_mortality[strain] = 0.
            rate_notifications[strain] = 0.
            for from_label, to_label, rate in self.fixed_transfer_rate_flows:
                if 'latent' in from_label and 'active' in to_label and strain in to_label:
                    rate_incidence[strain] \
                        += self.compartments[from_label] * rate
            for from_label, to_label, rate in self.var_transfer_rate_flows:
                if 'active' in from_label and 'detect' in to_label and strain in from_label:
                    rate_notifications[strain] \
                        += self.compartments[from_label] * self.vars[rate]
            for from_label, rate in self.infection_death_rate_flows:
                if strain in from_label:
                    rate_mortality[strain] \
                        += self.compartments[from_label] * rate
            self.vars["incidence" + strain] \
                = rate_incidence[strain] \
                / self.vars["population"] * 1E5
            self.vars["mortality" + strain] \
                = rate_mortality[strain] \
                / self.vars["population"] * 1E5
            self.vars["notifications" + strain] \
                = rate_notifications[strain] \
                / self.vars["population"] * 1E5

        for strain in self.strains:
            self.vars["prevalence" + strain] = 0.
            for label in self.labels:
                if "susceptible" not in label and "latent" not in label and strain in label:
                    self.vars["prevalence" + strain] += (
                        self.compartments[label]
                         / self.vars["population"] * 1E5)


class StratifiedModel(MultistrainModel):

    """
    A harmonised model that can run any number of strains
    and organ statuses
    """

    def __init__(self,
                 number_of_organs=3,
                 number_of_strains=1,
                 number_of_comorbidities=1,
                 input_parameters=None,
                 input_compartments=None):

        BaseModel.__init__(self)

        self.define_model_structure(number_of_organs, number_of_strains, number_of_comorbidities)

        self.initialise_compartments(input_compartments)

        self.set_parameters(input_parameters)

        self.split_default_death_proportions()

        self.ensure_all_progressions_go_somewhere()

        self.find_natural_history_flows()

        self.find_detection_rates()

        self.find_programmatic_rates()

        self.find_equal_detection_rates()

        self.find_treatment_rates()

    def define_model_structure(self, number_of_organs, number_of_strains, number_of_comorbidities):

        self.compartment_types = [
            "susceptible_fully",
            "susceptible_vac",
            "susceptible_treated",
            "latent_early",
            "latent_late",
            "active",
            "detect",
            "missed",
            "treatment_infect",
            "treatment_noninfect"]

        self.broad_compartment_types = [
            "susceptible",
            "latent",
            "active",
            "missed",
            "treatment"]

        available_organs = [
            "_smearpos",
            "_smearneg",
            "_extrapul"]
        self.organ_status =\
            available_organs[0: number_of_organs]

        available_strains = [
            "_ds",
            "_mdr",
            "_xdr"]
        self.strains\
            = available_strains[0: number_of_strains]

        available_comorbidities = [
            "_nocomorbs",
            "_hiv",
            "_diabetes"]
        self.comorbidities\
            = available_comorbidities[0: number_of_comorbidities]

        self.treatment_stages = [
            "_infect",
            "_noninfect"]

        self.infectious_tags = [
            "active",
            "missed",
            "detect",
            "treatment_infect"]

    def initialise_compartments(self, input_compartments):

        if input_compartments is None:
            input_compartments = {
                "susceptible_fully":
                    2e7,
                "active":
                    3.}

        # Initialise all compartments to zero
        for compartment in self.compartment_types:
            for comorbidity in self.comorbidities:
                if "susceptible" in compartment:  # Replicate for comorbidities only
                    self.set_compartment(compartment + comorbidity, 0.)
                elif "latent" in compartment:  # Replicate for comorbidities and strains
                    for strain in self.strains:
                        self.set_compartment(compartment + strain + comorbidity, 0.)
                else:
                    for strain in self.strains:
                        for organ in self.organ_status:
                            self.set_compartment(compartment + organ + strain + comorbidity, 0.)

        # Put in values from input_compartments - now initialise to DS-TB only
        for compartment in self.compartment_types:
            if compartment in input_compartments:
                if "susceptible" in compartment:
                    for comorbidity in self.comorbidities:
                        self.set_compartment(compartment + comorbidity,
                                             input_compartments[compartment]
                                             / len(self.comorbidities))
                elif "latent" in compartment:
                    for comorbidity in self.comorbidities:
                        self.set_compartment(compartment + "_ds" + comorbidity,
                                             input_compartments[compartment]
                                             / len(self.comorbidities))
                else:
                    for comorbidity in self.comorbidities:
                        for organ in self.organ_status:
                            self.set_compartment(compartment + organ + "_ds" + comorbidity,
                                                 input_compartments[compartment]
                                                 / len(self.comorbidities)
                                                 / len(self.strains)
                                                 / len(self.organ_status))

    def calculate_birth_rates(self):

        self.vars["rate_birth"] = \
            self.params["demo_rate_birth"] * self.vars["population"]
        self.vars["births_unvac"] = \
            self.params["program_prop_unvac"] * self.vars["rate_birth"]\
            / len(self.comorbidities)
        self.vars["births_vac"] = \
            self.params["program_prop_vac"] * self.vars["rate_birth"]\
            / len(self.comorbidities)

    def set_birth_flows(self):

        for comorbidity in self.comorbidities:
            self.set_var_entry_rate_flow(
                "susceptible_fully" + comorbidity, "births_unvac")
            self.set_var_entry_rate_flow(
                "susceptible_vac" + comorbidity, "births_vac")

    def set_infection_flows(self):

        for comorbidity in self.comorbidities:
            for strain in self.strains:
                self.set_var_transfer_rate_flow(
                    "susceptible_fully" + comorbidity,
                    "latent_early" + strain + comorbidity,
                    "rate_force" + strain)
                self.set_var_transfer_rate_flow(
                    "susceptible_vac" + comorbidity,
                    "latent_early" + strain + comorbidity,
                    "rate_force_weak" + strain)
                self.set_var_transfer_rate_flow(
                    "susceptible_treated" + comorbidity,
                    "latent_early" + strain + comorbidity,
                    "rate_force_weak" + strain)
                self.set_var_transfer_rate_flow(
                    "latent_late" + strain + comorbidity,
                    "latent_early" + strain + comorbidity,
                    "rate_force_weak" + strain)

    def set_natural_history_flows(self):

        for comorbidity in self.comorbidities:
            for strain in self.strains:
                self.set_fixed_transfer_rate_flow(
                    "latent_early" + strain + comorbidity,
                    "latent_late" + strain + comorbidity,
                    "tb_rate_stabilise")
                for organ in self.organ_status:
                    self.set_fixed_transfer_rate_flow(
                        "latent_early" + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "tb_rate_early_progression" + organ)
                    self.set_fixed_transfer_rate_flow(
                        "latent_late" + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "tb_rate_late_progression" + organ)
                    self.set_fixed_transfer_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "latent_late" + strain + comorbidity,
                        "tb_rate_recover" + organ)
                    self.set_fixed_transfer_rate_flow(
                        "missed" + organ + strain + comorbidity,
                        "latent_late" + strain + comorbidity,
                        "tb_rate_recover" + organ)
                    self.set_infection_death_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "tb_rate_death" + organ)
                    self.set_infection_death_rate_flow(
                        "missed" + organ + strain + comorbidity,
                        "tb_rate_death" + organ)

                    self.set_fixed_transfer_rate_flow(
                        "detect" + organ + strain + comorbidity,
                        "latent_late" + strain + comorbidity,
                        "tb_rate_recover" + organ)
                    self.set_infection_death_rate_flow(
                        "detect" + organ + strain + comorbidity,
                        "tb_rate_death" + organ)

    def set_programmatic_flows(self):

        for comorbidity in self.comorbidities:
            for strain in self.strains:
                for organ in self.organ_status:

                    self.set_var_transfer_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "detect" + organ + strain + comorbidity,
                        "program_rate_detect")
                    self.set_var_transfer_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "missed" + organ + strain + comorbidity,
                        "program_rate_missed")
                    self.set_fixed_transfer_rate_flow(
                        "detect" + organ + strain + comorbidity,
                        "treatment_infect" + organ + strain + comorbidity,
                        "program_rate_start_treatment")
                    self.set_fixed_transfer_rate_flow(
                        "missed" + organ + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "program_rate_restart_presenting")

    def set_treatment_flows(self):

        for comorbidity in self.comorbidities:
            for strain in self.strains:
                for organ in self.organ_status:
                    self.set_fixed_transfer_rate_flow(
                        "treatment_infect" + organ + strain + comorbidity,
                        "treatment_noninfect" + organ + strain + comorbidity,
                        "program_rate_success_infect" + strain)
                    self.set_fixed_transfer_rate_flow(
                        "treatment_noninfect" + organ + strain + comorbidity,
                        "susceptible_treated" + comorbidity,
                        "program_rate_success_noninfect" + strain)
                    self.set_infection_death_rate_flow(
                        "treatment_infect" + organ + strain + comorbidity,
                        "program_rate_death_infect" + strain)
                    self.set_infection_death_rate_flow(
                        "treatment_noninfect" + organ + strain + comorbidity,
                        "program_rate_death_noninfect" + strain)
                    self.set_fixed_transfer_rate_flow(
                        "treatment_infect" + organ + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "program_rate_default_infect" + strain)
                    self.set_fixed_transfer_rate_flow(
                        "treatment_noninfect" + organ + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "program_rate_default_noninfect" + strain)


class StratifiedWithAmplification(StratifiedModel):

    def set_treatment_flows(self):

        for comorbidity in self.comorbidities:
            for organ in self.organ_status:
                for i in range(len(self.strains)):
                    strain = self.strains[i]

                    # Set treatment success and death flows (unaffected by amplification)
                    self.set_fixed_transfer_rate_flow(
                        "treatment_infect" + organ + strain + comorbidity,
                        "treatment_noninfect" + organ + strain + comorbidity,
                        "program_rate_success_infect" + strain)
                    self.set_fixed_transfer_rate_flow(
                        "treatment_noninfect" + organ + strain + comorbidity,
                        "susceptible_treated" + comorbidity,
                        "program_rate_success_noninfect" + strain)
                    self.set_infection_death_rate_flow(
                        "treatment_infect" + organ + strain + comorbidity,
                        "program_rate_death_infect" + strain)
                    self.set_infection_death_rate_flow(
                        "treatment_noninfect" + organ + strain + comorbidity,
                        "program_rate_death_noninfect" + strain)

                    # If it's the most resistant strain
                    if i == len(self.strains) - 1:
                        self.set_fixed_transfer_rate_flow(
                            "treatment_infect" + organ + strain + comorbidity,
                            "active" + organ + strain + comorbidity,
                            "program_rate_default_infect" + strain)
                        self.set_fixed_transfer_rate_flow(
                            "treatment_noninfect" + organ + strain + comorbidity,
                            "active" + organ + strain + comorbidity,
                            "program_rate_default_noninfect" + strain)
                    else:  # Otherwise, there is a more resistant strain available
                        amplify_to_strain = self.strains[i + 1]  # Is the more resistant strain
                        # Split default rates into amplification and non-amplification proportions
                        for treatment_stage in self.treatment_stages:
                            # Calculate amplification proportion
                            self.set_param("program_rate_default" + treatment_stage + "_noamplify" + strain,
                                           self.params["program_rate_default" + treatment_stage + strain]
                                           * (1 - self.params["proportion_amplification"]))
                            # Calculate non-amplification proportion
                            self.set_param("program_rate_default" + treatment_stage + "_amplify" + strain,
                                           self.params["program_rate_default" + treatment_stage + strain]
                                           * self.params["proportion_amplification"])
                            # Calculate equivalent functions
                            self.set_scaleup_var(
                                "program_rate_default" + treatment_stage + "_noamplify" + strain,
                                make_sigmoidal_curve(
                                    self.params["program_rate_default" + treatment_stage + "_noamplify" + strain],
                                    self.params["program_rate_default" + treatment_stage + "_noamplify" + strain]
                                    - self.params["program_rate_default" + treatment_stage + "_amplify" + strain],
                                    self.params["timepoint_introduce" + amplify_to_strain],
                                    self.params["timepoint_introduce" + amplify_to_strain] + 3.
                                )
                            )
                            self.set_scaleup_var(
                                "program_rate_default" + treatment_stage + "_amplify" + strain,
                                make_sigmoidal_curve(
                                    0.,
                                    self.params["program_rate_default" + treatment_stage + "_amplify" + strain],
                                    self.params["timepoint_introduce" + amplify_to_strain],
                                    self.params["timepoint_introduce" + amplify_to_strain] + 3.
                                )
                            )
                            # Actually set the flows
                            self.set_var_transfer_rate_flow(
                                "treatment_infect" + organ + strain + comorbidity,
                                "active" + organ + strain + comorbidity,
                                "program_rate_default" + treatment_stage + "_noamplify" + strain)
                            self.set_var_transfer_rate_flow(
                                "treatment_infect" + organ + strain + comorbidity,
                                "active" + organ + amplify_to_strain + comorbidity,
                                "program_rate_default" + treatment_stage + "_amplify" + strain)


class StratifiedWithMisassignment(StratifiedWithAmplification):

    def initialise_compartments(self, input_compartments):

        if input_compartments is None:
            input_compartments = {
                "susceptible_fully":
                    2e7,
                "active":
                    3.}

        # Initialise all compartments to zero
        for compartment in self.compartment_types:
            for comorbidity in self.comorbidities:
                if "susceptible" in compartment:  # Replicate for comorbidities only
                    self.set_compartment(compartment + comorbidity, 0.)
                elif "latent" in compartment:  # Replicate for comorbidities and strains
                    for strain in self.strains:
                        self.set_compartment(compartment + strain + comorbidity, 0.)
                elif "active" in compartment or "missed" in compartment:
                    for strain in self.strains:
                        for organ in self.organ_status:
                            self.set_compartment(compartment + organ + strain + comorbidity, 0.)
                else:  # Mis-assignment by strain
                    for strain in self.strains:
                        for organ in self.organ_status:
                            for assigned_strain in self.strains:
                                self.set_compartment(compartment + organ + strain + "_as"+assigned_strain[1:] + comorbidity, 0.)

        # Put in values from input_compartments - now initialise to DS-TB only
        for compartment in self.compartment_types:
            if compartment in input_compartments:
                if "susceptible" in compartment:
                    for comorbidity in self.comorbidities:
                        self.set_compartment(compartment + comorbidity,
                                             input_compartments[compartment]
                                             / len(self.comorbidities))
                elif "latent" in compartment:
                    for comorbidity in self.comorbidities:
                        self.set_compartment(compartment + "_ds" + comorbidity,
                                             input_compartments[compartment]
                                             / len(self.comorbidities))
                else:
                    for comorbidity in self.comorbidities:
                        for organ in self.organ_status:
                            self.set_compartment(compartment + organ + "_ds" + comorbidity,
                                                 input_compartments[compartment]
                                                 / len(self.comorbidities)
                                                 / len(self.organ_status))

    def set_natural_history_flows(self):

        for comorbidity in self.comorbidities:
            for strain in self.strains:
                self.set_fixed_transfer_rate_flow(
                    "latent_early" + strain + comorbidity,
                    "latent_late" + strain + comorbidity,
                    "tb_rate_stabilise")
                for organ in self.organ_status:
                    self.set_fixed_transfer_rate_flow(
                        "latent_early" + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "tb_rate_early_progression" + organ)
                    self.set_fixed_transfer_rate_flow(
                        "latent_late" + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "tb_rate_late_progression" + organ)
                    self.set_fixed_transfer_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "latent_late" + strain + comorbidity,
                        "tb_rate_recover" + organ)
                    self.set_fixed_transfer_rate_flow(
                        "missed" + organ + strain + comorbidity,
                        "latent_late" + strain + comorbidity,
                        "tb_rate_recover" + organ)
                    self.set_infection_death_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "tb_rate_death" + organ)
                    self.set_infection_death_rate_flow(
                        "missed" + organ + strain + comorbidity,
                        "tb_rate_death" + organ)

                    for assigned_strain in self.strains:
                        self.set_infection_death_rate_flow(
                            "detect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "tb_rate_death" + organ)
                        self.set_fixed_transfer_rate_flow(
                            "detect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "latent_late" + strain + comorbidity,
                            "tb_rate_recover" + organ)

    def set_programmatic_flows(self):

        for i in range(len(self.strains)):
            strain = self.strains[i]
            for j in range(len(self.strains)):
                assigned_strain = self.strains[j]
                # Chance of being assigned to the strain two levels less resistant (XDR to DS)
                if i == j+2:
                    next_strain = self.strains[i - 1]
                    assignment_probability =\
                        (1. - self.params["program_prop_assign" + next_strain])
                # Chance of being assigned to the next less resistant strain
                # if there are two less resistant strains available (XDR to MDR)
                elif i == 2 and j == 1:
                    next_strain = self.strains[i - 1]
                    assignment_probability =\
                        (1. - self.params["program_prop_assign" + strain]) * self.params["program_prop_assign" + next_strain]
                # Chance of being assigned to the next less resistant strain
                # if the assigned strain is the least resistant one (MDR to DS)
                elif i == j+1 and j == 0:
                    assignment_probability =\
                        (1. - self.params["program_prop_assign" + strain])
                # Chance of being assigned to the correct strain, DS-TB
                elif i == 0 and j == 0:
                    assignment_probability = 1.
                # Chance of being assigned to the correct strain, MDR-TB
                elif i == 1 and j == 1:
                    assignment_probability =\
                        self.params["program_prop_assign" + strain]
                # Chance of being assigned to the correct strain, XDR-TB
                elif i == 2 and j == 2:
                    next_strain = self.strains[i - 1]
                    assignment_probability =\
                        self.params["program_prop_assign" + strain] * self.params["program_prop_assign" + next_strain]
                # Can't be assigned to a more resistant strain than you have (currently)
                elif i < j:
                    assignment_probability = 0.
                # Set the parameter values
                if assignment_probability == 0.:
                    self.set_param("program_rate_detect" + strain + "_as"+assigned_strain[1:], assignment_probability)
                    for comorbidity in self.comorbidities:
                        for organ in self.organ_status:
                            self.set_fixed_transfer_rate_flow(
                                "active" + organ + strain + comorbidity,
                                "detect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                                "program_rate_detect" + strain + "_as"+assigned_strain[1:])
                else:
                    self.set_scaleup_var(
                        "program_rate_detect" + strain + "_as"+assigned_strain[1:],
                        make_two_step_curve(
                            self.params["pretreatment_available_proportion"] * self.params["program_rate_detect"] * assignment_probability,
                            self.params["dots_start_proportion"]  * self.params["program_rate_detect"] * assignment_probability,
                            self.params["program_rate_detect"] * assignment_probability,
                            self.params["treatment_available_date"], self.params["dots_start_date"], self.params["finish_scaleup_date"]))
                    for comorbidity in self.comorbidities:
                        for organ in self.organ_status:
                            self.set_var_transfer_rate_flow(
                                "active" + organ + strain + comorbidity,
                                "detect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                                "program_rate_detect" + strain + "_as"+assigned_strain[1:])
                # print('\n')
                # print(strain)
                # print(assigned_strain)
                # print(assignment_probability)

        self.set_scaleup_var(
            "program_rate_missed",
            make_two_step_curve(
                self.params["pretreatment_available_proportion"] * self.params["program_rate_missed"],
                self.params["dots_start_proportion"] * self.params["program_rate_missed"],
                self.params["program_rate_missed"],
                self.params["treatment_available_date"], self.params["dots_start_date"], self.params["finish_scaleup_date"]))

        for comorbidity in self.comorbidities:
            for strain in self.strains:
                for organ in self.organ_status:
                    self.set_var_transfer_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "missed" + organ + strain + comorbidity,
                        "program_rate_missed")
                    self.set_fixed_transfer_rate_flow(
                        "missed" + organ + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "program_rate_restart_presenting")
                    for assigned_strain in self.strains:
                        self.set_fixed_transfer_rate_flow(
                            "detect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "treatment_infect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "program_rate_start_treatment")

    def set_treatment_flows(self):

        for comorbidity in self.comorbidities:
            for organ in self.organ_status:
                for i in range(len(self.strains)):
                    strain = self.strains[i]
                    for j in range(len(self.strains)):
                        assigned_strain = self.strains[j]
                        # Which treatment parameters to use - for the strain or for inappropriate treatment
                        if i <= j:
                            strain_or_inappropriate = strain
                        else:
                            strain_or_inappropriate = "_inappropriate"
                        # Set treatment success and death flows (unaffected by amplification)
                        self.set_fixed_transfer_rate_flow(
                            "treatment_infect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "treatment_noninfect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "program_rate_success_infect" + strain_or_inappropriate)
                        self.set_fixed_transfer_rate_flow(
                            "treatment_noninfect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "susceptible_treated" + comorbidity,
                            "program_rate_success_noninfect" + strain_or_inappropriate)
                        self.set_infection_death_rate_flow(
                            "treatment_infect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "program_rate_death_infect" + strain_or_inappropriate)
                        self.set_infection_death_rate_flow(
                            "treatment_noninfect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "program_rate_death_noninfect" + strain_or_inappropriate)

                        # If it's the most resistant strain
                        if i == len(self.strains) - 1:
                            self.set_fixed_transfer_rate_flow(
                                "treatment_infect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                                "active" + organ + strain + comorbidity,
                                "program_rate_default_infect" + strain_or_inappropriate)
                            self.set_fixed_transfer_rate_flow(
                                "treatment_noninfect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                                "active" + organ + strain + comorbidity,
                                "program_rate_default_noninfect" + strain_or_inappropriate)
                        else:  # Otherwise, there is a more resistant strain available
                            amplify_to_strain = self.strains[i + 1]  # Is the more resistant strain
                            # Split default rates into amplification and non-amplification proportions
                            for treatment_stage in self.treatment_stages:
                                # Calculate amplification proportion
                                self.set_param("program_rate_default" + treatment_stage + "_noamplify" + strain_or_inappropriate,
                                               self.params["program_rate_default" + treatment_stage + strain_or_inappropriate]
                                               * (1 - self.params["proportion_amplification"]))
                                # Calculate non-amplification proportion
                                self.set_param("program_rate_default" + treatment_stage + "_amplify" + strain_or_inappropriate,
                                               self.params["program_rate_default" + treatment_stage + strain_or_inappropriate]
                                               * self.params["proportion_amplification"])
                                # Calculate equivalent functions
                                self.set_scaleup_var(
                                    "program_rate_default" + treatment_stage + "_noamplify" + strain_or_inappropriate,
                                    make_sigmoidal_curve(
                                        self.params["program_rate_default" + treatment_stage + "_noamplify" + strain_or_inappropriate],
                                        self.params["program_rate_default" + treatment_stage + "_noamplify" + strain_or_inappropriate]
                                        - self.params["program_rate_default" + treatment_stage + "_amplify" + strain_or_inappropriate],
                                        self.params["timepoint_introduce" + amplify_to_strain],
                                        self.params["timepoint_introduce" + amplify_to_strain] + 3.
                                    )
                                )
                                self.set_scaleup_var(
                                    "program_rate_default" + treatment_stage + "_amplify" + strain_or_inappropriate,
                                    make_sigmoidal_curve(
                                        0.,
                                        self.params["program_rate_default" + treatment_stage + "_amplify" + strain_or_inappropriate],
                                        self.params["timepoint_introduce" + amplify_to_strain],
                                        self.params["timepoint_introduce" + amplify_to_strain] + 3.
                                    )
                                )
                                # Set the flows
                                self.set_var_transfer_rate_flow(
                                    "treatment_infect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                                    "active" + organ + strain + comorbidity,
                                    "program_rate_default" + treatment_stage + "_noamplify" + strain_or_inappropriate)
                                self.set_var_transfer_rate_flow(
                                    "treatment_infect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                                    "active" + organ + amplify_to_strain + comorbidity,
                                    "program_rate_default" + treatment_stage + "_amplify" + strain_or_inappropriate)


class StratifiedWithMisassignmentAndLowQuality(StratifiedWithMisassignment):

    def __init__(self,
                 number_of_organs=3,
                 number_of_strains=1,
                 number_of_comorbidities=1,
                 input_parameters=None,
                 input_compartments=None):

        BaseModel.__init__(self)

        self.define_model_structure(number_of_organs, number_of_strains, number_of_comorbidities)

        self.initialise_compartments(input_compartments)

        self.set_parameters(input_parameters)

        self.split_default_death_proportions()

        self.ensure_all_progressions_go_somewhere()

        self.find_natural_history_flows()

        self.find_detection_rates()

        self.find_equal_detection_rates()

        self.find_lowquality_detections()

        self.find_treatment_rates()

    def define_model_structure(self, number_of_organs, number_of_strains, number_of_comorbidities):

        self.compartment_types = [
            "susceptible_fully",
            "susceptible_vac",
            "susceptible_treated",
            "latent_early",
            "latent_late",
            "active",
            "detect",
            "missed",
            "lowquality",
            "treatment_infect",
            "treatment_noninfect"]

        self.broad_compartment_types = [
            "susceptible",
            "latent",
            "active",
            "missed",
            "treatment"]

        available_organs = [
            "_smearpos",
            "_smearneg",
            "_extrapul"]
        self.organ_status =\
            available_organs[0: number_of_organs]

        available_strains = [
            "_ds",
            "_mdr",
            "_xdr"]
        self.strains\
            = available_strains[0: number_of_strains]

        available_comorbidities = [
            "_nocomorbs",
            "_hiv",
            "_diabetes"]
        self.comorbidities\
            = available_comorbidities[0: number_of_comorbidities]

        self.treatment_stages = [
            "_infect",
            "_noninfect"]

        self.infectious_tags = [
            "active",
            "missed",
            "detect",
            "lowquality",
            "treatment_infect"]

    def initialise_compartments(self, input_compartments):

        if input_compartments is None:
            input_compartments = {
                "susceptible_fully":
                    2e7,
                "active":
                    3.}

        # Initialise all compartments to zero
        for compartment in self.compartment_types:
            for comorbidity in self.comorbidities:
                if "susceptible" in compartment:  # Replicate for comorbidities only
                    self.set_compartment(compartment + comorbidity, 0.)
                elif "latent" in compartment:  # Replicate for comorbidities and strains
                    for strain in self.strains:
                        self.set_compartment(compartment + strain + comorbidity, 0.)
                elif "active" in compartment or "missed" in compartment or "lowquality" in compartment:
                    for strain in self.strains:
                        for organ in self.organ_status:
                            self.set_compartment(compartment + organ + strain + comorbidity, 0.)
                else:  # Mis-assignment by strain
                    for strain in self.strains:
                        for organ in self.organ_status:
                            for assigned_strain in self.strains:
                                self.set_compartment(compartment + organ + strain + "_as"+assigned_strain[1:] + comorbidity, 0.)

        # Put in values from input_compartments - now initialise to DS-TB only
        for compartment in self.compartment_types:
            if compartment in input_compartments:
                if "susceptible" in compartment:
                    for comorbidity in self.comorbidities:
                        self.set_compartment(compartment + comorbidity,
                                             input_compartments[compartment]
                                             / len(self.comorbidities))
                elif "latent" in compartment:
                    for comorbidity in self.comorbidities:
                        self.set_compartment(compartment + "_ds" + comorbidity,
                                             input_compartments[compartment]
                                             / len(self.comorbidities))
                else:
                    for comorbidity in self.comorbidities:
                        for organ in self.organ_status:
                            self.set_compartment(compartment + organ + "_ds" + comorbidity,
                                                 input_compartments[compartment]
                                                 / len(self.comorbidities)
                                                 / len(self.organ_status))

    def find_lowquality_detections(self):

        self.set_param(
            "program_rate_enterlowquality",
            self.params["program_rate_detect"]\
            * self.params["program_prop_lowquality"]\
            / (1. - self.params["program_prop_lowquality"]))

    def set_natural_history_flows(self):

        for comorbidity in self.comorbidities:
            for strain in self.strains:
                self.set_fixed_transfer_rate_flow(
                    "latent_early" + strain + comorbidity,
                    "latent_late" + strain + comorbidity,
                    "tb_rate_stabilise")
                for organ in self.organ_status:
                    self.set_fixed_transfer_rate_flow(
                        "latent_early" + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "tb_rate_early_progression" + organ)
                    self.set_fixed_transfer_rate_flow(
                        "latent_late" + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "tb_rate_late_progression" + organ)
                    self.set_fixed_transfer_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "latent_late" + strain + comorbidity,
                        "tb_rate_recover" + organ)
                    self.set_fixed_transfer_rate_flow(
                        "missed" + organ + strain + comorbidity,
                        "latent_late" + strain + comorbidity,
                        "tb_rate_recover" + organ)
                    self.set_infection_death_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "tb_rate_death" + organ)
                    self.set_infection_death_rate_flow(
                        "missed" + organ + strain + comorbidity,
                        "tb_rate_death" + organ)

                    # Added natural history flows for low quality care patients
                    self.set_fixed_transfer_rate_flow(
                        "lowquality" + organ + strain + comorbidity,
                        "latent_late" + strain + comorbidity,
                        "tb_rate_recover" + organ)
                    self.set_infection_death_rate_flow(
                        "lowquality" + organ + strain + comorbidity,
                        "tb_rate_death" + organ)

                    for assigned_strain in self.strains:
                        self.set_infection_death_rate_flow(
                            "detect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "tb_rate_death" + organ)
                        self.set_fixed_transfer_rate_flow(
                            "detect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "latent_late" + strain + comorbidity,
                            "tb_rate_recover" + organ)

    def set_programmatic_flows(self):

        for i in range(len(self.strains)):
            strain = self.strains[i]
            for j in range(len(self.strains)):
                assigned_strain = self.strains[j]
                # Chance of being assigned to the strain two levels less resistant (XDR to DS)
                if i == j+2:
                    next_strain = self.strains[i - 1]
                    assignment_probability =\
                        (1. - self.params["program_prop_assign" + next_strain])
                # Chance of being assigned to the next less resistant strain
                # if there are two less resistant strains available (XDR to MDR)
                elif i == 2 and j == 1:
                    next_strain = self.strains[i - 1]
                    assignment_probability =\
                        (1. - self.params["program_prop_assign" + strain]) * self.params["program_prop_assign" + next_strain]
                # Chance of being assigned to the next less resistant strain
                # if the assigned strain is the least resistant one (MDR to DS)
                elif i == j+1 and j == 0:
                    assignment_probability =\
                        (1. - self.params["program_prop_assign" + strain])
                # Chance of being assigned to the correct strain, DS-TB
                elif i == 0 and j == 0:
                    assignment_probability = 1.
                # Chance of being assigned to the correct strain, MDR-TB
                elif i == 1 and j == 1:
                    assignment_probability =\
                        self.params["program_prop_assign" + strain]
                # Chance of being assigned to the correct strain, XDR-TB
                elif i == 2 and j == 2:
                    next_strain = self.strains[i - 1]
                    assignment_probability =\
                        self.params["program_prop_assign" + strain] * self.params["program_prop_assign" + next_strain]
                # Can't be assigned to a more resistant strain than you have (currently)
                elif i < j:
                    assignment_probability = 0.
                # Set the parameter values
                if assignment_probability == 0.:
                    self.set_param("program_rate_detect" + strain + "_as"+assigned_strain[1:], assignment_probability)
                    for comorbidity in self.comorbidities:
                        for organ in self.organ_status:
                            self.set_fixed_transfer_rate_flow(
                                "active" + organ + strain + comorbidity,
                                "detect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                                "program_rate_detect" + strain + "_as"+assigned_strain[1:])
                else:
                    self.set_scaleup_var(
                        "program_rate_detect" + strain + "_as"+assigned_strain[1:],
                        make_two_step_curve(
                            self.params["pretreatment_available_proportion"] * self.params["program_rate_detect"] * assignment_probability,
                            self.params["dots_start_proportion"] * self.params["program_rate_detect"] * assignment_probability,
                            self.params["program_rate_detect"] * assignment_probability,
                            self.params["treatment_available_date"], self.params["dots_start_date"], self.params["finish_scaleup_date"]))
                    # Set the detection flows
                    for comorbidity in self.comorbidities:
                        for organ in self.organ_status:
                            self.set_var_transfer_rate_flow(
                                "active" + organ + strain + comorbidity,
                                "detect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                                "program_rate_detect" + strain + "_as"+assigned_strain[1:])

        for missed_or_lowquality in ["_missed", "_enterlowquality"]:
            self.set_scaleup_var(
                "program_rate" + missed_or_lowquality,
                make_two_step_curve(
                    self.params["pretreatment_available_proportion"] * self.params[
                        "program_rate" + missed_or_lowquality],
                    self.params["dots_start_proportion"] * self.params["program_rate" + missed_or_lowquality],
                    self.params["program_rate" + missed_or_lowquality],
                    self.params["treatment_available_date"], self.params["dots_start_date"],
                    self.params["finish_scaleup_date"]))

        for comorbidity in self.comorbidities:
            for strain in self.strains:
                for organ in self.organ_status:
                    self.set_var_transfer_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "missed" + organ + strain + comorbidity,
                        "program_rate_missed")
                    self.set_fixed_transfer_rate_flow(
                        "missed" + organ + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "program_rate_restart_presenting")
                    self.set_var_transfer_rate_flow(
                        "active" + organ + strain + comorbidity,
                        "lowquality" + organ + strain + comorbidity,
                        "program_rate_enterlowquality")
                    self.set_fixed_transfer_rate_flow(
                        "lowquality" + organ + strain + comorbidity,
                        "active" + organ + strain + comorbidity,
                        "program_rate_leavelowquality")

                    for assigned_strain in self.strains:
                        self.set_fixed_transfer_rate_flow(
                            "detect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "treatment_infect" + organ + strain + "_as"+assigned_strain[1:] + comorbidity,
                            "program_rate_start_treatment")

