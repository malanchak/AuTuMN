
import tool_kit
import model
import os
import data_processing
import numpy
import datetime
from scipy.stats import norm, beta, gamma
from scipy.optimize import minimize
import autumn.economics
import itertools
from pyDOE import lhs


def elementwise_list_addition(increment, list_to_increment):
    """
    Simple method to element-wise increment a list by the values in another list of the same length.
    """

    assert len(increment) == len(list_to_increment), 'Attempted to add two lists of different lengths'
    return [sum(x) for x in zip(list_to_increment, increment)]


def elementwise_list_division(numerator, denominator):
    """
    Simple method to element-wise divide a list by the values in another list of the same length.
    """

    assert len(numerator) == len(denominator), 'Attempted to divide two lists of different lengths'
    return [n / d for n, d in zip(numerator, denominator)]


def elementwise_list_percentage(numerator, denominator):
    """
    Simple method to element-wise divide a list by the values in another list of the same length to produce a
    percentage.
    """

    assert len(numerator) == len(denominator), 'Attempted to divide two lists of different lengths'
    return [n / d * 1e2 for n, d in zip(numerator, denominator)]


def find_uncertainty_output_weights(list, method, relative_weights=(1., 2.)):
    """
    Creates a set of "weights" to determine the proportion of the log-likelihood to be contributed by the years
    considered in the calibration.

    Args:
        list: A list of the years that the weights are to be applied to.
        method: Choice of method.
        relative_weights: Relative size of the starting and ending weights if method is 1.
    """

    # linearly scaling weights summing to one
    if method == 1:
        if len(list) == 1:
            return [1.]
        else:
            weights = numpy.linspace(relative_weights[0], relative_weights[1], num=len(list))
            return [i / sum(weights) for i in weights]

    # equally distributed weights summing to one
    elif method == 2:
        return [1. / float(len(list))] * len(list)

    # all weights equal to one
    elif method == 3:
        return [1.] * len(list)


def is_parameter_value_valid(parameter):
    """
    Determine whether a number is finite and positive and so valid for the model as a parameter.
    """

    return numpy.isfinite(parameter) and parameter > 0.


def find_log_probability_density(distribution, param_val, bounds, additional_params=None):
    """
    Find the log probability density for the parameter value being considered. Uniform is the default distribution if no
    other distribution is specified.

    Args:
        distribution: String specifying the general type of distribution (uniform default)
        param_val: The parameter value
        bounds: Two element list for the upper and lower limits of the distribution
        additional_params: Any additional parameters to the distribution if not completely specified with bounds
    Returns:
        prior_log_likelihood: Prior log likelihood associated with the individual parameter fed in to this function
    """

    # save some code repetition by finding the parameter value's distance through the distribution width
    normalised_param_value = (param_val - bounds[0]) / (bounds[1] - bounds[0])

    # find the log probability density
    if distribution == 'beta_2_2':
        prior_log_likelihood = beta.logpdf(normalised_param_value, 2., 2.)
    elif distribution == 'beta_mean_stdev':
        alpha_value = ((1. - additional_params[0]) / additional_params[1] ** 2. - 1. / additional_params[0]) \
                      * additional_params[0] ** 2.
        beta_value = alpha_value * (1. / additional_params[0] - 1.)
        prior_log_likelihood = beta.logpdf(normalised_param_value, alpha_value, beta_value)
    elif distribution == 'beta_params':
        prior_log_likelihood = beta.logpdf(normalised_param_value, additional_params[0], additional_params[1])
    elif distribution == 'gamma_mean_stdev':
        prior_log_likelihood = gamma.logpdf(param_val, (additional_params[0] / additional_params[1]) ** 2.,
                                             scale=additional_params[1] ** 2. / additional_params[0])
    elif distribution == 'gamma_params':
        prior_log_likelihood = gamma.logpdf(param_val, additional_params[0])
    else:
        prior_log_likelihood = numpy.log(1. / (bounds[1] - bounds[0]))
    return prior_log_likelihood


