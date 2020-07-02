from autumn.constants import Region
from apps.covid_19.calibration import base


def run_calibration_chain(max_seconds: int, run_id: int):
    base.run_calibration_chain(
        max_seconds, run_id, Region.CALABARZON, PAR_PRIORS, TARGET_OUTPUTS, mode="autumn_mcmc", _multipliers=MULTIPLIERS
    )

MULTIPLIERS = {
    "prevXlateXclinical_icuXamong": 16057300.0
}  # to get absolute pop size instead of proportion


PAR_PRIORS = [
    {
        "param_name": "contact_rate", 
        "distribution": "uniform", 
        "distri_params": [0.04, 0.06],
    },
    {
        "param_name": "start_time", 
        "distribution": "uniform", 
        "distri_params": [0.0, 40.0],
    },
    # Add extra params for negative binomial likelihood
    {
        "param_name": "notifications_dispersion_param",
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
]

# notification data:
notification_times = [
43,
44,
51,
53,
61,
62,
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
175,
]

notification_values = [
1,
1,
1,
1,
1,
1,
1,
2,
1,
3,
5,
4,
6,
9,
12,
9,
11,
16,
14,
21,
29,
28,
32,
20,
29,
29,
27,
37,
26,
22,
38,
38,
30,
29,
46,
40,
29,
37,
60,
35,
33,
24,
52,
40,
37,
24,
22,
23,
28,
28,
29,
11,
12,
20,
14,
16,
12,
13,
6,
25,
20,
20,
7,
14,
8,
18,
7,
9,
16,
20,
12,
9,
9,
23,
27,
6,
15,
12,
12,
41,
18,
22,
24,
67,
41,
25,
28,
11,
20,
13,
3,
34,
18,
42,
18,
29,
9,
18,
31,
10,
13,
20,
19,
14,
37,
32,
60,
62,
41,
11,
50,
77,
40,
32,
84,
3,
]

TARGET_OUTPUTS = [
    {
        "output_key": "notifications",
        "years": notification_times,
        "values": notification_values,
        "loglikelihood_distri": "negative_binomial",
    },
]
