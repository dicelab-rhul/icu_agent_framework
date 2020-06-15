from json import dump, load

from icu_environment.icu_env import ICUEnvironment
from icu_agent.icu_agent import ICUManagerAgent
from icu_agent.icu_agent_mind import ICUTeleoreactiveMind


def save_global_state(environment: ICUEnvironment, file_path: str) -> None:
    global_state: dict = {
        "environment": dump_env_state(environment=environment),
        "agents": []
    }

    for agent in environment.get_agent_pool():
        agent_state: dict = dump_agent_state(agent=agent)
        global_state["agents"].append(agent_state)

    with open(file_path, "w") as o_f:
        dump(obj=global_state, fp=o_f)


def dump_env_state(environment: ICUEnvironment) -> dict:
    return {
        "hostname": environment.get_hostname(),
        "port": environment.get_port(),
        "event_generator_names": environment.get_event_generator_names(),
        "initial_state": environment.get_initial_state() # Note: this is the initial state, NOT the current state.
    }


def dump_agent_state(agent: ICUManagerAgent) -> dict:
    return {
        "id": agent.get_id(),
        "managed_generator": agent.get_managed_group(),
        "env_hostname": agent.get_env_hostname(),
        "env_port": agent.get_env_port(),
        "mind": dump_agent_mind(mind=agent.get_mind())
    }


def dump_agent_mind(mind: ICUTeleoreactiveMind) -> dict:
    return {
        "name": mind.__class__.__name__,
        "id": mind.get_id(),
        "goal": mind.get_working_memory().get_goal().dump(),
        "belief": mind.get_working_memory().get_belief().dump(),
        "storage_info": mind.get_storage().get_storage_type()
    }


def load_global_state(file_path: str) -> ICUEnvironment:
    with open(file_path, "r") as i_f:
        global_state: dict = load(fp=i_f)

    return ICUEnvironment.from_state(state=global_state)