class ModelRunner:
    def __init__(self, gui_inputs, runtime_outputs, js_gui=None):
        """
        Instantiation method for model runner - currently including some attributes that should be set externally, e.g.
        in the GUI(s).

        Args:
            gui_inputs: Inputs from the off-line Tkinter GUI
            runtime_outputs: Offline GUI window for commenting
            js_gui: JavaScript GUI inputs
        """

        # conversion of inputs to attributes
        self.gui_inputs = gui_inputs
        self.scenarios = self.gui_inputs['scenarios_to_run']
        self.runtime_outputs = runtime_outputs
        self.inputs = data_processing.Inputs(gui_inputs, runtime_outputs, js_gui=js_gui)
        self.inputs.read_and_load_data()

        # preparing for basic runs
        self.models = {}
        self.interventions_to_cost = self.inputs.interventions_to_cost

        # uncertainty-related attributes
        self.is_last_run_success = False
        self.loglikelihoods = []
        self.outputs_unc = [{'key': 'incidence',
                             'posterior_width': None,
                             'width_multiplier': 2.  # width of normal posterior relative to range of allowed values
                             }]
        self.all_parameters_tried = {}  # all refers to applying to every model run (rather than accepted only)
        self.all_compartment_values_tried = {}
        self.all_other_adjustments_made = {}
        self.whether_accepted_list = []
        self.accepted_indices = []
        self.rejected_indices = []
        self.solns_for_extraction = ['compartment_soln', 'fraction_soln']
        self.arrays_for_extraction = ['flow_array', 'fraction_array', 'soln_array', 'var_array', 'costs']
        self.acceptance_dict = {}
        self.rejection_dict = {}
        self.uncertainty_percentiles = {}
        self.n_centiles_for_shading = 100
        self.percentiles = [2.5, 50., 97.5] + list(numpy.linspace(0., 100., self.n_centiles_for_shading * 2 + 1))
        self.random_start = False  # whether to start from a random point, as opposed to the manually calibrated value
        self.intervention_uncertainty = self.inputs.intervention_uncertainty
        self.relative_difference_to_adjust_mortality = 1.1
        self.amount_to_adjust_mortality = .02

        # optimisation attributes
        self.optimisation = False  # leave True even if loading optimisation results
        self.opti_outputs_dir = 'saved_optimisation_analyses'
        self.indicator_to_minimise = 'incidence'  # currently must be 'incidence' or 'mortality'
        self.annual_envelope = [112.5e6]  # size of funding envelope in scenarios to be run
        self.save_opti = True
        self.load_optimisation = False  # optimisation will not be run if true
        self.total_funding = None  # funding for entire period
        self.f_tol = {'incidence': 0.5,
                      'mortality': 0.05}  # stopping condition for optimisation algorithm (differs by indicator)
        self.year_end_opti = 2035.  # model is run until that date during optimisation
        self.acceptable_combinations = []  # list of intervention combinations that can be considered with funding
        self.opti_results = {}  # store all the results that we need for optimisation
        self.optimised_combinations = []
        self.optimal_allocation = {}
        self.interventions_considered_for_opti \
            = ['engage_lowquality', 'xpert', 'cxrxpertacf_prison', 'cxrxpertacf_urbanpoor', 'ipt_age0to5',
               'intensive_screening']  # interventions that must appear in optimal plan
        self.interventions_forced_for_opti = ['engage_lowquality', 'ipt_age0to5', 'intensive_screening']

        # output-related attributes
        self.epi_outputs_to_analyse = ['incidence', 'prevalence', 'mortality', 'true_mortality', 'notifications']
        self.epi_outputs = {}
        self.epi_outputs_uncertainty = {}
        self.epi_outputs_uncertainty_centiles = None
        self.cost_outputs = {}
        self.cost_outputs_dict = {}
        self.cost_outputs_integer_dict = {}
        self.cost_outputs_uncertainty = {}
        self.cost_outputs_uncertainty_centiles = None
        self.additional_cost_types = ['inflated', 'discounted', 'discounted_inflated']
        self.cost_types = self.additional_cost_types + ['raw']

        # saving-related
        self.attributes_to_save \
            = ['epi_outputs', 'epi_outputs_uncertainty', 'cost_outputs', 'cost_outputs_dict',
               'cost_outputs_integer_dict', 'cost_outputs_uncertainty', 'accepted_indices', 'rejected_indices',
               'all_parameters_tried', 'whether_accepted_list', 'acceptance_dict', 'rejection_dict', 'loglikelihoods',
               'all_other_adjustments_made']

        # GUI-related
        self.emit_delay = 0.1
        self.plot_count = 0
        self.js_gui = js_gui
        if self.js_gui: self.js_gui('init')

    ''' master methods to run other methods '''

    def master_runner(self):
        """
        Calls methods to run model with each of the three fundamental approaches.
        """

        # prepare file for saving
        out_dir = 'saved_uncertainty_analyses'
        if not os.path.isdir(out_dir): os.makedirs(out_dir)
        storage_file_name = os.path.join(out_dir, 'store.pkl')

        # load a saved simulation
        if self.gui_inputs['pickle_uncertainty'] == 'Load':
            self.add_comment_to_gui_window('Loading results from previous simulation')
            loaded_data = tool_kit.pickle_load(storage_file_name)
            self.add_comment_to_gui_window('Loading finished')
            for attribute in loaded_data: setattr(self, attribute, loaded_data[attribute])

        # or run the manual scenarios as requested by user
        else:
            self.run_manual_calibration()
            if self.gui_inputs['output_uncertainty']: self.run_epi_uncertainty()
            if self.intervention_uncertainty: self.run_intervention_uncertainty()

        # save uncertainty if requested
        if self.gui_inputs['pickle_uncertainty'] == 'Save':
            data_to_save = {}
            for attribute in self.attributes_to_save: data_to_save[attribute] = getattr(self, attribute)
            tool_kit.pickle_save(data_to_save, storage_file_name)
            self.add_comment_to_gui_window('Uncertainty results saved to disc')

        # master optimisation method
        if self.optimisation and not self.load_optimisation: self.run_optimisation()

        # prepare file for saving, save and load as requested
        if not os.path.isdir(self.opti_outputs_dir): os.makedirs(self.opti_outputs_dir)
        self.load_opti_results()
        self.save_opti_results()

        # notify user that model running has finished
        self.add_comment_to_gui_window('Model running complete')

    def run_manual_calibration(self):
        """
        Runs the scenarios a single time, starting from baseline with parameter values as specified in spreadsheets.
        """

        # run fo each scenario, including baseline which is always included by default
        for scenario in self.scenarios:

            # name, initialise and describe model, with appropriate times for scenario runs if required
            self.models[scenario] = model.ConsolidatedModel(scenario, self.inputs, self.gui_inputs)
            if scenario > 0: self.prepare_new_model_from_baseline(scenario)
            self.add_comment_to_gui_window('Running %s conditions for %s using point estimates for parameters.'
                                           % ('manual_' + tool_kit.find_scenario_string_from_number(scenario),
                                              self.gui_inputs['country']))

            # integrate
            self.models[scenario].integrate()

            # interpret
            self.epi_outputs[scenario] \
                = self.find_epi_outputs(scenario, outputs_to_analyse=self.epi_outputs_to_analyse,
                                        strata=[self.models[scenario].agegroups, self.models[scenario].riskgroups])
            if self.models[scenario].interventions_to_cost: self.find_cost_outputs(scenario)
            self.find_population_fractions(
                scenario=scenario, strata=[self.models[scenario].agegroups, self.models[scenario].riskgroups])

    def prepare_new_model_from_baseline(self, scenario):
        """
        Method to set the start time of a model and load the compartment values from the baseline run.

        Args:
            scenario: Scenario number
        """

        scenario_start_time_index \
            = self.models[0].find_time_index(self.inputs.model_constants['before_intervention_time'])
        start_time = self.models[0].times[scenario_start_time_index]
        self.models[scenario].start_time = start_time
        self.models[scenario].next_time_point = start_time
        self.models[scenario].loaded_compartments = self.models[0].load_state(scenario_start_time_index)

    ''' output interpretation methods '''

    def find_epi_outputs(self, scenario, outputs_to_analyse, strata=[]):
        """
        Method to extract all requested epidemiological outputs from the models. Intended ultimately to be flexible\
        enough for use for analysis of scenarios, uncertainty and optimisation.

        Args:
            scenario: The number value representing the scenario of the model to be analysed
            outputs_to_analyse: List of strings for the outputs of interest to be worked through
            strata: Whether it is necessary to provide outputs by any model compartmental stratifications
        """

        ''' compulsory elements to calculate '''

        if 'population' not in outputs_to_analyse: outputs_to_analyse.append('population')
        epi_outputs = {'times': self.models[scenario].times}

        ''' unstratified outputs '''

        # initialise lists to zeros to allow incrementation
        for output in outputs_to_analyse:
            epi_outputs[output] = [0.] * len(epi_outputs['times'])
            for strain in self.models[scenario].strains:
                epi_outputs[output + strain] = [0.] * len(epi_outputs['times'])

        # population
        for compartment in self.models[scenario].compartments:
            epi_outputs['population'] \
                = elementwise_list_addition(self.models[scenario].get_compartment_soln(compartment),
                                            epi_outputs['population'])

        # replace zeroes with small numbers for division
        total_denominator = tool_kit.prepare_denominator(epi_outputs['population'])

        # to allow calculation by strain and the total output
        strains = self.models[scenario].strains + ['']

        # incidence
        if 'incidence' in outputs_to_analyse:
            for strain in strains:
                for from_label, to_label, rate in self.models[scenario].var_transfer_rate_flows:  # variable flows
                    if 'latent' in from_label and 'active' in to_label and strain in to_label:
                        incidence_increment = self.models[scenario].get_compartment_soln(from_label) \
                                              * self.models[scenario].get_var_soln(rate) / total_denominator * 1e5
                        epi_outputs['incidence' + strain] \
                            = elementwise_list_addition(incidence_increment, epi_outputs['incidence' + strain])
                for from_label, to_label, rate in self.models[scenario].fixed_transfer_rate_flows:  # fixed flows
                    if 'latent' in from_label and 'active' in to_label and strain in to_label:
                        incidence_increment = self.models[scenario].get_compartment_soln(from_label) \
                                              * rate / total_denominator * 1e5
                        epi_outputs['incidence' + strain] \
                            = elementwise_list_addition(incidence_increment, epi_outputs['incidence' + strain])

            # find percentage incidence by strain
            if len(self.models[scenario].strains) > 1:
                for strain in self.models[scenario].strains:
                    epi_outputs['perc_incidence' + strain] \
                        = elementwise_list_percentage(epi_outputs['incidence' + strain],
                                                      tool_kit.prepare_denominator(epi_outputs['incidence']))

        # notifications
        if 'notifications' in outputs_to_analyse:
            for strain in strains:
                for from_label, to_label, rate in self.models[scenario].var_transfer_rate_flows:
                    if 'active' in from_label and 'detect' in to_label and strain in to_label:
                        notifications_increment \
                            = self.models[scenario].get_compartment_soln(from_label) \
                              * self.models[scenario].get_var_soln(rate)
                        epi_outputs['notifications' + strain] \
                            = elementwise_list_addition(notifications_increment, epi_outputs['notifications' + strain])

        # mortality
        if 'mortality' in outputs_to_analyse:
            for strain in strains:

                # fixed flows are outside of the health system and so the natural death contribution is reduced
                for from_label, rate in self.models[scenario].fixed_infection_death_rate_flows:
                    if strain in from_label:
                        mortality_increment = self.models[scenario].get_compartment_soln(from_label) \
                                              * rate / total_denominator * 1e5
                        epi_outputs['true_mortality' + strain] \
                            = elementwise_list_addition(mortality_increment, epi_outputs['true_mortality' + strain])
                        epi_outputs['mortality' + strain] \
                            = elementwise_list_addition(
                                mortality_increment * self.models[scenario].params['program_prop_death_reporting'],
                                epi_outputs['mortality' + strain])

                # variable flows are within the health system and so true and reported are dealt with the same way
                for from_label, rate in self.models[scenario].var_infection_death_rate_flows:
                    if strain in from_label:
                        mortality_increment = self.models[scenario].get_compartment_soln(from_label) \
                                              * self.models[scenario].get_var_soln(rate) / total_denominator * 1e5
                        for mortality_type in ['true_mortality', 'mortality']:
                            epi_outputs[mortality_type + strain] \
                                = elementwise_list_addition(mortality_increment, epi_outputs[mortality_type + strain])

        # prevalence
        if 'prevalence' in outputs_to_analyse:
            for strain in strains:
                for label in self.models[scenario].labels:
                    if 'susceptible' not in label and 'latent' not in label and strain in label:
                        prevalence_increment \
                            = self.models[scenario].get_compartment_soln(label) / total_denominator * 1e5
                        epi_outputs['prevalence' + strain] \
                            = elementwise_list_addition(prevalence_increment, epi_outputs['prevalence' + strain])

        # infections (absolute number)
        if 'infections' in outputs_to_analyse:
            for strain in strains:
                for from_label, to_label, rate in self.models[scenario].var_transfer_rate_flows:
                    if 'latent_early' in to_label and strain in to_label:
                        epi_outputs['infections' + strain] \
                            = elementwise_list_addition(self.models[scenario].get_compartment_soln(from_label)
                                                        * self.models[scenario].get_var_soln(rate),
                                                        epi_outputs['infections' + strain])

                # annual risk of infection (as a percentage)
                epi_outputs['annual_risk_infection' + strain] \
                    = elementwise_list_percentage(epi_outputs['infections' + strain], total_denominator)

        ''' stratified outputs (currently not repeated for each strain) '''

        for stratification in strata:
            if len(stratification) > 1:
                for stratum in stratification:

                    # initialise lists
                    for output in outputs_to_analyse: epi_outputs[output + stratum] = [0.] * len(epi_outputs['times'])

                    # population
                    for compartment in self.models[scenario].compartments:
                        if stratum in compartment:
                            epi_outputs['population' + stratum] \
                                = elementwise_list_addition(self.models[scenario].get_compartment_soln(compartment),
                                                            epi_outputs['population' + stratum])

                    # the population denominator to be used with zeros replaced with small numbers
                    stratum_denominator = tool_kit.prepare_denominator(epi_outputs['population' + stratum])

                    # incidence
                    if 'incidence' in outputs_to_analyse:
                        for from_label, to_label, rate in self.models[scenario].var_transfer_rate_flows:
                            if 'latent' in from_label and 'active' in to_label and stratum in from_label:
                                incidence_increment = self.models[scenario].get_compartment_soln(from_label) \
                                                      * self.models[scenario].get_var_soln(rate) \
                                                      / stratum_denominator * 1e5
                                epi_outputs['incidence' + stratum] \
                                    = elementwise_list_addition(incidence_increment, epi_outputs['incidence' + stratum])
                        for from_label, to_label, rate in self.models[scenario].fixed_transfer_rate_flows:
                            if 'latent' in from_label and 'active' in to_label and stratum in from_label:
                                incidence_increment = self.models[scenario].get_compartment_soln(from_label) \
                                                      * rate / stratum_denominator * 1e5
                                epi_outputs['incidence' + stratum] \
                                    = elementwise_list_addition(incidence_increment, epi_outputs['incidence' + stratum])

                    # notifications
                    if 'notifications' in outputs_to_analyse:
                        for strain in strains:
                            for from_label, to_label, rate in self.models[scenario].var_transfer_rate_flows:
                                if 'active' in from_label and 'detect' in to_label and strain in to_label \
                                        and stratum in from_label:
                                    notifications_increment \
                                        = self.models[scenario].get_compartment_soln(from_label) \
                                          * self.models[scenario].get_var_soln(rate)
                                    epi_outputs['notifications' + strain + stratum] \
                                        = elementwise_list_addition(
                                            notifications_increment, epi_outputs['notifications' + strain + stratum])

                    # mortality
                    if 'mortality' in outputs_to_analyse:

                        # fixed flows are outside of the health system and so the natural death contribution is reduced
                        for from_label, rate in self.models[scenario].fixed_infection_death_rate_flows:
                            if stratum in from_label:
                                mortality_increment = self.models[scenario].get_compartment_soln(from_label) \
                                                      * rate / stratum_denominator * 1e5
                                epi_outputs['true_mortality' + stratum] \
                                    = elementwise_list_addition(mortality_increment,
                                                                epi_outputs['true_mortality' + stratum])
                                epi_outputs['mortality' + stratum] \
                                    = elementwise_list_addition(
                                        mortality_increment
                                        * self.models[scenario].params['program_prop_death_reporting'],
                                        epi_outputs['mortality' + stratum])

                        # variable flows are within the health system and so dealt with as described above
                        for from_label, rate in self.models[scenario].var_infection_death_rate_flows:
                            if stratum in from_label:
                                mortality_increment = self.models[scenario].get_compartment_soln(from_label) \
                                                      * self.models[scenario].get_var_soln(rate) \
                                                      / stratum_denominator * 1e5
                                for mortality_type in ['true_mortality', 'mortality']:
                                    epi_outputs[mortality_type + stratum] \
                                        = elementwise_list_addition(mortality_increment,
                                                                    epi_outputs[mortality_type + stratum])

                    # prevalence
                    if 'prevalence' in outputs_to_analyse:
                        for label in self.models[scenario].labels:
                            if 'susceptible' not in label and 'latent' not in label and stratum in label:
                                prevalence_increment = self.models[scenario].get_compartment_soln(label) \
                                                       / stratum_denominator * 1e5
                                epi_outputs['prevalence' + stratum] \
                                    = elementwise_list_addition(prevalence_increment,
                                                                epi_outputs['prevalence' + stratum])

                    # infections (absolute number)
                    if 'infections' in outputs_to_analyse:
                        for from_label, to_label, rate in self.models[scenario].var_transfer_rate_flows:
                            if 'latent_early' in to_label and stratum in from_label:
                                epi_outputs['infections' + stratum] \
                                    = elementwise_list_addition(
                                        self.models[scenario].get_compartment_soln(from_label)
                                        * self.models[scenario].get_var_soln(rate),
                                        epi_outputs['infections' + stratum])

                        # annual risk of infection (as a percentage)
                        epi_outputs['annual_risk_infection' + stratum] \
                            = elementwise_list_percentage(epi_outputs['infections' + stratum], stratum_denominator)

        return epi_outputs

    def find_population_fractions(self, scenario, strata=[]):
        """
        Find the proportion of the population in various strata. The stratifications must apply to the entire
        population, so this method should not be used for strains, health systems, etc.
        """

        for stratification in strata:
            if len(stratification) > 1:
                for stratum in stratification:
                    self.epi_outputs[scenario]['fraction' + stratum] \
                        = elementwise_list_division(self.epi_outputs[scenario]['population' + stratum],
                                                    self.epi_outputs[scenario]['population'])

    def find_cost_outputs(self, scenario):
        """
        Master method to call methods to find and update costs below.

        Args:
            scenario: Number of the name of the model being costed
        """

        self.cost_outputs[scenario] = self.find_raw_cost_outputs(scenario)
        self.cost_outputs[scenario]['raw_cost_all_programs'] = self.find_costs_all_programs(scenario)
        self.cost_outputs[scenario].update(self.find_adjusted_costs(scenario))

    def find_raw_cost_outputs(self, scenario):
        """
        Find cost dictionaries to add to cost_outputs attribute.
        """

        cost_outputs = {'times': self.models[scenario].cost_times}
        for i, intervention in enumerate(self.interventions_to_cost[scenario]):
            cost_outputs['raw_cost_' + intervention] = self.models[scenario].costs[:, i]
        return cost_outputs

    def find_costs_all_programs(self, scenario):
        """
        Sum costs across all programs and populate to cost_outputs dictionary for each scenario.
        """

        costs_all_programs \
            = [0.] * len(self.cost_outputs[scenario]['raw_cost_' + self.interventions_to_cost[scenario][0]])
        for intervention in self.interventions_to_cost[scenario]:
            costs_all_programs \
                = elementwise_list_addition(self.cost_outputs[scenario]['raw_cost_' + intervention], costs_all_programs)
        return costs_all_programs

    def find_adjusted_costs(self, scenario):
        """
        Find costs adjusted for inflation, discounting and both.

        Args:
            scenario: Scenario being costed
        """

        # get some preliminary parameters
        year_current = self.inputs.model_constants['recent_time']
        current_cpi = self.inputs.scaleup_fns[0]['econ_cpi'](year_current)
        discount_rate = self.inputs.model_constants['econ_discount_rate']

        # loop over interventions for costing and cost types
        cost_outputs = {}
        for intervention in self.interventions_to_cost[scenario] + ['all_programs']:
            for cost_type in self.additional_cost_types:
                cost_outputs[cost_type + '_cost_' + intervention] = []
                for t, time in enumerate(self.cost_outputs[scenario]['times']):
                    cost_outputs[cost_type + '_cost_' + intervention].append(
                        autumn.economics.get_adjusted_cost(
                            self.cost_outputs[scenario]['raw_cost_' + intervention][t], cost_type, current_cpi,
                            self.inputs.scaleup_fns[0]['econ_cpi'](time), discount_rate,
                            max(0., (time - year_current))))
        return cost_outputs

    ''' epidemiological uncertainty methods '''

    def run_epi_uncertainty(self):
        """
        Main method to run all the uncertainty processes using a Metropolis-Hastings algorithm with normal proposal
        distribution.
        """

        self.add_comment_to_gui_window('Uncertainty analysis commenced')

        # prepare parameters and other basic variables for uncertainty loop
        n_accepted, prev_log_likelihood, new_param_list, param_candidates = 0, -5e2, [], {}
        for param in self.inputs.param_ranges_unc:
            param_candidates[param['key']] = [self.inputs.model_constants[param['key']]]
            self.all_parameters_tried[param['key']] = []
            self.acceptance_dict[param['key']] = {}
            self.rejection_dict[param['key']] = {n_accepted: []}
            new_param_list.append(param_candidates[param['key']][0])
            params = new_param_list
        for compartment_type in self.inputs.compartment_types:
            if compartment_type in self.inputs.model_constants: self.all_compartment_values_tried[compartment_type] = []
        self.all_other_adjustments_made['program_prop_death_reporting'] = []

        # find weights for outputs that are being calibrated to
        years_to_compare = range(1990, 2015)
        weights = find_uncertainty_output_weights(years_to_compare, 1, [1., 2.])
        self.add_comment_to_gui_window('"Weights": \n' + str(weights))

        # instantiate uncertainty model objects
        for scenario in self.scenarios:
            self.models[scenario] = model.ConsolidatedModel(scenario, self.inputs, self.gui_inputs)

        run, population_adjustment, accepted = 0, 1., 0

        while n_accepted < self.gui_inputs['uncertainty_runs']:

            # set timer
            start_timer_run = datetime.datetime.now()

            # run baseline scenario (includes parameter checking, parameter setting and recording success/failure)
            self.run_with_params(
                new_param_list, scenario=0, population_adjustment=population_adjustment, accepted=accepted)

            # store outputs regardless of acceptance, provided run was completed successfully
            if self.is_last_run_success:

                # get outputs for calibration and store results
                self.store_uncertainty(0, epi_outputs_to_analyse=self.epi_outputs_to_analyse)
                outputs_for_comparison \
                    = [self.epi_outputs[0]['incidence'][tool_kit.find_first_list_element_at_least_value(
                        self.epi_outputs[0]['times'], float(year))] for year in years_to_compare]

                # calculate prior
                prior_log_likelihood = 0.
                for p, param in enumerate(self.inputs.param_ranges_unc):
                    param_val = new_param_list[p]
                    self.all_parameters_tried[param['key']].append(new_param_list[p])
                    if 'additional_params' not in param: param['additional_params'] = None
                    prior_log_likelihood \
                        += find_log_probability_density(param['distribution'], param_val,  param['bounds'],
                                                        additional_params=param['additional_params'])

                # calculate posterior
                posterior_log_likelihood = 0.
                for output_dict in self.outputs_unc:

                    # the GTB values for the output of interest
                    working_output_dictionary = self.get_fitting_data()[output_dict['key']]
                    for y, year in enumerate(years_to_compare):
                        if year in working_output_dictionary.keys():
                            model_result_for_output = outputs_for_comparison[y]
                            mu, sd = working_output_dictionary[year][0], working_output_dictionary[year][1]
                            posterior_log_likelihood += norm.logpdf(model_result_for_output, mu, sd) * weights[y]

                # determine acceptance
                log_likelihood = prior_log_likelihood + posterior_log_likelihood
                accepted = numpy.random.binomial(n=1, p=min(1., numpy.exp(log_likelihood - prev_log_likelihood)))

                # describe progression of likelihood analysis
                self.add_comment_to_gui_window(
                    'Previous log likelihood:\n%4.3f\nLog likelihood this run:\n%4.3f\nAcceptance probability:\n%4.3f'
                    % (log_likelihood, prev_log_likelihood, min(1., numpy.exp(log_likelihood - prev_log_likelihood)))
                    + '\nWhether accepted:\n%s\n________________\n' % str(bool(accepted)))
                self.loglikelihoods.append(log_likelihood)

                # record starting population
                if self.gui_inputs['write_uncertainty_outcome_params']:
                    for compartment_type in self.all_compartment_values_tried:
                        self.all_compartment_values_tried[compartment_type].append(
                            self.inputs.model_constants[compartment_type])

                # record uncertainty calculations for all runs
                if accepted:
                    self.whether_accepted_list.append(True)
                    self.accepted_indices.append(run)
                    n_accepted += 1
                    for p, param in enumerate(self.inputs.param_ranges_unc):
                        self.acceptance_dict[param['key']][n_accepted] = new_param_list[p]
                        self.rejection_dict[param['key']][n_accepted] = []

                    # update likelihood and parameter set for next run
                    prev_log_likelihood = log_likelihood
                    params = new_param_list

                    # run scenarios other than baseline and store uncertainty (only if accepted)
                    for scenario in self.scenarios:
                        if scenario:
                            self.prepare_new_model_from_baseline(scenario)
                            self.run_with_params(new_param_list, scenario=scenario)
                            self.store_uncertainty(scenario, epi_outputs_to_analyse=self.epi_outputs_to_analyse)

                    # iteratively adjusting proportion of mortality reported
                    ratios = []
                    for year in years_to_compare:
                        if year in self.inputs.original_data['tb']['e_mort_exc_tbhiv_100k']:
                            ratios.append(self.epi_outputs[0]['mortality'][
                                             tool_kit.find_first_list_element_above_value(self.epi_outputs[0]['times'],
                                                                                          float(year))]
                                         / self.inputs.original_data['tb']['e_mort_exc_tbhiv_100k'][year])
                    average_ratio = numpy.mean(ratios)
                    if average_ratio < 1. / self.relative_difference_to_adjust_mortality:
                        self.inputs.model_constants['program_prop_death_reporting'] += self.amount_to_adjust_mortality
                    elif average_ratio > self.relative_difference_to_adjust_mortality:
                        self.inputs.model_constants['program_prop_death_reporting'] -= self.amount_to_adjust_mortality

                else:
                    self.whether_accepted_list.append(False)
                    self.rejected_indices.append(run)
                    for p, param in enumerate(self.inputs.param_ranges_unc):
                        self.rejection_dict[param['key']][n_accepted].append(new_param_list[p])

                # plot parameter progression and report on progress
                self.plot_progressive_parameters()
                self.add_comment_to_gui_window(
                    str(n_accepted) + ' accepted / ' + str(run) + ' candidates. Running time: '
                    + str(datetime.datetime.now() - start_timer_run))

                # find value to adjust starting population by, if a target population specified
                if 'target_population' in self.inputs.model_constants:
                    population_adjustment \
                        = self.inputs.model_constants['target_population'] \
                          / self.epi_outputs[0]['population'][tool_kit.find_first_list_element_above_value(
                                self.epi_outputs[0]['times'], self.inputs.model_constants['current_time'])]

                # record death reporting proportion, which may or may not have been adjusted
                self.all_other_adjustments_made['program_prop_death_reporting'].append(
                    self.inputs.model_constants['program_prop_death_reporting'])

                run += 1

            new_param_list = self.update_params(params)

    def get_fitting_data(self):
        """
        Define the characteristics (mean and standard deviation) of the normal distribution for model outputs
        (incidence, mortality).

        Returns:
            normal_char: Dictionary with keys outputs and values dictionaries. Sub-dictionaries have keys years
                and values lists, with first element of list means and second standard deviations.
        """

        # dictionary storing the characteristics of the normal distributions
        normal_char = {}
        for output_dict in self.inputs.outputs_unc:
            normal_char[output_dict['key']] = {}

            # incidence
            if output_dict['key'] == 'incidence':
                for year in self.inputs.data_to_fit[output_dict['key']].keys():
                    low = self.inputs.data_to_fit['incidence_low'][year]
                    high = self.inputs.data_to_fit['incidence_high'][year]
                    sd = output_dict['width_multiplier'] * (high - low) / (2. * 1.96)
                    mu = (high + low) / 2.
                    normal_char[output_dict['key']][year] = [mu, sd]

            # mortality
            elif output_dict['key'] == 'mortality':
                sd = output_dict['posterior_width'] / (2. * 1.96)
                for year in self.inputs.data_to_fit[output_dict['key']].keys():
                    mu = self.inputs.data_to_fit[output_dict['key']][year]
                    normal_char[output_dict['key']][year] = [mu, sd]

        return normal_char

    def run_with_params(self, params, scenario=0, population_adjustment=1., accepted=0):
        """
        Integrate the model with the proposed parameter set.

        Args:
            params: The parameters to be set in the model.
        """

        # check whether parameter values are acceptable
        for p, param in enumerate(params):

            # whether the parameter value is valid
            if not is_parameter_value_valid(param):
                print 'Warning: parameter%d=%f is invalid for model' % (p, param)
                self.is_last_run_success = False
                return

            # whether the parameter value is within acceptable ranges
            bounds = self.inputs.param_ranges_unc[p]['bounds']
            if param < bounds[0] or param > bounds[1]:
                print 'Warning: parameter%d=%f is outside of the allowed bounds' % (p, param)
                self.is_last_run_success = False
                return

        param_dict = {names['key']: vals for names, vals in zip(self.inputs.param_ranges_unc, params)}

        # set parameters and run
        self.set_model_with_params(param_dict, scenario, population_adjustment=population_adjustment,
                                   accepted=accepted)
        self.is_last_run_success = True
        try:
            self.models[scenario].integrate()
        except:
            print 'Warning: parameters=%s failed with model' % params
            self.is_last_run_success = False

    def set_model_with_params(self, param_dict, scenario=0, population_adjustment=1., accepted=0):
        """
        Populates baseline model with params from uncertainty calculations, including adjusting starting time.
        Also adjusts starting population to better match target population at current time using target_population input
        from country sheet. (Not currently in default sheet.)

        Args:
            param_dict: Dictionary of the parameters to be set within the model (keys parameter name strings and values
                parameter values)
        """

        # adjust starting populations if target_population in sheets (i.e. country sheet, because not in defaults)
        if accepted and population_adjustment != 1.:
            for compartment_type in self.inputs.compartment_types:
                if compartment_type in self.inputs.model_constants:
                    self.inputs.model_constants[compartment_type] *= population_adjustment

        for key in param_dict:

            # start time usually set in instantiation, which has already been done here, so needs to be set separately
            if key == 'start_time':
                self.models[scenario].start_time = param_dict[key]

            # set parameters
            elif key in self.models[scenario].params:
                self.models[scenario].set_parameter(key, param_dict[key])
            else:
                raise ValueError('%s not in model_object params' % key)

    def store_uncertainty(self, scenario, epi_outputs_to_analyse):
        """
        Add model results from one uncertainty run to the appropriate outputs dictionary, vertically stacking
        results on to the previous matrix.

        Args:
            scenario: The scenario being run
            epi_outputs_to_analyse: The epidemiological outputs of interest
        Updates:
            self.epi_outputs_uncertainty
            self.cost_outputs_uncertainty
        """

        # get outputs
        self.epi_outputs[scenario] = self.find_epi_outputs(scenario, outputs_to_analyse=self.epi_outputs_to_analyse)
        if self.models[scenario].interventions_to_cost: self.find_cost_outputs(scenario)

        # initialise dictionaries if necessary
        if scenario not in self.epi_outputs_uncertainty:
            self.epi_outputs_uncertainty[scenario] = {'times': self.epi_outputs[scenario]['times']}
            self.cost_outputs_uncertainty[scenario] = {'times': self.cost_outputs[scenario]['times']}
            for output in epi_outputs_to_analyse:
                self.epi_outputs_uncertainty[scenario][output] \
                    = numpy.empty(shape=[0, len(self.epi_outputs[scenario]['times'])])
            for output in self.cost_outputs[scenario]:
                self.cost_outputs_uncertainty[scenario][output] \
                    = numpy.empty(shape=[0, len(self.cost_outputs[scenario]['times'])])

        # add uncertainty data to dictionaries
        for output in epi_outputs_to_analyse:
            new_output = tool_kit.force_list_to_length(self.epi_outputs[scenario][output],
                                                       int(self.epi_outputs_uncertainty[scenario][output].shape[1]))
            self.epi_outputs_uncertainty[scenario][output] \
                = numpy.vstack([self.epi_outputs_uncertainty[scenario][output], new_output])
        for output in self.cost_outputs[scenario]:
            self.cost_outputs_uncertainty[scenario][output] \
                = numpy.vstack([self.cost_outputs_uncertainty[scenario][output],
                                self.cost_outputs[scenario][output]])

    def update_params(self, old_params):
        """
        Update all the parameter values being used in the uncertainty analysis.

        Args:
            old_params:
        Returns:
            new_params: The new parameters to be used in the next model run.
        """

        new_params = []

        # iterate through the parameters being used
        for p, param_dict in enumerate(self.inputs.param_ranges_unc):
            bounds = param_dict['bounds']
            sd = self.gui_inputs['search_width'] * (bounds[1] - bounds[0]) / (2. * 1.96)
            random = -100.

            # search for new parameters
            while random < bounds[0] or random > bounds[1]: random = norm.rvs(loc=old_params[p], scale=sd, size=1)

            # add them to the dictionary
            new_params.append(random[0])

        return new_params

    ''' other run type methods '''

    def run_intervention_uncertainty(self):
        """
        Master method for running intervention uncertainty. That is, starting from the calibrated baseline simulated,
        project forward scenarios based on varying parameters for the effectiveness of the intervention under
        consideration.
        """

        # extract relevant intervention parameters from the intervention uncertainty dictionary
        working_param_dict = {}
        for param in self.inputs.intervention_param_dict[self.inputs.uncertainty_intervention]:
            for int_param in range(len(self.inputs.int_ranges_unc)):
                if self.inputs.int_ranges_unc[int_param]['key'] \
                        in self.inputs.intervention_param_dict[self.inputs.uncertainty_intervention]:
                    working_param_dict[param] = self.inputs.int_ranges_unc[int_param]

        # generate samples using latin hypercube design
        sample_values = lhs(len(working_param_dict), samples=self.inputs.n_samples)
        parameter_values = {}
        for p, param in enumerate(working_param_dict):
            parameter_values[param] = []
            for sample in range(self.inputs.n_samples):
                parameter_values[param].append(
                    working_param_dict[param]['bounds'][0]
                    + (working_param_dict[param]['bounds'][1] - working_param_dict[param]['bounds'][0])
                    * sample_values[sample][p])

        # loop through parameter values
        for sample in range(self.inputs.n_samples):

            # prepare for integration of scenario
            self.models[15] = model.ConsolidatedModel(15, self.inputs, self.gui_inputs)
            self.prepare_new_model_from_baseline(0, 15)
            self.models[15].relevant_interventions.append(self.inputs.uncertainty_intervention)
            for param in parameter_values:
                self.models[15].set_parameter(param, parameter_values[param][sample])

            # integrate and save
            self.models[15].integrate()
            self.store_uncertainty(15, epi_outputs_to_analyse=self.epi_outputs_to_analyse)

    ''' optimisation methods '''

    def run_optimisation(self):
        """
        Master optimisation method for the different levels of funding defined in self.annual_envelope
        """

        # initialise the optimisation output data structures
        standard_optimisation_attributes = ['best_allocation', 'incidence', 'mortality']
        self.opti_results['indicator_to_minimise'] = self.indicator_to_minimise
        self.opti_results['annual_envelope'] = self.annual_envelope
        for attribute in standard_optimisation_attributes:
            self.opti_results[attribute] = []

        # run optimisation for each envelope
        for envelope in self.annual_envelope:
            self.add_comment_to_gui_window('Start optimisation for annual total envelope of: ' + str(envelope))
            self.total_funding = envelope * (self.inputs.model_constants['scenario_end_time']
                                             - self.inputs.model_constants['scenario_start_time'])
            self.optimise_single_envelope()
            full_results = self.get_full_results_opti()
            for attribute in standard_optimisation_attributes:
                self.opti_results[attribute].append(full_results[attribute])

    def get_acceptable_combinations(self):
        """
        Determines the acceptable combinations of interventions according to the related starting costs and given a
        total amount of funding populates the acceptable_combinations attribute of model_runner.
        """

        # find all possible combinations of the considered interventions
        all_possible_combinations \
            = list(itertools.chain.from_iterable(
            itertools.combinations(range(len(self.interventions_considered_for_opti)), n) for n in
            range(len(self.interventions_considered_for_opti) + 1)[1:]))

        # determine whether each combination is fund-able given start-up costs
        fundable_combinations = []
        for combination in all_possible_combinations:
            total_startup_costs = 0.
            for intervention in combination:
                if self.inputs.intervention_startdates[0][self.interventions_considered_for_opti[intervention]] is 0:
                    total_startup_costs \
                        += self.inputs.model_constants['econ_startupcost_' +
                                                       self.interventions_considered_for_opti[intervention]]
            if total_startup_costs <= self.total_funding:
                fundable_combinations.append(combination)

        # determine whether a forced intervention is missing from each fund-able intervention
        combinations_missing_a_forced_intervention = []
        for c, combination in enumerate(fundable_combinations):
            for intervention in self.interventions_forced_for_opti:
                if self.interventions_considered_for_opti.index(intervention) not in combination \
                        and combination not in combinations_missing_a_forced_intervention:
                    combinations_missing_a_forced_intervention.append(combination)

        # populate final list of acceptable combinations
        acceptable_combinations = []
        for combination in fundable_combinations:
            if combination not in combinations_missing_a_forced_intervention:
                acceptable_combinations.append(combination)
        self.acceptable_combinations = acceptable_combinations
        self.add_comment_to_gui_window('Number of combinations to consider: ' + str(len(self.acceptable_combinations)))

    def optimise_single_envelope(self):
        """
        Method to fully run optimisation for a single funding envelope.
        """

        start_timer_opti = datetime.datetime.now()
        self.optimised_combinations = []

        # initialise a new model that will be run from recent_time and set basic attributes for optimisation
        self.models['optimisation'] = model.ConsolidatedModel(0, self.inputs, self.gui_inputs)
        self.prepare_new_model_from_baseline('manual', 'optimisation')
        self.models['optimisation'].eco_drives_epi = True
        self.models['optimisation'].inputs.model_constants['scenario_end_time'] = self.year_end_opti
        self.models['optimisation'].interventions_considered_for_opti = self.interventions_considered_for_opti

        # find the combinations of interventions to be optimised
        self.get_acceptable_combinations()

        # for each acceptable combination of interventions
        for c, combination in enumerate(self.acceptable_combinations):

            # prepare storage
            dict_optimised_combi = {'interventions': [], 'distribution': [], 'objective': None}

            for i in range(len(combination)):
                intervention = self.interventions_considered_for_opti[combination[i]]
                dict_optimised_combi['interventions'].append(intervention)

            print('Optimisation of the distribution across: ')
            print(dict_optimised_combi['interventions'])

            # function to minimise: incidence in 2035
            def minimisation_function(x):

                """
                Args:
                    x: defines the resource allocation (as absolute funding over the total period (2015 - 2035))
                Returns:
                    x has same length as combination
                    predicted incidence for 2035
                """

                # initialise funding at zero for each intervention
                for intervention in self.interventions_considered_for_opti:
                    self.models['optimisation'].available_funding[intervention] = 0.

                # input values from x
                for i in range(len(x)):
                    intervention = self.interventions_considered_for_opti[combination[i]]
                    self.models['optimisation'].available_funding[intervention] = x[i] * self.total_funding
                self.models['optimisation'].distribute_funding_across_years()
                self.models['optimisation'].integrate()
                output_list = self.find_epi_outputs('optimisation',
                                                    outputs_to_analyse=['incidence', 'mortality', 'true_mortality'])
                return output_list[self.indicator_to_minimise][-1]

            # if only one intervention, the distribution is obvious
            if len(combination) == 1:
                dict_optimised_combi['distribution'] = [1.]
                dict_optimised_combi['objective'] = minimisation_function([1.])

            # otherwise
            else:

                # initial guess
                starting_distribution = []
                for i in range(len(combination)):
                    starting_distribution.append(1. / len(combination))

                # equality constraint is that the sum of the proportions has to be equal to one
                sum_to_one_constraint = [{'type': 'ineq',
                                          'fun': lambda x: 1. - sum(x),
                                          'jac': lambda x: -numpy.ones(len(x))}]
                cost_bounds = []
                for i in range(len(combination)):
                    minimal_allocation = 0.

                    # if start-up costs apply
                    if self.inputs.intervention_startdates[0][
                        self.models['manual_baseline'].interventions_to_cost[combination[i]]] is None:
                        minimal_allocation \
                            = self.models['manual_baseline'].inputs.model_constants[
                                  'econ_startupcost_'
                                  + self.models['manual_baseline'].interventions_to_cost[combination[i]]] \
                              / self.total_funding
                    cost_bounds.append((minimal_allocation, 1.))

                # ready to run optimisation
                optimisation_result \
                    = minimize(minimisation_function, starting_distribution, jac=None, bounds=cost_bounds,
                               constraints=sum_to_one_constraint, method='SLSQP',
                               options={'disp': False, 'ftol': self.f_tol[self.indicator_to_minimise]})
                dict_optimised_combi['distribution'] = optimisation_result.x
                dict_optimised_combi['objective'] = optimisation_result.fun

            self.optimised_combinations.append(dict_optimised_combi)
            self.add_comment_to_gui_window('Combination ' + str(c + 1) + '/' + str(len(self.acceptable_combinations))
                                           + ' completed.')

        # update optimal allocation
        self.optimal_allocation = {}
        best_dict = {}
        best_obj = 1e10
        for i, dict_opti in enumerate(self.optimised_combinations):
            if dict_opti['objective'] < best_obj:
                best_dict = dict_opti
                best_obj = dict_opti['objective']

        for intervention in self.interventions_considered_for_opti:
            self.optimal_allocation[intervention] = 0.
        for i, intervention in enumerate(best_dict['interventions']):
            self.optimal_allocation[intervention] = best_dict['distribution'][i]

        self.add_comment_to_gui_window('End optimisation after ' + str(datetime.datetime.now() - start_timer_opti))

    def get_full_results_opti(self):
        """
        We need to run the best allocation scenario until 2035 to obtain the final incidence and mortality.
        """

        # prepare new model to run full scenario duration
        self.models['optimisation'] = model.ConsolidatedModel(0, self.inputs, self.gui_inputs)
        self.prepare_new_model_from_baseline('manual', 'optimisation')
        self.models['optimisation'].eco_drives_epi = True
        self.models['optimisation'].interventions_considered_for_opti = self.interventions_considered_for_opti

        # initialise funding at zero for each intervention
        for intervention in self.interventions_considered_for_opti:
            self.models['optimisation'].available_funding[intervention] = 0.

        # distribute funding and integrate
        for intervention, prop in self.optimal_allocation.iteritems():
            self.models['optimisation'].available_funding[intervention] = prop * self.total_funding
        self.models['optimisation'].distribute_funding_across_years()
        self.models['optimisation'].integrate()

        # find epi results
        output_list = self.find_epi_outputs('optimisation',
                                            outputs_to_analyse=['incidence', 'mortality', 'true_mortality'])
        del self.models['optimisation']
        return {'best_allocation': self.optimal_allocation, 'incidence': output_list['incidence'][-1],
                'mortality': output_list['mortality'][-1]}

    def load_opti_results(self):
        """
        Load optimisation results if attribute to self is True.
        """

        if self.load_optimisation:
            storage_file_name = os.path.join(self.opti_outputs_dir, 'opti_outputs.pkl')
            self.opti_results = tool_kit.pickle_load(storage_file_name)
            self.add_comment_to_gui_window('Optimisation results loaded')

    def save_opti_results(self):
        """
        Save optimisation results, which is expected to be the usual behaviour for the model runner.
        """

        # save only if optimisation has been run and save requested
        if self.save_opti and self.optimisation:
            filename = os.path.join(self.opti_outputs_dir, 'opti_outputs.pkl')
            tool_kit.pickle_save(self.opti_results, filename)
            self.add_comment_to_gui_window('Optimisation results saved')

    ''' GUI-related methods '''

    def add_comment_to_gui_window(self, comment):

        if self.js_gui:
            self.js_gui('console', { "message": comment })

    def plot_progressive_parameters(self):
        """
        Produce real-time parameter plot, according to which GUI is in use.
        """

        if self.js_gui:
            self.js_gui('graph', {
                "all_parameters_tried": self.all_parameters_tried,
                "whether_accepted_list": self.whether_accepted_list,
                "rejection_dict": self.rejection_dict,
                "accepted_indices": self.accepted_indices,
                "acceptance_dict": self.acceptance_dict,
                "names": {
                    param: tool_kit.find_title_from_dictionary(param)
                    for p, param in enumerate(self.all_parameters_tried)
                },
                "param_ranges_unc": self.inputs.param_ranges_unc
            })




