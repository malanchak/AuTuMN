from autumn.constants import Region
from apps.covid_19.calibration import base


def run_calibration_chain(max_seconds: int, run_id: int):
    base.run_calibration_chain(
        max_seconds, run_id, Region.CENTRAL_VISAYAS, PAR_PRIORS, TARGET_OUTPUTS, mode="autumn_mcmc",
        _multipliers=MULTIPLIERS
    )


MULTIPLIERS = {
    "prevXlateXclinical_icuXamong": 7957050.0
}  # to get absolute pop size instead of proportion


PAR_PRIORS = [
    {"param_name": "contact_rate", "distribution": "uniform", "distri_params": [0.010, 0.05],},
    {"param_name": "start_time", "distribution": "uniform", "distri_params": [0.0, 40.0],},
    # Add extra params for negative binomial likelihood
    {
        "param_name": "infection_deathsXall_dispersion_param",
        "distribution": "uniform",
        "distri_params": [0.1, 5.0],
    },
    {
        "param_name": "notifications_dispersion_param",
        "distribution": "uniform",
        "distri_params": [0.1, 5.0],
    },
    {
        "param_name": "prevXlateXclinical_icuXamong_dispersion_param",
        "distribution": "uniform",
        "distri_params": [0.1, 5.0],
    },
    {
        "param_name": "compartment_periods_calculated.incubation.total_period",
        "distribution": "gamma",
        "distri_mean": 5.0,
        "distri_ci": [4.4, 5.6],
    },
    {
        "param_name": "compartment_periods_calculated.total_infectious.total_period",
        "distribution": "gamma",
        "distri_mean": 7.0,
        "distri_ci": [4.5, 9.5],
    },
    # parameters to derive age-specific IFRs
    {
        "param_name": "ifr_double_exp_model_params.k",
        "distribution": "uniform",
        "distri_params": [6., 14.],
    },
    {
        "param_name": "ifr_double_exp_model_params.last_representative_age",
        "distribution": "uniform",
        "distri_params": [75., 85.],
    },
]

# death data:
death_times = [
     75,
     83,
     87,
     88,
     90,
     96,
     97,
    101,
    109,
    113,
    116,
    117,
    120,
    121,
    122,
    123,
    126,
    127,
    129,
    130,
    132,
    133,
    134,
    136,
    137,
    139,
    140,
    141,
    142,
    143,
    144,
    145,
    146,
    148,
    149,
    150,
    151,
    152,
    153,
    155,
    156,
    157,
    158,
    159,
    160,
    161,
    162,
    163,
    165,
    166,
    167,
    168,
]

death_values = [
      1,
      1,
      1,
      1,
      1,
      2,
      1,
      1,
      1,
      1,
      2,
      1,
      1,
      2,
      1,
      1,
      2,
      1,
      1,
      5,
      1,
      2,
      3,
      1,
      1,
      2,
      4,
      1,
      6,
      4,
      2,
      1,
      3,
      3,
      2,
      2,
      3,
      1,
      3,
      3,
      1,
      1,
      1,
      1,
      1,
      4,
      3,
      5,
      1,
      6,
      3,
      2,
]

# notification data:
notification_times = [
     66,
     70,
     71,
     72,
     76,
     77,
     78,
     79,
     80,
     81,
     82,
     83,
     85,
     86,
     87,
     89,
     90,
     93,
     95,
     97,
    100,
    101,
    102,
    103,
    104,
    105,
    106,
    107,
    108,
    109,
    110,
    111,
    112,
    113,
    114,
    115,
    116,
    117,
    118,
    119,
    120,
    121,
    122,
    123,
    124,
    125,
    126,
    127,
    128,
    129,
    130,
    131,
    132,
    133,
    134,
    135,
    136,
    137,
    138,
    139,
    140,
    141,
    142,
    143,
    144,
    145,
    146,
    147,
    148,
    149,
    150,
    151,
    152,
    153,
    154,
    155,
    156,
    157,
    158,
    159,
    160,
    161,
    162,
    163,
    164,
    165,
    166,
    167,
    168,
]

notification_values = [
       1,
       1,
       1,
       1,
       2,
       3,
       1,
       3,
       2,
       4,
       2,
       1,
       5,
       4,
       2,
       1,
       1,
       2,
       1,
       2,
       7,
      21,
      25,
       2,
      17,
      26,
      50,
       8,
     138,
      24,
      30,
      76,
      39,
      36,
       3,
     107,
     131,
      92,
      81,
     120,
       8,
     102,
     210,
      37,
      16,
      67,
      82,
      78,
      60,
      18,
       3,
       2,
       2,
      14,
      14,
      13,
      90,
      52,
       3,
       4,
      53,
       7,
       8,
      55,
      23,
      23,
     137,
     138,
     108,
     335,
     143,
     141,
     176,
     210,
     160,
     106,
      87,
      72,
     107,
      81,
     117,
      89,
      62,
     169,
     299,
     122,
     444,
     267,
     257,
]

# ICU data:
icu_times = [
    146,
    147,
    148,
    149,
    150,
    151,
    152,
    153,
    154,
    155,
    156,
    157,
    158,
    159,
    160,
    161,
    162,
    163,
    164,
    165,
    166,
    167,
    168,
    169,
    170,
    171,
    172,
    173,
    174,
    175,
    176,
]

icu_values = [
      25,
      26,
      26,
      27,
      26,
      26,
      23,
      25,
      22,
      31,
      26,
      38,
      39,
      27,
      28,
      30,
      26,
      28,
      29,
      36,
      43,
      35,
      34,
      39,
      50,
      55,
      58,
      61,
      67,
      61,
      55,
]

TARGET_OUTPUTS = [
    {
        "output_key": "infection_deathsXall",
        "years": death_times,
        "values": death_values,
        "loglikelihood_distri": "negative_binomial",
    },
    {
        "output_key": "notifications",
        "years": notification_times,
        "values": notification_values,
        "loglikelihood_distri": "negative_binomial",
    },
    {
        "output_key": "prevXlateXclinical_icuXamong",
        "years": icu_times,
        "values": icu_values,
        "loglikelihood_distri": "negative_binomial",
    },
]
