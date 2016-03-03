digraph {
	graph [fontsize=16 label="Dynamic Transmission Model"]
	node [fillcolor="#CCDDFF" fontname=Helvetica shape=box style=filled]
	edge [arrowhead=open fontname=Courier fontsize=10 style=dotted]
		susceptible_fully_nocomorbs
		susceptible_vac_nocomorbs
		susceptible_treated_nocomorbs
		latent_early_ds_nocomorbs
		latent_late_ds_nocomorbs
		active_smearpos_ds_nocomorbs
		active_smearneg_ds_nocomorbs
		active_extrapul_ds_nocomorbs
		detect_smearpos_ds_nocomorbs
		detect_smearneg_ds_nocomorbs
		detect_extrapul_ds_nocomorbs
		missed_smearpos_ds_nocomorbs
		missed_smearneg_ds_nocomorbs
		missed_extrapul_ds_nocomorbs
		treatment_infect_smearpos_ds_nocomorbs
		treatment_infect_smearneg_ds_nocomorbs
		treatment_infect_extrapul_ds_nocomorbs
		treatment_noninfect_smearpos_ds_nocomorbs
		treatment_noninfect_smearneg_ds_nocomorbs
		treatment_noninfect_extrapul_ds_nocomorbs
		tb_death
			susceptible_fully_nocomorbs -> latent_early_ds_nocomorbs [label=rate_force_ds]
			susceptible_vac_nocomorbs -> latent_early_ds_nocomorbs [label=rate_force_weak_ds]
			susceptible_treated_nocomorbs -> latent_early_ds_nocomorbs [label=rate_force_weak_ds]
			latent_late_ds_nocomorbs -> latent_early_ds_nocomorbs [label=rate_force_weak_ds]
			latent_early_ds_nocomorbs -> latent_late_ds_nocomorbs [label=2.3]
			latent_early_ds_nocomorbs -> active_smearpos_ds_nocomorbs [label=0.20]
			latent_late_ds_nocomorbs -> active_smearpos_ds_nocomorbs [label=0.0042]
			active_smearpos_ds_nocomorbs -> latent_late_ds_nocomorbs [label=0.10]
			latent_early_ds_nocomorbs -> active_smearneg_ds_nocomorbs [label=0.07]
			latent_late_ds_nocomorbs -> active_smearneg_ds_nocomorbs [label=0.0014]
			active_smearneg_ds_nocomorbs -> latent_late_ds_nocomorbs [label=0.30]
			latent_early_ds_nocomorbs -> active_extrapul_ds_nocomorbs [label=0.07]
			latent_late_ds_nocomorbs -> active_extrapul_ds_nocomorbs [label=0.0014]
			active_extrapul_ds_nocomorbs -> latent_late_ds_nocomorbs [label=0.30]
			active_smearpos_ds_nocomorbs -> detect_smearpos_ds_nocomorbs [label=2.9]
			active_smearpos_ds_nocomorbs -> missed_smearpos_ds_nocomorbs [label=0.47]
			detect_smearpos_ds_nocomorbs -> treatment_infect_smearpos_ds_nocomorbs [label=25.6]
			missed_smearpos_ds_nocomorbs -> active_smearpos_ds_nocomorbs [label=0.27]
			active_smearneg_ds_nocomorbs -> detect_smearneg_ds_nocomorbs [label=2.9]
			active_smearneg_ds_nocomorbs -> missed_smearneg_ds_nocomorbs [label=0.47]
			detect_smearneg_ds_nocomorbs -> treatment_infect_smearneg_ds_nocomorbs [label=25.6]
			missed_smearneg_ds_nocomorbs -> active_smearneg_ds_nocomorbs [label=0.27]
			active_extrapul_ds_nocomorbs -> detect_extrapul_ds_nocomorbs [label=2.9]
			active_extrapul_ds_nocomorbs -> missed_extrapul_ds_nocomorbs [label=0.47]
			detect_extrapul_ds_nocomorbs -> treatment_infect_extrapul_ds_nocomorbs [label=25.6]
			missed_extrapul_ds_nocomorbs -> active_extrapul_ds_nocomorbs [label=0.27]
			treatment_infect_smearpos_ds_nocomorbs -> treatment_noninfect_smearpos_ds_nocomorbs [label=28.0]
			treatment_infect_smearpos_ds_nocomorbs -> active_smearpos_ds_nocomorbs [label=0.18]
			treatment_noninfect_smearpos_ds_nocomorbs -> active_smearpos_ds_nocomorbs [label=0.17]
			treatment_noninfect_smearpos_ds_nocomorbs -> susceptible_treated_nocomorbs [label=1.7]
			treatment_infect_smearneg_ds_nocomorbs -> treatment_noninfect_smearneg_ds_nocomorbs [label=28.0]
			treatment_infect_smearneg_ds_nocomorbs -> active_smearneg_ds_nocomorbs [label=0.18]
			treatment_noninfect_smearneg_ds_nocomorbs -> active_smearneg_ds_nocomorbs [label=0.17]
			treatment_noninfect_smearneg_ds_nocomorbs -> susceptible_treated_nocomorbs [label=1.7]
			treatment_infect_extrapul_ds_nocomorbs -> treatment_noninfect_extrapul_ds_nocomorbs [label=28.0]
			treatment_infect_extrapul_ds_nocomorbs -> active_extrapul_ds_nocomorbs [label=0.18]
			treatment_noninfect_extrapul_ds_nocomorbs -> active_extrapul_ds_nocomorbs [label=0.17]
			treatment_noninfect_extrapul_ds_nocomorbs -> susceptible_treated_nocomorbs [label=1.7]
			active_smearpos_ds_nocomorbs -> tb_death [label=0.26]
			detect_smearpos_ds_nocomorbs -> tb_death [label=0.26]
			active_smearneg_ds_nocomorbs -> tb_death [label=0.07]
			detect_smearneg_ds_nocomorbs -> tb_death [label=0.07]
			active_extrapul_ds_nocomorbs -> tb_death [label=0.07]
			detect_extrapul_ds_nocomorbs -> tb_death [label=0.07]
			treatment_infect_smearpos_ds_nocomorbs -> tb_death [label=0.18]
			treatment_noninfect_smearpos_ds_nocomorbs -> tb_death [label=0.17]
			treatment_infect_smearneg_ds_nocomorbs -> tb_death [label=0.18]
			treatment_noninfect_smearneg_ds_nocomorbs -> tb_death [label=0.17]
			treatment_infect_extrapul_ds_nocomorbs -> tb_death [label=0.18]
			treatment_noninfect_extrapul_ds_nocomorbs -> tb_death [label=0.17]
}