from autumn.constants import Region
from apps.covid_19.calibration import base


def run_calibration_chain(max_seconds: int, run_id: int, num_chains: int):
    base.run_calibration_chain(
        max_seconds,
        run_id,
        num_chains,
        Region.MALAYSIA,
        PAR_PRIORS,
        TARGET_OUTPUTS,
        mode="autumn_mcmc",
        _multipliers=MULTIPLIERS,
    )


PAR_PRIORS = [
    {
        "param_name": "contact_rate",
        "distribution": "uniform",
        "distri_params": [0.015, 0.040],
    },
    {
        "param_name": "start_time",
        "distribution": "uniform",
        "distri_params": [0.0, 40.0],
    },
    {
        "param_name": "compartment_periods_calculated.incubation.total_period",
        "distribution": "uniform",
        "distri_mean": 5.0,
        "distri_ci": [4.4, 5.6],
    },
    {
        "param_name": "compartment_periods.icu_late",
        "distribution": "uniform",
        "distri_mean": 10.8,
        "distri_ci": [5.0, 16.0],
    },
    {
        "param_name": "compartment_periods.icu_early",
        "distribution": "uniform",
        "distri_mean": 12.7,
        "distri_ci": [2.0, 25.0],
    },
    {
        "param_name": "tv_detection_sigma",
        "distribution": "uniform",
        "distri_mean": 0.25,
        "distri_ci": [0.1, 0.4],
    },
    {
        "param_name": "tv_detection_b",
        "distribution": "uniform",
        "distri_mean": 0.075,
        "distri_ci": [0.05, 0.1],
    },
    {
        "param_name": "prop_detected_among_symptomatic",
        "distribution": "uniform",
        "distri_mean": 0.7,
        "distri_ci": [0.6, 0.9],
    },
    {
        "param_name": "icu_prop",
        "distribution": "uniform",
        "distri_mean": 0.17,
        "distri_ci": [0.1, 0.35],
    },
    # Add negative binomial over-dispersion parameters
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
        "param_name": "microdistancing.parameters.sigma",
        "distribution": "uniform",
        "distri_params": [0.4, 0.9],
    },
    {
        "param_name": "microdistancing.parameters.c",
        "distribution": "uniform",
        "distri_params": [78.0, 124.0],
    },
]

# notification data, provided by the country
notification_times = [
    63,
    64,
    65,
    66,
    67,
    68,
    69,
    70,
    71,
    72,
    73,
    74,
    75,
    76,
    77,
    78,
    79,
    80,
    81,
    82,
    83,
    84,
    85,
    86,
    87,
    88,
    89,
    90,
    91,
    92,
    93,
    94,
    95,
    96,
    97,
    98,
    99,
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
    169,
    170,
    171,
    172,
    173,
    174,
    175,
    176,
    177,
    178,
    179,
    180,
    181,
    182,
    183,
    184,
    185,
    186,
    187,
    188,
    189,
    190,
    191,
    192,
    193,
    194,
    195,
    196,
    197,
    198,
    199,
    200,
    201,
    202,
    203,
]
notification_counts = [
    7,
    14,
    5,
    28,
    10,
    6,
    18,
    12,
    20,
    9,
    45,
    35,
    190,
    125,
    120,
    117,
    110,
    130,
    153,
    123,
    212,
    106,
    172,
    235,
    130,
    159,
    150,
    156,
    140,
    142,
    208,
    217,
    150,
    179,
    131,
    170,
    156,
    109,
    118,
    184,
    153,
    134,
    170,
    85,
    110,
    69,
    54,
    84,
    36,
    57,
    50,
    71,
    88,
    51,
    38,
    40,
    31,
    94,
    57,
    69,
    105,
    122,
    55,
    30,
    45,
    39,
    68,
    54,
    67,
    70,
    16,
    37,
    40,
    36,
    17,
    22,
    47,
    37,
    31,
    50,
    78,
    48,
    60,
    172,
    187,
    15,
    10,
    103,
    30,
    57,
    38,
    20,
    93,
    277,
    19,
    37,
    19,
    7,
    7,
    2,
    31,
    33,
    43,
    8,
    41,
    11,
    10,
    14,
    6,
    21,
    16,
    15,
    3,
    6,
    4,
    6,
    10,
    18,
    3,
    2,
    1,
    3,
    5,
    10,
    5,
    5,
    6,
    3,
    6,
    13,
    8,
    14,
    7,
    4,
    5,
    3,
    18,
    9,
    15,
    21,
    15,
]

# ICU data (prev / million pop), provided by the country
icu_times = [
    71,
    72,
    73,
    74,
    75,
    76,
    77,
    78,
    79,
    80,
    81,
    82,
    83,
    84,
    85,
    86,
    87,
    88,
    89,
    90,
    91,
    92,
    93,
    94,
    95,
    96,
    97,
    98,
    99,
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
    169,
    170,
    171,
    172,
    173,
    174,
    175,
    176,
    177,
    178,
    179,
    180,
    181,
    182,
    183,
    184,
    185,
    186,
    187,
    188,
    189,
    190,
    191,
    192,
    193,
    194,
    195,
    196,
    197,
    198,
    199,
    200,
    201,
    202,
    203,
]
icu_counts = [
    2,
    3,
    4,
    5,
    9,
    12,
    12,
    15,
    20,
    26,
    37,
    46,
    57,
    64,
    45,
    45,
    54,
    73,
    73,
    94,
    94,
    102,
    105,
    108,
    99,
    99,
    102,
    92,
    76,
    72,
    69,
    72,
    66,
    66,
    60,
    56,
    56,
    51,
    49,
    46,
    45,
    43,
    43,
    42,
    41,
    36,
    36,
    37,
    36,
    40,
    36,
    37,
    31,
    27,
    28,
    24,
    22,
    19,
    18,
    18,
    18,
    20,
    16,
    16,
    16,
    14,
    13,
    13,
    13,
    11,
    11,
    10,
    9,
    9,
    9,
    8,
    8,
    8,
    8,
    8,
    9,
    9,
    8,
    6,
    6,
    6,
    6,
    5,
    5,
    6,
    6,
    5,
    5,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    3,
    3,
    3,
    2,
    3,
    2,
    2,
    2,
    2,
    2,
    4,
    4,
    4,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    4,
    6,
    5,
    5,
    3,
    1,
    2,
    3,
    4,
]

TARGET_OUTPUTS = [
    {
        "output_key": "notifications",
        "years": notification_times,
        "values": notification_counts,
        "loglikelihood_distri": "negative_binomial",
        "time_weights": list(range(1, len(notification_times) + 1)),
    },
    {
        "output_key": "prevXlateXclinical_icuXamong",
        "years": icu_times,
        "values": icu_counts,
        "loglikelihood_distri": "negative_binomial",
        "time_weights": list(range(1, len(icu_times) + 1)),
    },
]

MULTIPLIERS = {
    "prevXlateXclinical_icuXamong": 32364904.0
}  # to get absolute pop size instead of proportion
