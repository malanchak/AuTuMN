
import os
import glob
import datetime
import autumn.model
import autumn.tool_kit
from autumn.spreadsheet import read_input_data_xls
import autumn.outputs as outputs
import autumn.data_processing

# Start timer
start_realtime = datetime.datetime.now()

# Import the data
country = read_input_data_xls(True, ['control_panel'])['control_panel']['country']

inputs = autumn.data_processing.Inputs(True)
inputs.read_and_load_data()

print('Data have been loaded.')
print('Time elapsed so far is ' + str(datetime.datetime.now() - start_realtime) + '\n')

# A few basic preliminaries
out_dir = 'fullmodel_graphs'
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

project = outputs.Project(country, inputs)

base = os.path.join(out_dir, country + '_baseline')

models = {}
for n, scenario in enumerate(inputs.model_constants['scenarios_to_run']):

    # Name model
    if scenario is None:
        scenario_name = 'baseline'
    else:
        scenario_name = 'scenario_' + str(scenario)

    # Determine whether this is the final iteration of the loop
    if scenario == inputs.model_constants['scenarios_to_run'][-1]:
        final = True
    else:
        final = False

    # Create an outputs object for use later
    project.scenarios.append(scenario_name)

    models[scenario_name] = autumn.model.ConsolidatedModel(scenario, inputs)

    if n == 0:
        print(autumn.tool_kit.introduce_model(models, scenario_name))

    # Create Boolean for uncertainty for this run to save re-typing the multi-factorial condition statement
    uncertainty_this_run = False
    if (inputs.model_constants['output_uncertainty'] and scenario is None) \
            or inputs.model_constants['output_uncertainty_all_scenarios']:

        # Generally only run uncertainty if this on the baseline scenario, unless specified otherwise
        uncertainty_this_run = True

    if scenario is not None:
        scenario_start_time_index = \
            models['baseline'].find_time_index(inputs.model_constants['scenario_start_time'])
        models[scenario_name].start_time = \
            models['baseline'].times[scenario_start_time_index]
        models[scenario_name].loaded_compartments = \
            models['baseline'].load_state(scenario_start_time_index)
        if uncertainty_this_run:
            for count_run in range(len(models['baseline'].model_shelf)):
                new_model = autumn.model.ConsolidatedModel(scenario, inputs)
                new_model.start_time = models['baseline'].model_shelf[count_run].times[scenario_start_time_index]
                new_model.loaded_compartments = models['baseline'].model_shelf[count_run].load_state(scenario_start_time_index)
                new_model.integrate()
                models[scenario_name].model_shelf.append(new_model)

    # Describe model
    print('Running model "' + scenario_name + '".')
    if n == 0:
        print(autumn.tool_kit.describe_model(models, scenario_name))

    if uncertainty_this_run:
        models[scenario_name].run_uncertainty()

    # Integrate the rigid parameterization in any case. Indeed, we still need the central estimates for uncertainty
    models[scenario_name].integrate()

    print('Time elapsed to completion of integration is ' + str(datetime.datetime.now() - start_realtime))



    if inputs.model_constants['output_by_age']:
        autumn.outputs.plot_outputs_by_age(
            models[scenario_name],
            inputs.model_constants['recent_time'],
            'scenario_end_time',
            base + '_age_outputs_gtb.png',
            country,
            scenario=scenario,
            figure_number=21,
            final_run=final)

    project.models[scenario_name] = []
    if uncertainty_this_run:
        project.model_shelf_uncertainty[scenario_name] = models[scenario_name].model_shelf
    project.models[scenario_name] = models[scenario_name]

# Write to spreadsheets
project.create_output_dicts()  # Store simplified outputs

# Make a flow-diagram
if inputs.model_constants['output_flow_diagram']:
    models['baseline'].make_graph(base + '.workflow')

# Plot over subgroups
if inputs.model_constants['output_fractions']:
    subgroup_solns, subgroup_fractions = autumn.tool_kit.find_fractions(models['baseline'])
    for i, category in enumerate(subgroup_fractions):
        autumn.outputs.plot_fractions(
            models['baseline'],
            subgroup_fractions[category],
            models['baseline'].inputs.model_constants['recent_time'],
            'strain', base + '_fraction_' + category + '.png',
            figure_number=30+i)

# Plot proportions of population
if inputs.model_constants['output_comorbidity_fractions']:
    autumn.outputs.plot_stratified_populations(models['baseline'],
                                               png=base + '_comorbidity_fraction.png',
                                               age_or_comorbidity='comorbidity',
                                               start_time='early_time')

# Plot proportions of population
if inputs.model_constants['output_age_fractions']:
    autumn.outputs.plot_stratified_populations(models['baseline'],
                                               png=base + '_age_fraction.png',
                                               age_or_comorbidity='age',
                                               start_time='early_time')

pngs = glob.glob(os.path.join(out_dir, '*png'))

project.write_spreadsheets()
project.write_documents()
project.run_plotting()

autumn.outputs.open_pngs(pngs)

print('Time elapsed in running script is ' + str(datetime.datetime.now() - start_realtime))
