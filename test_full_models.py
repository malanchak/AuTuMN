

import os
import glob
import datetime
import autumn.model
import autumn.plotting
from autumn.spreadsheet import read_and_process_data

def indices(a, func):
    return [i for (i, val) in enumerate(a) if func(val)]

# Start timer
start_realtime = datetime.datetime.now()

# Decide on country
country = u'Fiji'

# A few basic preliminaries
out_dir = 'fullmodel_graphs'
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)
keys_of_sheets_to_read = [
    'bcg', 'birth_rate', 'life_expectancy', 'attributes', 'parameters', 'miscellaneous', 'programs', 'tb',
    'notifications', 'outcomes']
data = read_and_process_data(True, keys_of_sheets_to_read, country)

# Note that it takes about one hour to run all of the possible model structures,
# so perhaps don't do that
for n_organs in data['attributes']['n_organs']:
    for n_strains in data['attributes']['n_strains']:
        for n_comorbidities in data['attributes']['n_comorbidities']:
            for is_quality in data['attributes']['is_lowquality']:
                for is_amplification in data['attributes']['is_amplification']:
                    for is_misassignment in data['attributes']['is_misassignment']:
                        if (is_misassignment and not is_amplification) \
                                or (n_strains <= 1 and (is_amplification or is_misassignment)):
                            pass
                        else:
                            name = 'model%d' % n_organs
                            base = os.path.join(out_dir, name)

                            model = autumn.model.ConsolidatedModel(
                                n_organs,
                                n_strains,
                                n_comorbidities,
                                is_quality,  # Low quality care
                                is_amplification,  # Amplification
                                is_misassignment,  # Misassignment by strain
                                data)
                            print(str(n_organs) + " organ(s),   " +
                                  str(n_strains) + " strain(s),   " +
                                  str(n_comorbidities) + " comorbidity(ies),   " +
                                  "Low quality? " + str(is_quality) + ",   " +
                                  "Amplification? " + str(is_amplification) + ",   " +
                                  "Misassignment? " + str(is_misassignment) + ".")

                            for key, value in data['parameters'].items():
                                model.set_parameter(key, value)
                            for key, value in data['miscellaneous'].items():
                                model.set_parameter(key, value)

                            model.make_times(data['attributes']['start_time'], data['attributes']['current_time'], 0.1)
                            model.integrate()

                            # Only make a flow-diagram if the model isn't overly complex
                            if n_organs + n_strains + n_comorbidities <= 5:
                                model.make_graph(base + '.workflow')

                            # INDIVIDUAL COMPARTMENTS
                            # autumn.plotting.plot_fractions(
                            #     model, model.labels, model.compartment_soln, data['attributes']['recent_time'],
                            #     "strain", base + '.individ_total_bystrain.png')
                            # autumn.plotting.plot_fractions(
                            #     model, model.labels, model.compartment_soln, data['attributes']['recent_time'],
                            #     "organ", base + '.individ_total_byorgan.png')
                            # autumn.plotting.plot_fractions(
                            #     model, model.labels, model.fraction_soln, data['attributes']['recent_time'],
                            #     "strain", base + '.individ_fraction_bystrain.png')
                            # autumn.plotting.plot_fractions(
                            #     model, model.labels, model.fraction_soln, data['attributes']['recent_time'],
                            #     "organ", base + '.individ_fraction_byorgan.png')
                            # COMPARTMENT TYPES
                            # autumn.plotting.plot_fractions(
                            #     model, model.compartment_types, model.compartment_type_fraction_soln, data['attributes']['recent_time'],
                            #     "", base + '.types_fraction.png')
                            # autumn.plotting.plot_fractions(
                            #     model, model.compartment_types, model.compartment_type_soln, data['attributes']['recent_time'],
                            #     "", base + '.types_total.png')
                            # autumn.plotting.plot_fractions(
                            #     model, model.compartment_types_bystrain, model.compartment_type_bystrain_fraction_soln, data['attributes']['recent_time'],
                            #     "strain", base + '.types_fraction_bystrain.png')
                            # BROAD COMPARTMENT TYPES
                            # autumn.plotting.plot_fractions(
                            #     model, model.broad_compartment_types, model.broad_fraction_soln, data['attributes']['recent_time'],
                            #     "", base + '.broad_fraction.png')
                            # autumn.plotting.plot_fractions(
                            #     model, model.broad_compartment_types, model.broad_fraction_soln, data['attributes']['start_time'],
                            #     "", base + '.broad_fraction.png')
                            # autumn.plotting.plot_fractions(
                            #     model, model.broad_compartment_types_bystrain, model.broad_compartment_type_bystrain_fraction_soln, data['attributes']['recent_time'],
                            #     "strain", base + '.broadtypes_fraction_bystrain.png')
                            # autumn.plotting.plot_fractions(
                            #     model, model.broad_compartment_types_byorgan, model.broad_compartment_type_byorgan_fraction_soln, data['attributes']['recent_time'],
                            #     "organ", base + '.broadtypes_fraction_byorgan.png')
                            # SUBGROUPS
                            # autumn.plotting.plot_fractions(
                            #     model, model.groups["treatment"], model.treatment_fraction_soln, data['attributes']['recent_time'],
                            #     "", base + '.treatment_fraction.png')
                            # autumn.plotting.plot_fractions(
                            #     model, model.groups["identified"], model.identified_fraction_soln, data['attributes']['recent_time'],
                            #     "", base + '.identified.png')
                            # OUTPUT RATES
                            # if n_strains >= 2:
                            #     autumn.plotting.plot_outputs(
                            #         model, ["incidence_ds", "incidence_mdr", "mortality_ds", "mortality_mdr", "prevalence_ds", "prevalence_mdr",
                            #                 "notifications_ds", "notifications_mdr"],
                            #         data['attributes']['start_time'], base + '.rate_bystrain_outputs.png')
                            autumn.plotting.plot_outputs(
                                model, ["incidence", "mortality", "prevalence"],
                                data['attributes']['start_time'], base + '.rate_outputs.png')
                            autumn.plotting.plot_outputs_against_gtb(
                                model, "incidence",
                                data['attributes']['recent_time'], base + '.rate_outputs_gtb.png',
                                data)
                            autumn.plotting.plot_all_outputs_against_gtb(
                                model, ["incidence", "mortality", "prevalence", "notifications"],
                                data['attributes']['recent_time'], base + '.rate_outputs_gtb_new.png',
                                data, country)
                            # if n_strains >= 2:
                            #     autumn.plotting.plot_outputs(
                            #         model, ["incidence_ds", "incidence_mdr", "mortality_ds", "mortality_mdr", "prevalence_ds", "prevalence_mdr",
                            #                 "notifications_ds", "notifications_mdr"],
                            #         data['attributes']['recent_time'], base + '.rate_bystrain_outputs_recent.png')
                            #     autumn.plotting.plot_outputs(
                            #         model, ["incidence_ds", "incidence_mdr", "mortality_ds", "mortality_mdr", "prevalence_ds", "prevalence_mdr",
                            #                 "notifications_ds", "notifications_mdr"],
                            #         start_time, base + '.rate_outputs.png')
                            #     autumn.plotting.plot_outputs(
                            #         model, ["incidence_mdr", "prevalence_mdr", "mortality_mdr"],
                            #         data['attributes']['start_time'], base + '.mdr_outputs.png')
                            #     autumn.plotting.plot_outputs(
                            #         model, ["incidence_mdr", "prevalence_mdr", "mortality_mdr"],
                            #         data['attributes']['recent_time'], base + '.mdr_outputs_recent.png')
                            #     autumn.plotting.plot_outputs(
                            #         model, ["proportion_mdr"],
                            #         data['attributes']['start_time'], base + '.mdr_proportion_recent.png')
                            #
                            vars_to_plot = []
                            for var in model.programs.keys():
                                if var in model.programs.keys() and 'inappropriate' not in var\
                                        and 'xdr' not in var and 'lowquality' not in var\
                                        and 'mdr' not in var and 'dst' not in var:
                                    vars_to_plot += [var]

                            autumn.plotting.plot_scaleup_fns(model,
                                                             vars_to_plot,
                                                             base + '.scaleups_start.png', data['attributes']['start_time'])
                            autumn.plotting.plot_scaleup_fns(model,
                                                             vars_to_plot,
                                                             base + '.scaleups_recent.png', data['attributes']['recent_time'])
                            autumn.plotting.plot_all_scaleup_fns_against_data(model,
                                                                              vars_to_plot,
                                                                              base + '.scaleup_recent.png',
                                                                              data['attributes']['recent_time'])
                            autumn.plotting.plot_all_scaleup_fns_against_data(model,
                                                                              vars_to_plot,
                                                                              base + '.scaleup_start.png',
                                                                              data['attributes']['start_time'])
                            #
                            #     year = indices(model.times, lambda x: x >= 2015.)[0]
                            #     print("2015 incidence is: ")
                            #     print(model.get_var_soln("incidence")[year])
                            #     print("2015 prevalence is: ")
                            #     print(model.get_var_soln("prevalence")[year])
                            #     print("2015 proportion MDR-TB is: ")
                            #     print(model.get_var_soln("proportion_mdr")[year])
                            #     print("2015 mortality is: ")
                            #     print(model.get_var_soln("mortality")[year])

pngs = glob.glob(os.path.join(out_dir, '*png'))
autumn.plotting.open_pngs(pngs)

print("Time elapsed in running script is " + str(datetime.datetime.now() - start_realtime))

