from summer.model import StratifiedModel
from autumn.constants import Compartment, BirthApproach
from autumn.tool_kit.scenarios import get_model_times_from_inputs


def build_model(params: dict) -> StratifiedModel:
    """
    Build the master function to run a simple SIR model
    Returns the final model with all parameters and stratifications
    """
    compartments = [
        Compartment.SUSCEPTIBLE,
        Compartment.INFECTIOUS,
        Compartment.RECOVERED,
    ]

    flows = [
        {
            "type": "infection_frequency",
            "parameter": "contact_rate",
            "origin": Compartment.SUSCEPTIBLE,
            "to": Compartment.INFECTIOUS,
        },
        {
            "type": "standard_flows",
            "parameter": "recovery_rate",
            "origin": Compartment.INFECTIOUS,
            "to": Compartment.RECOVERED,
        },
    ]

    integration_times = get_model_times_from_inputs(
        round(params["start_time"]), params["end_time"], params["time_step"]
    )

    init_conditions = {Compartment.INFECTIOUS: 1}

    sir_model = StratifiedModel(
        integration_times,
        compartments,
        init_conditions,
        params,
        flows,
        infectious_compartment=(Compartment.INFECTIOUS,),
        birth_approach=BirthApproach.NO_BIRTH,
        starting_population=1000000,
    )

    return sir_model
