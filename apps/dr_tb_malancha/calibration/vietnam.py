from autumn.constants import Region
from apps.dr_tb_malancha.calibration import base
from .utils import get_prior_distributions, add_dispersion_param_prior_for_gaussian


def run_calibration_chain(max_seconds: int, run_id: int):
    base.run_calibration_chain(
        max_seconds,
        run_id,
        Region.VIETNAM,
        PAR_PRIORS,
        TARGET_OUTPUTS,
        mode="autumn_mcmc",
        _multipliers=MULTIPLIERS,
    )

PAR_PRIORS = get_prior_distributions()

MULTIPLIERS = {
}

TARGET_OUTPUTS = [
    {
        "output_key": "prev_infectious",
        "years": [2007, 2018],
        "values": [0.00307, 0.00322],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "notifications",
        "years": [2018],
        "values": [102171],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "perc_strain_inh_R",
        "years": [2011],
        "values": [14.86],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "perc_strain_rif_R",
        "years": [2011],
        "values": [0.23],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "perc_strain_mdr",
        "years": [2011],
        "values": [6.93],
        "loglikelihood_distri": "normal",
    },

]


PAR_PRIORS = add_dispersion_param_prior_for_gaussian(PAR_PRIORS, TARGET_OUTPUTS)

if __name__ == "__main__":
    run_calibration_chain(1000, 0)
