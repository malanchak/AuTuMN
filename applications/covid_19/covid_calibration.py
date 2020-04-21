import os

from autumn.calibration import Calibration
from autumn.tool_kit.utils import find_first_index_reaching_cumulative_sum
from autumn.tool_kit.params import load_params
from autumn.db import get_iso3_from_country_name

from applications.covid_19.covid_model import build_covid_model, input_database
from applications.covid_19.JH_data.process_JH_data import read_john_hopkins_data_from_csv

from numpy import linspace

FILE_DIR = os.path.dirname(os.path.abspath(__file__))


def run_calibration_chain(max_seconds: int, run_id: int, country: str, par_priors, target_outputs, mode='lsm',
                          _start_time_range=None):
    """
    Run a calibration chain for the covid model

    num_iters: Maximum number of iterations to run.
    available_time: Maximum time, in seconds, to run the calibration.
    mode is either 'lsm' or 'autumn_mcmc'
    """
    print(f"Preparing to run covid model calibration for country {country}")
    params = load_params(FILE_DIR, application=country.lower())
    scenario_params = params["scenarios"]
    sc_start_time = params["scenario_start_time"]
    # params["default"]["country"] = country
    params["default"]["iso3"] = get_iso3_from_country_name(input_database, country) if country != 'Victoria' else 'VIC'

    calib = Calibration(
        "covid_" + country,
        build_covid_model,
        par_priors,
        target_outputs,
        MULTIPLIERS,
        run_id,
        scenario_params,
        sc_start_time,
        model_parameters=params["default"],
        start_time_range=_start_time_range
    )
    print("Starting calibration.")
    calib.run_fitting_algorithm(
        run_mode=mode,
        n_iterations=100000,
        n_burned=0,
        n_chains=1,
        available_time=max_seconds,
    )
    print(f"Finished calibration for run {run_id}.")


def get_priors_and_targets(country, data_type="confirmed", start_after_n_cases=1):
    """
    Automatically build prior distributions and calibration targets using John Hopkins data
    :param country: the country name
    :param data_type: either "confirmed" or "deaths"
    :return:
    """

    # for JH data, day_1 is '1/22/20', that is 22 Jan 2020
    n_daily_cases = read_john_hopkins_data_from_csv(data_type, country=country.title())

    # get the subset of data points starting after 1st case detected
    index_start = find_first_index_reaching_cumulative_sum(n_daily_cases, start_after_n_cases)
    data_of_interest = n_daily_cases[index_start:]

    start_day = index_start + 22  # because JH data starts 22/1

    PAR_PRIORS = [
        {"param_name": "contact_rate", "distribution": "uniform", "distri_params": [0.1, 4.0]},
        {
            "param_name": "start_time",
            "distribution": "uniform",
            "distri_params": [-30, start_day - 1],
        },
    ]

    output_key = {"confirmed": "notifications", "deaths": "infection_deathsXall"}

    assert data_type in output_key

    TARGET_OUTPUTS = [
        {
            "output_key": output_key[data_type],
            "years": linspace(
                start_day, start_day + len(data_of_interest) - 1, num=len(data_of_interest)
            ),
            "values": data_of_interest,
            "loglikelihood_distri": "poisson",
        }
    ]

    return PAR_PRIORS, TARGET_OUTPUTS


MULTIPLIERS = {}
