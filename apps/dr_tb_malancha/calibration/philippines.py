from autumn.constants import Region
from apps.dr_tb_malancha.calibration import base
from .utils import get_prior_distributions, add_dispersion_param_prior_for_gaussian


def run_calibration_chain(max_seconds: int, run_id: int):
    base.run_calibration_chain(
        max_seconds,
        run_id,
        Region.PHILIPPINES,
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
        "years": [2007, 2016],
        "values": [0.00660, 0.01159],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "notifications",
        "years": [2018],
        "values": [382543],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "perc_strain_inh_R",
        "years": [2007, 2016],
        "values": [9.44, 12.43],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "perc_strain_rif_R",
        "years": [2007, 2016],
        "values": [1.008, 0.82],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "perc_strain_mdr",
        "years": [2007, 2016],
        "values": [5.8, 3.35],
        "loglikelihood_distri": "normal",
    },
]

PAR_PRIORS = add_dispersion_param_prior_for_gaussian(PAR_PRIORS, TARGET_OUTPUTS)


if __name__ == "__main__":
    run_calibration_chain(1000, 0)
