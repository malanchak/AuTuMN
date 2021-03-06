from summer.model import StratifiedModel
from autumn.constants import Compartment, BirthApproach
from autumn.tool_kit.scenarios import get_model_times_from_inputs
from summer.model.utils.flowchart import create_flowchart
from autumn.curve import scale_up_function


def build_model(params: dict, update_params={}) -> StratifiedModel:
    """
    Build the master function to run a simple SIR model

    :param update_params: dict
        Any parameters that need to be updated for the current run
    :return: StratifiedModel
        The final model with all parameters and stratifications
    """
    params.update(update_params)
    compartments = [
        Compartment.SUSCEPTIBLE,
        Compartment.EARLY_LATENT,
        Compartment.LATE_LATENT,
        Compartment.INFECTIOUS,
        Compartment.RECOVERED
    ]

    params['delta'] = params['beta'] * params['rr_reinfection_once_recovered']
    params['theta'] = params['beta'] * params['rr_reinfection_once_infected']

    flows = [
        {
            'type': 'infection_frequency',
            'parameter': 'beta',
            'origin': Compartment.SUSCEPTIBLE,
            'to': Compartment.EARLY_LATENT
        },
        {
            'type': 'standard_flows',
            'parameter': 'kappa',
            'origin': Compartment.EARLY_LATENT,
            'to': Compartment.LATE_LATENT
        },
        {
            'type': 'standard_flows',
            'parameter': 'epsilon',
            'origin': Compartment.EARLY_LATENT,
            'to': Compartment.INFECTIOUS
        },

        {
            'type': 'standard_flows',
            'parameter': 'nu',
            'origin': Compartment.LATE_LATENT,
            'to': Compartment.INFECTIOUS
        },
        {
            'type': 'standard_flows',
            'parameter': 'tau',
            'origin': Compartment.INFECTIOUS,
            'to': Compartment.RECOVERED
        },
        {
            'type': 'standard_flows',
            'parameter': 'gamma',
            'origin': Compartment.INFECTIOUS,
            'to': Compartment.RECOVERED
        },
        {
            'type': 'infection_frequency',
            'parameter': 'delta',
            'origin': Compartment.RECOVERED,
            'to': Compartment.EARLY_LATENT
        },
        {
            'type': 'infection_frequency',
            'parameter': 'theta',
            'origin': Compartment.LATE_LATENT,
            'to': Compartment.EARLY_LATENT
        },
        {
            'type': 'compartment_death',
            'parameter': 'infect_death',
            'origin': Compartment.INFECTIOUS
        }

    ]

    integration_times = get_model_times_from_inputs(
        round(params["start_time"]), params["end_time"], params["time_step"]
    )

    init_conditions = {Compartment.INFECTIOUS: 1}

    tb_sir_model = StratifiedModel(
        integration_times,
        compartments,
        init_conditions,
        params,
        requested_flows=flows,
        birth_approach=BirthApproach.REPLACE_DEATHS,
        entry_compartment='susceptible',
        starting_population=params['population_size'],
        infectious_compartment=(Compartment.INFECTIOUS,),
        verbose=True,

    )

    tb_sir_model.adaptation_functions['universal_death_rateX'] = lambda x: 1./70

