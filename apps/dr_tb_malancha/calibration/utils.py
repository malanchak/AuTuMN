
def get_prior_distributions():
    par_priors = [
        {"param_name": "beta", "distribution": "uniform", "distri_params": [3.0, 12.0],},
        {"param_name": "epsilon", "distribution": "lognormal", "distri_params": [-6.78, 0.15]},
        {"param_name": "kappa", "distribution": "lognormal", "distri_params": [-4.50, 0.13]},
        {"param_name": "nu", "distribution": "lognormal", "distri_params": [-11.99, 0.34]},
        {"param_name": "gamma", "distribution": "gamma", "distri_mean": 0.2, "distri_ci": [0.16, 0.29]},
        {
            "param_name": "infect_death",
            "distribution": "gamma",
            "distri_mean": 0.08,
            "distri_ci": [.06, 1.06],
        },
        {
        	"param_name": "rr_reinfection_once_recovered",
        	"distribution": "uniform",
        	"distri_ci": [0.5, 1.5],
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
    ]

    return par_priors
