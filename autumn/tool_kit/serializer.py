from summer.model import StratifiedModel


def serialize_model(model: StratifiedModel) -> dict:
    """
    Model serializer - transform all relevant model info into basic Python data structures
    """
    return {
        "settings": {
            "entry_compartment": model.entry_compartment,
            "birth_approach": model.birth_approach,
            "infectious_compartment": model.infectious_compartment,
        },
        "infectiousness": {
            "infectiousness_levels": model.infectiousness_levels,
            "infectiousness_multipliers": model.infectiousness_multipliers,
        },
        "start": {
            "initial_conditions": model.initial_conditions,
            "starting_population": model.starting_population,
            "times": model.times,
        },
        "stratifications": model.all_stratifications,
        "parameters": serialize_params(model.parameters),
        "flows": {
            "transition": model.transition_flows,
            "death": model.death_flows,
            "requested": model.requested_flows,
        },
        "adaptation_functions": list(model.adaptation_functions.keys()),
        "mixing": {
            "mixing_matrix": None if model.mixing_matrix is None else model.mixing_matrix.tolist(),
            "dynamic_mixing_matrix": model.dynamic_mixing_matrix,
        },
    }


def serialize_params(ps):
    params = {}
    for k, v in ps.items():
        try:
            params[k] = v.tolist()
        except:
            params[k] = v
    return params
