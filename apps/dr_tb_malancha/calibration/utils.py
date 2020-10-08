
def get_prior_distributions():
    par_priors = [
        {"param_name": "beta", "distribution": "uniform", "distri_params": [3.0, 12.0],},
        # {"param_name": "epsilon", "distribution": "lognormal", "distri_params": [-6.78, 0.15]},
        # {"param_name": "kappa", "distribution": "lognormal", "distri_params": [-4.50, 0.13]},
        # {"param_name": "nu", "distribution": "lognormal", "distri_params": [-11.99, 0.34]},
        # {"param_name": "gamma", "distribution": "gamma", "distri_mean": 0.2, "distri_ci": [0.16, 0.29]},
        {
            "param_name": "rr_reinfection_once_recovered",
            "distribution": "uniform",
            "distri_params": [0.5, 1.5],
        },
        {
            "param_name": "prop_of_failures_developing_inh_R",
            "distribution": "uniform",
            "distri_params": [.01, 0.99],
        },
        {
            "param_name": "prop_of_failures_developing_rif_R",
            "distribution": "uniform",
            "distri_params": [0.01, 0.99],
        },
        {
            "param_name": "cdr_start_time",
            "distribution": "uniform",
            "distri_params": [1950., 1970.],
        },
        {
            "param_name": "cdr_final_level",
            "distribution": "uniform",
            "distri_params": [.3, .8],
        },
        {
            "param_name": "fitness_inh_R",
            "distribution": "uniform",
            "distri_params": [.9, 1.2],
        },
        {
            "param_name": "fitness_rif_R",
            "distribution": "uniform",
            "distri_params": [.5, 1.2],
        },
        {
            "param_name": "fitness_mdr",
            "distribution": "uniform",
            "distri_params": [.5, 1.2],
        },
    ]

    return par_priors


def add_dispersion_param_prior_for_gaussian(par_priors, target_outputs):
    for t in target_outputs:
        if t["loglikelihood_distri"] == "normal":
            max_val = max(t["values"])
            # sd_ that would make the 95% gaussian CI cover half of the max value (4*sd = 95% width)
            sd_ = 0.25 * max_val / 4.0
            lower_sd = sd_ / 2.0
            upper_sd = 2.0 * sd_

            par_priors.append(
                {
                    "param_name": t["output_key"] + "_dispersion_param",
                    "distribution": "uniform",
                    "distri_params": [lower_sd, upper_sd],
                },
            )

    return par_priors
