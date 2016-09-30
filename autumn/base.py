import os

import numpy
from scipy.integrate import odeint
import tool_kit
from autumn.economics import get_cost_from_coverage, inflate_cost, discount_cost
import scipy.stats


class BaseModel:

    def __init__(self):

        self.labels = []
        self.init_compartments = {}
        self.params = {}
        self.times = None

        self.scaleup_fns = {}
        self.vars = {}

        self.soln_array = None
        self.var_labels = None
        self.var_array = None
        self.flow_array = None
        self.fraction_array = None

        self.is_additional_diagnostics = False

        self.flows = {}
        self.fixed_transfer_rate_flows = []
        self.linked_transfer_rate_flows = []
        self.fixed_infection_death_rate_flows = []
        self.var_transfer_rate_flows = []
        self.var_flows = []
        self.var_infection_death_rate_flows = []

        self.costs = {}
        self.run_costing = True
        self.end_period_costing = 2035
        self.interventions_to_cost = ['vaccination', 'xpert', 'treatment_support', 'smearacf', 'xpertacf',
                                      'ipt_age0to5', 'ipt_age5to15', 'decentralisation']

        self.eco_drives_epi = False

        self.startups_apply = {}
        self.intervention_startdates = {}

    def make_times(self, start, end, delta):

        "Return steps between start and end every delta"

        self.times = []
        step = start
        while step <= end:
            self.times.append(step)
            step += delta
        if self.times[-1] < end:
            self.times.append(end)

    def make_times_with_n_step(self, start, end, n):
        "Return steps between start and in n increments"
        self.times = []
        step = start
        delta = (end - start) / float(n)
        while step <= end:
            self.times.append(step)
            step += delta
        if self.times[-1] < end:
            self.times.append(end)

    def find_time_index(self, time):

        for index, model_time in enumerate(self.times):
            if model_time > time:
                return index

        raise ValueError('Time not found')

    def set_compartment(self, label, init_val=0.0):
        if label not in self.labels:
            self.labels.append(label)
        self.init_compartments[label] = init_val
        assert init_val >= 0, 'Start with negative compartment not permitted'

    def set_parameter(self, label, val):
        self.params[label] = val

    def convert_list_to_compartments(self, vec):
        return {l: vec[i] for i, l in enumerate(self.labels)}

    def convert_compartments_to_list(self, compartments):
        return [compartments[l] for l in self.labels]

    def get_init_list(self):

        if self.loaded_compartments is None:
            return self.convert_compartments_to_list(self.init_compartments)
        else:
            return self.convert_compartments_to_list(self.loaded_compartments)

    def set_population_death_rate(self, death_label):

        # Currently inactive (although Bosco might not be pleased about this)
        self.death_rate = self.params[death_label]

    def set_fixed_infection_death_rate_flow(self, label, param_label):
        add_unique_tuple_to_list(
            self.fixed_infection_death_rate_flows,
            (label, self.params[param_label]))

    def set_var_infection_death_rate_flow(self, label, vars_label):
        add_unique_tuple_to_list(
            self.var_infection_death_rate_flows,
            (label, vars_label))

    def set_fixed_transfer_rate_flow(self, from_label, to_label, param_label):
        add_unique_tuple_to_list(
            self.fixed_transfer_rate_flows,
            (from_label, to_label, self.params[param_label]))

    def set_linked_transfer_rate_flow(self, from_label, to_label, vars_label):
        add_unique_tuple_to_list(
            self.linked_transfer_rate_flows,
            (from_label, to_label, vars_label))

    def set_var_transfer_rate_flow(self, from_label, to_label, vars_label):
        add_unique_tuple_to_list(
            self.var_transfer_rate_flows,
            (from_label, to_label, vars_label))

    def set_scaleup_fn(self, label, fn):
        self.scaleup_fns[label] = fn

    def set_var_entry_rate_flow(self, label, vars_label):
        add_unique_tuple_to_list(
            self.var_flows,
            (label, vars_label))

    def calculate_vars_of_scaleup_fns(self):
        for label, fn in self.scaleup_fns.iteritems():
            self.vars[label] = fn(self.time)

    def calculate_vars(self):
        """
        Calculate self.vars that only depend on compartment values
        """
        pass

    def calculate_flows(self):
        """
        Calculate flows, which should only depend on compartment values
        and self.vars calculated in calculate_variable_rates.
        """
        for label in self.labels:
            self.flows[label] = 0.0

        # birth flows
        for label, vars_label in self.var_flows:
            self.flows[label] += self.vars[vars_label]

        # dynamic transmission flows
        for from_label, to_label, vars_label in self.var_transfer_rate_flows:
            val = self.compartments[from_label] * self.vars[vars_label]
            self.flows[from_label] -= val
            self.flows[to_label] += val

        # fixed-rate flows
        for from_label, to_label, rate in self.fixed_transfer_rate_flows:
            val = self.compartments[from_label] * rate
            self.flows[from_label] -= val
            self.flows[to_label] += val

        # linked flows
        for from_label, to_label, vars_label in self.linked_transfer_rate_flows:
            val = self.vars[vars_label]
            self.flows[from_label] -= val
            self.flows[to_label] += val

        # normal death flows
        # This might be naughty - but now changed to access one of the parameters
        # (which has to have this name). Saves on creating a separate model attribute
        # just for population death. I think it makes more sense for it to be just
        # another parameter.
        # Now works if the death rate is selected to be constant or time-variant
        self.vars['rate_death'] = 0.
        for label in self.labels:
            if self.inputs.time_variants['demo_life_expectancy'][u'time_variant'] == u'no':
                val = self.compartments[label] / self.params['demo_life_expectancy']
            elif self.inputs.time_variants['demo_life_expectancy'][u'time_variant'] == u'yes':
                val = self.compartments[label] / self.vars['demo_life_expectancy']
            self.flows[label] -= val
            self.vars['rate_death'] += val

        # extra death flows
        self.vars['rate_infection_death'] = 0.
        for label, rate in self.fixed_infection_death_rate_flows:
            val = self.compartments[label] * rate
            self.flows[label] -= val
            self.vars['rate_infection_death'] += val
        for label, rate in self.var_infection_death_rate_flows:
            val = self.compartments[label] * self.vars[vars_label]
            self.flows[label] -= val
            self.vars['rate_infection_death'] += val

    def prepare_vars_flows(self):

        # This function collects some other functions that
        # previously led to a bug because not all of them
        # were called in the diagnostics round.
        # (Written by James, not Bosco)

        # Before clearing vars, we need to save the ones that are population sizes as its needed for the economics
        saved_vars = {}
        if self.eco_drives_epi:
            for key in self.vars.keys():
                if 'popsize' in key:
                    saved_vars[key] = self.vars[key]

        self.vars.clear() # clear all the vars
        self.vars = saved_vars # re-populate the saved vars
        self.calculate_vars_of_scaleup_fns()
        self.calculate_vars()
        self.calculate_flows()

    def make_derivate_fn(self):

        def derivative_fn(y, t):
            self.time = t
            self.compartments = self.convert_list_to_compartments(y)
            self.prepare_vars_flows()
            flow_vector = self.convert_compartments_to_list(self.flows)
            self.checks()
            return flow_vector

        return derivative_fn

    def init_run(self):

        self.make_times(self.start_time,
                        self.inputs.model_constants['scenario_end_time'],
                        self.gui_inputs['time_step'])
        self.initialise_compartments()
        self.set_flows()
        self.var_labels = None
        self.soln_array = None
        self.var_array = None
        self.flow_array = None
        self.fraction_array = None
        assert not self.times is None, 'Times have not been set yet'

    def integrate_scipy(self, dt_max=0.05):

        """ Uses Adams method coded in the LSODA Fortran package. This method is programmed to "slow down" when a tricky
        point is encountered. Then we need to allow for a high maximal number of iterations (mxstep)so that the
        algorithm does not get stuck.
        Input:
            min_dt: represents the time step for calculation points. The attribute self.times will also be used to make sure
            that a solution is affected to the time points known by the model
        """
        self.init_run()
        init_y = self.get_init_list()
        derivative = self.make_derivate_fn()

        tt = [] # all the calculation times
        tt_record = [] # store the indices of tt corresponding to the calculation times to be stored

        time = self.times[0]
        tt.append(time)
        tt_record.append(0)
        i_tt = 0
        for i_time, new_time in enumerate(self.times):
            while time < new_time:
                time = time + dt_max
                if time > new_time:
                    time = new_time
                i_tt += 1
                tt.append(time)
                if time == new_time:
                    tt_record.append(i_tt)

        sol = odeint(derivative, init_y, tt, mxstep=5000000)
        self.soln_array = sol[tt_record, :]

        self.calculate_diagnostics()
        if self.run_costing:
            self.calculate_economics_diagnostics(self.end_period_costing)

    def integrate_explicit(self, dt_max=0.05):

        """ Uses Euler Explicit method.
            Input:
            min_dt: represents the time step for calculation points. The attribute self.times will also be used to make sure
            that a solution is affected to the time points known by the model
        """
        self.init_run()
        y = self.get_init_list()
        y_candidate = numpy.zeros((len(y)))
        n_compartment = len(y)
        n_time = len(self.times)
        self.soln_array = numpy.zeros((n_time, n_compartment))

        derivative = self.make_derivate_fn()
        old_time = self.times[0]
        time = old_time
        self.soln_array[0, :] = y
        dt_is_ok = True
        for i_time, new_time in enumerate(self.times):
            while time < new_time:
                if not dt_is_ok:
                    adaptive_dt_max = dt / 2.0
                else:
                    adaptive_dt_max = dt_max
                    old_time = time
                dt_is_ok = True

                f = derivative(y, time)
                time = old_time + adaptive_dt_max
                dt = adaptive_dt_max
                if time > new_time:
                    dt = new_time - old_time
                    time = new_time

                for i in range(n_compartment):
                    y_candidate[i] = y[i] + dt * f[i]

                if (numpy.asarray(y_candidate) >= 0).all():
                    dt_is_ok = True
                    for i in range(n_compartment):
                        y[i] = y_candidate[i]
                else:
                    dt_is_ok = False


            if i_time < n_time - 1:
                self.soln_array[i_time+1, :] = y

        self.calculate_diagnostics()
        if self.run_costing:
            self.calculate_economics_diagnostics()

    def integrate_runge_kutta(self, dt_max=0.05):

        """
        Uses Runge-Kutta 4 method.

            Input:
                min_dt: represents the time step for calculation points. The attribute self.times will also be used to make
                sure that a solution is affected to the time points known by the model
        """

        self.init_run()
        y = self.get_init_list()
        n_compartment = len(y)
        n_time = len(self.times)
        self.soln_array = numpy.zeros((n_time, n_compartment))

        derivative = self.make_derivate_fn()
        old_time = self.times[0]
        time = self.times[0]
        self.soln_array[0, :] = y
        dt_is_ok = True
        for i_time, new_time in enumerate(self.times):
            while time < new_time:
                if not dt_is_ok:
                    adaptive_dt_max = dt/2.0
                else:
                    old_time = time
                    adaptive_dt_max = dt_max
                dt_is_ok = True
                #old_time = time
                time = old_time + adaptive_dt_max
                dt = adaptive_dt_max
                if time > new_time:
                    dt = new_time - old_time
                    time = new_time
                k1 = numpy.asarray(derivative(y, old_time))
                y_k2 = y + 0.5 * dt * k1
                if (y_k2 >= 0).all():
                    k2 = numpy.asarray(derivative(y_k2, old_time + 0.5*dt))
                else:
                    dt_is_ok = False
                    continue
                y_k3 = y + 0.5 * dt * k2
                if (y_k3 >= 0).all():
                    k3 = numpy.asarray(derivative(y_k3,  old_time + 0.5*dt))
                else:
                    dt_is_ok = False
                    continue
                y_k4 = y + dt*k3
                if (y_k4 >= 0).all():
                    k4 = numpy.asarray(derivative(y_k4, time))
                else:
                    dt_is_ok = False
                    continue

                y_candidate = []
                for i in range(n_compartment):
                    y_candidate.append(y[i] + (dt/6.0) * (k1[i] + 2.0*k2[i] + 2.0*k3[i] + k4[i]))

                if (numpy.asarray(y_candidate) >= 0).all():
                    y = y_candidate
                else:
                    dt_is_ok = False
                    continue


            if i_time < n_time - 1:
                self.soln_array[i_time + 1, :] = y

        self.calculate_diagnostics()
        if self.run_costing:
            self.calculate_economics_diagnostics()

    def calculate_output_vars(self):
        """
        Calculate diagnostic vars that can depend on self.flows as
        well as self.vars calculated in calculate_vars
        """
        pass

    def calculate_diagnostics(self):

        self.compartment_soln = {}
        for label in self.labels:
            if label in self.compartment_soln:
                continue
            self.compartment_soln[label] = self.get_compartment_soln(label)

        n_time = len(self.times)
        for i in range(n_time):

            self.time = self.times[i]

            for label in self.labels:
                self.compartments[label] = self.compartment_soln[label][i]

            self.prepare_vars_flows()
            self.calculate_output_vars()

            # only set after self.calculate_diagnostic_vars is
            # run so that we have all var_labels, including
            # the ones in calculate_diagnostic_vars
            if self.var_labels is None:
                self.var_labels = self.vars.keys()
                self.var_array = numpy.zeros((n_time, len(self.var_labels)))
                self.flow_array = numpy.zeros((n_time, len(self.labels)))

            for i_label, label in enumerate(self.var_labels):
                self.var_array[i, i_label] = self.vars[label]
            for i_label, label in enumerate(self.labels):
                self.flow_array[i, i_label] = self.flows[label]

        self.fraction_array = numpy.zeros((n_time, len(self.labels)))
        self.fraction_soln = {}
        for i_label, label in enumerate(self.labels):
            self.fraction_soln[label] = [
                v / t
                for v, t
                in zip(
                    self.compartment_soln[label],
                    self.get_var_soln('population'))]
            self.fraction_array[:, i_label] = self.fraction_soln[label]

    def coverage_over_time(self, param_key):

        """
        Define a function which returns the coverage over time associated with an intervention
        Args:
            model: model object, after integration
            param_key: the key of the parameter associated with the intervention

        Returns:
            a function which takes a time for argument an will return a coverage
        """

        coverage_function = self.scaleup_fns[param_key]
        return coverage_function

    def calculate_economics_diagnostics(self):

        """
        Run the economics diagnostics associated with a model run.
        Integration is supposed to have been completed by this point.

        """

        self.determine_whether_startups_apply()

        # If model is not age-structured, age-specific IPT does not make sense
        if len(self.agegroups) < 2:
            self.interventions_to_cost = [inter for inter in self.interventions_to_cost
                                          if inter not in ['ipt_age0to5', 'ipt_age5to15']]

        # Find start and end indices for economics calculations
        start_index = tool_kit.find_first_list_element_at_least_value(self.times,
                                                                      self.inputs.model_constants['recent_time'])
        end_index = tool_kit.find_first_list_element_at_least_value(self.times,
                                                                    self.inputs.model_constants['scenario_end_time'])

        # Find the current year and CPI
        year_current = self.inputs.model_constants['current_time']
        current_cpi = self.scaleup_fns['econ_cpi'](year_current)

        # Prepare the storage object. 'costs' will store the costs for each program being costed
        # and will be added to the current object instance.
        costs = {'cost_times': []}

        # Loop over interventions to be costed
        for intervention in self.interventions_to_cost:

            # Initialise output lists
            costs[intervention] = {'raw_cost': [],
                                   'inflated_cost': [],
                                   'discounted_cost': [],
                                   'discounted_inflated_cost': []}

            # for each step time. We may want to change this bit. No need for all time steps
            # Just add a third argument if you want to decrease the frequency of calculation
            for i in range(start_index, end_index + 1):
                t = self.times[i]

                # If it's the first intervention, store a list of times
                if intervention == self.interventions_to_cost[0]:
                    costs['cost_times'].append(t)

                # Raw cost
                cost = get_cost_from_coverage(self.coverage_over_time('program_prop_' + intervention)(t),
                                              self.inputs.model_constants['econ_inflectioncost_' + intervention],
                                              self.inputs.model_constants['econ_saturation_' + intervention],
                                              self.inputs.model_constants['econ_unitcost_' + intervention],
                                              self.var_array[i, self.var_labels.index('popsize_' + intervention)])

                # Start-up costs
                if self.startups_apply[intervention] \
                        and self.inputs.model_constants['scenario_start_time'] < t \
                        and t < self.inputs.model_constants['scenario_start_time'] \
                                + self.inputs.model_constants['econ_startupduration_' + intervention]:

                    # New code with beta PDF used to smooth out scale-up costs
                    cost += scipy.stats.beta.pdf((t - self.inputs.model_constants['scenario_start_time'])
                                                 / self.inputs.model_constants['econ_startupduration_' + intervention],
                                                 2.,
                                                 5.) \
                            / self.inputs.model_constants['econ_startupduration_' + intervention] \
                            * self.inputs.model_constants['econ_startupcost_' + intervention]

                    # Old code for constant function
                    # cost += self.inputs.model_constants['econ_startupcost_' + intervention] \
                    #         / self.inputs.model_constants['econ_startupduration_' + intervention]

                # Store uninflated cost
                costs[intervention]['raw_cost'].append(cost)

                # Calculate and store inflated cost
                cpi_time_variant = self.scaleup_fns['econ_cpi'](t)
                inflated_cost = inflate_cost(cost,
                                             current_cpi,
                                             cpi_time_variant)
                costs[intervention]['inflated_cost'].append(inflated_cost)

                # Calculate and store discounted cost
                t_into_future = max(0, (t - year_current))
                discounted_cost = discount_cost(cost,
                                                self.params['econ_discount_rate'],
                                                t_into_future)
                costs[intervention]['discounted_cost'].append(discounted_cost)

                # Calculate and store discounted-inflated cost
                discounted_inflated_cost = discount_cost(inflated_cost,
                                                self.params['econ_discount_rate'],
                                                t_into_future)
                costs[intervention]['discounted_inflated_cost'].append(discounted_inflated_cost)

        self.costs = costs

    def update_vars_from_cost(self):

        """
        update parameter values according to the funding allocated to each interventions. This process is done during
        integration
        Returns:
        Nothing
        """

        def get_coverage_from_cost(cost, c_inflection_cost, saturation, unit_cost, pop_size, alpha=1.0):

            """
            Estimate the coverage associated with a spending in a programme
            Args:
               cost: the amount of money allocated to a programme (absolute number, not a proportion of global funding)
               c_inflection_cost: cost at which inflection occurs on the curve. It's also the configuration leading to the
                                   best efficiency.
               saturation: maximal acceptable coverage, ie upper asymptote
               unit_cost: unit cost of the intervention
               pop_size: size of the population targeted by the intervention
               alpha: steepness parameter

            Returns:
               coverage (as a proportion, then lives in 0-1)

           """

            assert cost >= 0, 'cost must be positive or null'
            if cost <= c_inflection_cost:  # if cost is smaller thar c_inflection_cost, then the starting cost necessary to get coverage has not been reached
                return 0

            if pop_size * unit_cost == 0:  # if unit cost or pop_size is null, return 0
                return 0

            a = saturation / (1.0 - 2 ** alpha)
            b = ((2.0 ** (alpha + 1.0)) / (alpha * (saturation - a) * unit_cost * pop_size))
            coverage_estimated = a + (saturation - a) / (
                (1 + numpy.exp((-b) * (cost - c_inflection_cost))) ** alpha)
            return coverage_estimated

        interventions = self.interventions_to_cost
        for int in interventions:
            if (int in ['ipt_age0to5', 'ipt_age5to15']) and (len(self.agegroups) < 2):
                continue

            vars_key = 'program_prop_' + int
            cost = 1000000.
            if cost == 0:
                coverage = 0
            else:
                unit_cost = self.inputs.model_constants['econ_unitcost_' + int]
                c_inflection_cost = self.inputs.model_constants['econ_inflectioncost_' + int]
                saturation = self.inputs.model_constants['econ_saturation_' + int]
                popsize_key = 'popsize_' + int
                if popsize_key in self.vars.keys():
                    pop_size = self.vars[popsize_key]
                else:
                    pop_size = 0

                # starting costs
                # is a programm starting right now? In that case, update intervention_startdates
                if self.intervention_startdates[int] is None: # means intervention hadn't started yet
                    self.intervention_startdates[int] = self.time

                # calculate current starting cost
                current_start_cost = 0.
                if self.intervention_startdates[int] <= self.time <= self.intervention_startdates[int] + self.inputs.model_constants['econ_startupduration_' + int]:
                    current_start_cost = scipy.stats.beta.pdf((self.time - self.intervention_startdates[int])
                                                     / self.inputs.model_constants['econ_startupduration_' + int],
                                                     2.,
                                                     5.) \
                                / self.inputs.model_constants['econ_startupduration_' + int] \
                                * self.inputs.model_constants['econ_startupcost_' + int]

                remaining_money = cost - current_start_cost
                assert remaining_money >= 0, 'available funding is not enough to cover starting costs of ' + int + ' at time ' + str(self.time)

                coverage = get_coverage_from_cost(remaining_money, c_inflection_cost, saturation, unit_cost, pop_size, alpha=1.0)
            self.vars[vars_key] = coverage

    def get_compartment_soln(self, label):
        assert self.soln_array is not None, 'calculate_diagnostics has not been run'
        i_label = self.labels.index(label)
        return self.soln_array[:, i_label]

    def get_var_soln(self, label):

        assert self.var_array is not None, 'calculate_diagnostics has not been run'
        i_label = self.var_labels.index(label)
        return self.var_array[:, i_label]

    def get_flow_soln(self, label):
        assert self.flow_array is not None, 'calculate_diagnostics has not been run'
        i_label = self.labels.index(label)
        return self.flow_array[:, i_label]

    def load_state(self, i_time):

        self.time = self.times[i_time]
        for i_label, label in enumerate(self.labels):
            self.compartments[label] = \
                self.soln_array[i_time, i_label]

        return self.compartments

    def checks(self, error_margin=0.1):

        """
        Assertion run during the simulation, should be overridden
        for each model.

        Args:
            error_margin: acceptable difference between target invariants

        Returns:

        """

        # Check all compartments are positive
        for label in self.labels:
            assert self.compartments[label] >= 0.
        # Check population is conserved across compartments
        # population_change = \
        #       self.vars['births_vac'] \
        #     - self.vars['births_unvac'] \
        #     - self.vars['rate_death'] \
        #     - self.vars['rate_infection_death']
        # assert abs(sum(self.flows.values()) - population_change ) < error_margin

    def make_flow_diagram(self, png):

        from graphviz import Digraph

        styles = {
            'graph': {
                'label': 'Dynamic Transmission Model',
                'fontsize': '16',
            },
            'nodes': {
                'fontname': 'Helvetica',
                'shape': 'box',
                'style': 'filled',
                'fillcolor': '#CCDDFF',
            },
            'edges': {
                'style': 'dotted',
                'arrowhead': 'open',
                'fontname': 'Courier',
                'fontsize': '10',
            }
        }

        def apply_styles(graph, styles):
            graph.graph_attr.update(
                ('graph' in styles and styles['graph']) or {}
            )
            graph.node_attr.update(
                ('nodes' in styles and styles['nodes']) or {}
            )
            graph.edge_attr.update(
                ('edges' in styles and styles['edges']) or {}
            )
            return graph

        def num_str(f):
            abs_f = abs(f)
            if abs_f > 1E9:
                return '%.1fB' % (f/1E9)
            if abs_f > 1E6:
                return '%.1fM' % (f/1E6)
            if abs_f > 1E3:
                return '%.1fK' % (f/1E3)
            if abs_f > 100:
                return '%.0f' % f
            if abs_f > 0.5:
                return '%.1f' % f
            if abs_f > 0.05:
                return '%.2f' % f
            if abs_f > 0.0005:
                return '%.4f' % f
            if abs_f > 0.000005:
                return '%.6f' % f
            return str(f)

        self.graph = Digraph(format='png')
        for label in self.labels:
            self.graph.node(label)
        self.graph.node('tb_death')
        for from_label, to_label, var_label in self.var_transfer_rate_flows:
            self.graph.edge(from_label, to_label, label=var_label[:4])
        for from_label, to_label, rate in self.fixed_transfer_rate_flows:
            self.graph.edge(from_label, to_label, label=num_str(rate))
        for from_label, to_label, rate in self.linked_transfer_rate_flows:
            self.graph.edge(from_label, to_label, label='link')
        for label, rate in self.fixed_infection_death_rate_flows:
            self.graph.edge(label, 'tb_death', label=num_str(rate))
        for label, rate in self.var_infection_death_rate_flows:
            self.graph.edge(label, 'tb_death', label=var_label[:4])
        base, ext = os.path.splitext(png)
        if ext.lower() != '.png':
            base = png

        self.graph = apply_styles(self.graph, styles)

        self.graph.render(base)

    def determine_whether_startups_apply(self):

        """
        Determine whether an intervention is applied and has start-up costs in this scenario

        """

        # Start assuming each costed intervention has no start-up costs in this scenario
        for program in self.interventions_to_cost:
            self.startups_apply[program] = False

            # If the program reaches values greater than zero and start-up costs are greater than zero, change to true
            if self.inputs.intervention_applied[self.scenario]['program_prop_' + program] \
                    and self.inputs.model_constants['econ_startupcost_' + program] > 0.:
                self.startups_apply[program] = True

    def find_intervention_startdates(self):
        """
        Find the dates when the different interventions start and populate self.intervention_startdates
        """
        scenario = self.scenario
        for intervention in self.interventions_to_cost:
            self.intervention_startdates[intervention] = None
            param_key = 'program_prop_' + intervention
            param_key2 = 'program_perc_' + intervention
            param_dict = self.inputs.scaleup_data[scenario][param_key]
            years_pos_coverage = [key for (key, value) in param_dict.items() if value > 0.]  # years after start
            if len(years_pos_coverage) > 0:  # some coverage present at baseline
                self.intervention_startdates[intervention] = min(years_pos_coverage)

def add_unique_tuple_to_list(a_list, a_tuple):

    """
    Adds or modifies a list of tuples, compares only the items
    before the last in the tuples, the last value in the tuple
    is assumed to be a value.
    """

    for i, test_tuple in enumerate(a_list):
        if test_tuple[:-1] == a_tuple[:-1]:
            a_list[i] = a_tuple
            break
    else:
        a_list.append(a_tuple)