# #   add  time_variant parameters
    def time_variant_CDR():
        times = [params['cdr_start_time'], 2020]
        values = [0., params['cdr_final_level']]
        return scale_up_function(times, values, method=4)

    my_tv_cdr = time_variant_CDR()

    def time_variant_TSR():
        times = [params['tsr_start_time'], 2020]
        values = [0., params['tsr_final_level']]
        return scale_up_function(times, values, method=4)

    my_tv_tsr = time_variant_TSR()

    def my_tv_tau(time):  # this is for DS-TB
        return my_tv_detection_rate(time) * my_tv_tsr(time)

    tb_sir_model.adaptation_functions["tau"] = my_tv_tau
    tb_sir_model.parameters["tau"] = "tau"

    def my_tv_detection_rate(time):
        return my_tv_cdr(time)/(1-my_tv_cdr(time)) * (params['gamma'] + params['universal_death_rate'] + params['infect_death']) #calculating the time varaint detection rate from tv CDR


   #adding strain stratification

    stratify_by = ['strain']  # ['strain', 'treatment_type']

    if 'strain' in stratify_by:

        tb_sir_model.stratify(
            "strain", ['ds', 'inh_R', 'rif_R', 'mdr'],
            compartment_types_to_stratify=[Compartment.EARLY_LATENT, Compartment.LATE_LATENT, Compartment.INFECTIOUS],
            requested_proportions={'ds': 1., 'inh_R': 0., 'rif_R':0., 'mdr': 0.},
            verbose=False,
            adjustment_requests={
                'beta': {'ds': 1., 'inh_R': params['fitness_inh_R'], 'rif_R': params['fitness_rif_R'], 'mdr': params['fitness_mdr']},
                'delta': {'ds': 1., 'inh_R': params['fitness_inh_R'], 'rif_R': params['fitness_rif_R'], 'mdr': params['fitness_mdr']},
                'theta': {'ds': 1., 'inh_R': params['fitness_inh_R'], 'rif_R': params['fitness_rif_R'], 'mdr': params['fitness_mdr']},
                'tau': {'ds': 1., 'inh_R': params['relative_TSR_H'], 'rif_R': params['relative_TSR_R'], 'mdr': params['relative_TSR_MDR']}
                }
        )

        # set up some amplification flows
        # from DS to INH_R
        tb_sir_model.add_transition_flow(
                    {"type": "standard_flows", "parameter": "dr_amplification_ds_to_inh",
                     "origin": "infectiousXstrain_ds", "to": "infectiousXstrain_inh_R",
                     "implement": len(tb_sir_model.all_stratifications)})

        def tv_amplification_ds_to_inh_rate(time):
            return my_tv_detection_rate(time) * (1 - my_tv_tsr(time)) * params['prop_of_failures_developing_inh_R']

        tb_sir_model.adaptation_functions["dr_amplification_ds_to_inh"] = tv_amplification_ds_to_inh_rate
        tb_sir_model.parameters["dr_amplification_ds_to_inh"] = "dr_amplification_ds_to_inh"


        #set up amplification flow for DS to RIF_R
        tb_sir_model.add_transition_flow(
                    {"type": "standard_flows", "parameter": "dr_amplification_ds_to_rif",
                     "origin": "infectiousXstrain_ds", "to": "infectiousXstrain_rif_R",
                     "implement": len(tb_sir_model.all_stratifications)})

        def tv_amplification_ds_to_rif_rate(time):
            return my_tv_detection_rate(time) * (1 - my_tv_tsr(time)) * params['prop_of_failures_developing_rif_R']

        tb_sir_model.adaptation_functions["dr_amplification_ds_to_rif"] = tv_amplification_ds_to_rif_rate
        tb_sir_model.parameters["dr_amplification_ds_to_rif"] = "dr_amplification_ds_to_rif"

        # set up amplification flow for INH_R to MDR
        tb_sir_model.add_transition_flow(
                {"type": "standard_flows", "parameter": "dr_amplification_inh_to_mdr",
                 "origin": "infectiousXstrain_inh_R", "to": "infectiousXstrain_mdr",
                 "implement": len(tb_sir_model.all_stratifications)})

        def tv_amplification_inh_to_mdr_rate(time):
            return my_tv_detection_rate(time) * (1 - (my_tv_tsr(time) * params['relative_TSR_H'])) * params['prop_of_failures_developing_inh_R']

        tb_sir_model.adaptation_functions["dr_amplification_inh_to_mdr"] = tv_amplification_inh_to_mdr_rate
        tb_sir_model.parameters["dr_amplification_inh_to_mdr"] = "dr_amplification_inh_to_mdr"

  		# set up amplification flow for RIF_R to MDR
        tb_sir_model.add_transition_flow(
                {"type": "standard_flows", "parameter": "dr_amplification_rif_to_mdr",
                 "origin": "infectiousXstrain_rif_R", "to": "infectiousXstrain_mdr",
                 "implement": len(tb_sir_model.all_stratifications)})

        def tv_amplification_rif_to_mdr_rate(time):
            return my_tv_detection_rate(time) * (1 - (my_tv_tsr(time) * params['relative_TSR_R'])) * params['prop_of_failures_developing_rif_R']

        tb_sir_model.adaptation_functions["dr_amplification_rif_to_mdr"] = tv_amplification_rif_to_mdr_rate
        tb_sir_model.parameters["dr_amplification_rif_to_mdr"] = "dr_amplification_rif_to_mdr"


    # Add trackers for the flows used to derive outputs
    flow_connections = {}

    #### track notifications in the model
    for strain in ['ds', 'inh_R', 'rif_R', 'mdr']:
        flow_connections["recovery_tracker_" + strain] = {
            "origin": Compartment.INFECTIOUS,
            "to": Compartment.RECOVERED,
            "origin_condition": "strain_" + strain,
            "to_condition": "",
        }

    ### track incidence flows to be able to distinguish DR amplification from transmission
    amplification_source = {
        "inh_R": ['ds'],
        "rif_R": ['ds'],
        "mdr": ["inh_R", "rif_R"]
    }
    for destination_strain, source_strains in amplification_source.items():
        flow_connections["incidence_progression_early" + destination_strain] = {
            "origin": Compartment.EARLY_LATENT,
            "to": Compartment.INFECTIOUS,
            "origin_condition": "strain_" + destination_strain,
            "to_condition": "",
        }
        flow_connections["incidence_progression_late" + destination_strain] = {
            "origin": Compartment.LATE_LATENT,
            "to": Compartment.INFECTIOUS,
            "origin_condition": "strain_" + destination_strain,
            "to_condition": "",
        }
        for source_strain in source_strains:
            flow_connections[f"incidence_ampli_from_{source_strain}_to_{destination_strain}"] = {
                "origin": Compartment.INFECTIOUS,
                "to": Compartment.INFECTIOUS,
                "origin_condition": "strain_" + source_strain,
                "to_condition": "strain_" + destination_strain,
            }

    tb_sir_model.output_connections = flow_connections

    # Prepare TSR calculation by strain
    def make_func_tsr_by_strain(strain):
        def tsr_by_strain(time):
            return my_tv_tsr(time) * params['relative_TSR_' + mapping[strain]]

        return tsr_by_strain

    tsr_by_strain = {'ds': my_tv_tsr}

    for strain_non_ds in ['inh_R', 'rif_R', 'mdr']:
        mapping = {
            'inh_R': 'H', 'rif_R': 'R', 'mdr': 'MDR'
        }
        tsr_by_strain[strain_non_ds] = make_func_tsr_by_strain(strain_non_ds)


    # calculate the derived output for notifications
    def get_notifications(model, time):
        notifications_count = 0.0
        time_idx = model.times.index(time)
        for strain in ['ds', 'inh_R', 'rif_R', 'mdr']:
            notifications_count += model.derived_outputs["recovery_tracker_" + strain][time_idx] / tsr_by_strain[strain](time)
        return notifications_count

    tb_sir_model.derived_output_functions["notifications"] = get_notifications

    # calculate prevalence infectious
    def get_prev_infectious(model, time):
        time_idx = model.times.index(time)
        infectious_compartments_indices = [i for i, c in enumerate(model.compartment_names) if 'infectious' in c]
        prev_infectious = sum([float(model.outputs[time_idx, i]) for i in infectious_compartments_indices])
        prev_infectious_prop = prev_infectious /\
                               sum([float(model.outputs[time_idx, i]) for i in range(len(model.compartment_names))])
        return prev_infectious_prop

    tb_sir_model.derived_output_functions["prev_infectious"] = get_prev_infectious

    # calculate proportion of strain-specific TB
    def make_get_strain_perc(strain):
        # strain is one of ['ds','inh_R', 'rif_R', 'mdr']
        def get_perc_strain(model, time):
            time_idx = model.times.index(time)
            infectious_compartments_indices = [i for i, c in enumerate(model.compartment_names) if 'infectious' in c]
            prev_infectious = sum([float(model.outputs[time_idx, i]) for i in infectious_compartments_indices])
            infectious_strain_compartments_indices = [i for i, c in enumerate(model.compartment_names) if 'infectiousXstrain_' + strain in c]
            prev_infectious_strain = sum([float(model.outputs[time_idx, i]) for i in infectious_strain_compartments_indices])
            perc_strain = 100. * prev_infectious_strain / prev_infectious
            return perc_strain
        return get_perc_strain

    for strain in ['inh_R', 'rif_R', 'mdr']:
        tb_sir_model.derived_output_functions["perc_strain_" + strain] = make_get_strain_perc(strain)

    # tb_sir_model.transition_flows.to_csv("transitions.csv")

    # create_flowchart(tb_sir_model, name="sir_model_diagram")

    # calculate percentage of transmitted DR among all incident DR
    def make_get_perc_dr_transmitted(strain):
        # strain is one of ['ds','inh_R', 'rif_R', 'mdr']
        def get_perc_dr_transmitted(model, time):
            time_idx = model.times.index(time)
            incidence_from_transmission = \
                model.derived_outputs["incidence_progression_early" + strain][time_idx] +\
                model.derived_outputs["incidence_progression_late" + strain][time_idx]
            incidence_from_amplification = 0
            for source_strain in amplification_source[strain]:
                incidence_from_amplification +=\
                    model.derived_outputs[f"incidence_ampli_from_{source_strain}_to_{strain}"][time_idx]

            return 100. * incidence_from_transmission / (incidence_from_transmission + incidence_from_amplification)

        return get_perc_dr_transmitted

    for strain in ['inh_R', 'rif_R', 'mdr']:
        tb_sir_model.derived_output_functions["perc_transmitted_" + strain] = make_get_perc_dr_transmitted(strain)

    return tb_sir_model

