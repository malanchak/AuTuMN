from autumn.constants import Region
from apps.dr_tb_malancha.calibration import base
from .utils import get_prior_distributions


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
    "prevXinfectiousXamong": 100000,
    "prevXinfectiousXstrain_inh_RXamongXinfectious": 100,
    "prevXinfectiousXstrain_rif_RXamongXinfectious": 100,
    "prevXinfectiousXstrain_mdrXamongXinfectious": 100,
}

TARGET_OUTPUTS = [
    {
        "output_key": "prevXinfectiousXamong",
        "years": [2007, 2016],
        "values": [660, 1159],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "notifications",
        "years": [2018],
        "values": [382543],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "prevXinfectiousXstrain_inh_RXamongXinfectious",
        "years": [2007, 2016],
        "values": [9.44, 12.43],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "prevXinfectiousXstrain_rif_RXamongXinfectious",
        "years": [2007, 2016],
        "values": [1.008, 0.82],
        "loglikelihood_distri": "normal",
    },
    {
        "output_key": "prevXinfectiousXstrain_mdrXamongXinfectious",
        "years": [2007, 2016],
        "values": [5.8, 3.35],
        "loglikelihood_distri": "normal",
    },
]

if __name__ == "__main__":
    run_calibration_chain(1000, 0)
