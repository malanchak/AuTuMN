from copy import deepcopy

import pytest
from summer.model import StratifiedModel

from apps import mongolia, covid_19, marshall_islands
from autumn.tool_kit.utils import merge_dicts


@pytest.mark.local_only
@pytest.mark.parametrize("region", covid_19.REGION_APPS)
def test_run_models_partial(verify, region):
    """
    Smoke test: ensure we can build and run each default model with nothing crashing.
    Does not include scenarios, plotting, etc.
    """
    region_app = covid_19.get_region_app(region)
    ps = deepcopy(region_app.params["default"])
    # Only run model for ~2 epochs.
    ps["end_time"] = ps["start_time"] + 2
    model = region_app.build_model(ps)
    verify_model(verify, model, f"test_run_models_partial-model-{region}")
    model.run_model()
    verify(model.outputs, f"test_run_models_partial-outputs-{region}")


@pytest.mark.local_only
@pytest.mark.parametrize("region", covid_19.REGION_APPS)
def test_build_scenario_models(verify, region):
    """
    Smoke test: ensure we can build the each model with nothing crashing.
    """
    region_app = covid_19.get_region_app(region)
    for idx, scenario_params in enumerate(region_app.params["scenarios"].values()):
        default_params = deepcopy(region_app.params["default"])
        params = merge_dicts(scenario_params, default_params)
        params = {**params, "start_time": region_app.params["scenario_start_time"]}
        model = region_app.build_model(params)
        assert type(model) is StratifiedModel
        verify_model(verify, model, f"test_build_scenario_models-{idx}-model-{region}")


def verify_model(verify, model: StratifiedModel, key: str):
    """
    Model serializer - transform all relevant model info into basic Python data structures
    """
    t_flows_df = model.transition_flows
    flow_implement = t_flows_df.implement.max()
    mask = t_flows_df["implement"] == flow_implement
    t_flows_imp_df = t_flows_df[mask]
    t_flows = list(t_flows_imp_df.T.to_dict().values())
    d_flows_df = model.death_flows
    flow_implement = d_flows_df.implement.max()
    mask = d_flows_df["implement"] == flow_implement
    d_flows_imp_df = d_flows_df[mask]
    d_flows = list(d_flows_imp_df.T.to_dict().values())

    verify(model.entry_compartment, f"{key}-entry_compartment")
    verify(model.birth_approach, f"{key}-birth_approach")
    verify(model.infectious_compartment, f"{key}-infectious_compartment")
    verify(model.infectiousness_levels, f"{key}-infectiousness_levels")
    verify(model.infectiousness_multipliers, f"{key}-infectiousness_multipliers")
    verify(model.initial_conditions, f"{key}-initial_conditions")
    verify(model.starting_population, f"{key}-starting_population")
    verify(model.times, f"{key}-times")
    verify(model.all_stratifications, f"{key}-all_stratifications")
    verify(model.initial_conditions, f"{key}-initial_conditions")
    # verify(t_flows, f"{key}-transition-flows")
    verify(d_flows, f"{key}-death-flows")
    verify(model.requested_flows, f"{key}-requested_flows")
    verify(list(model.adaptation_functions.keys()), f"{key}-adaptation_functions")
    verify(
        None if model.mixing_matrix is None else model.mixing_matrix.tolist(),
        f"{key}-mixing_matrix",
    )
    verify(model.dynamic_mixing_matrix, f"{key}-dynamic_mixing_matrix")


@pytest.mark.run_models
@pytest.mark.github_only
@pytest.mark.parametrize("region", covid_19.REGION_APPS)
def test_run_models_full(region):
    """
    Smoke test: ensure our models run to completion without crashing.
    This takes ~30s per model.
    """
    region_app = covid_19.get_region_app(region)
    region_app.run_model()
