__author__ = "cloudstrife9999"

from icu_agent.icu_agent import ICUManagerAgent, ICUWorkerAgentSensor, ICUWorkerAgentActuator
from icu_agent.icu_agent_mind import ICUTeleoreactiveMind, ICUScaleMind, ICUPumpMind, ICUTrackingWidgetMind, ICUWarningLightMind
from icu_agent.icu_memory import ICUMindInternalStorage
from icu_exceptions import ICUException


def build_manager_agent(managed_group: str, managed_group_info: dict, env_interface: tuple) -> ICUManagerAgent:
    mind: ICUTeleoreactiveMind = build_manager_agent_mind(managed_group=managed_group, managed_group_info=managed_group_info)
    
    return ICUManagerAgent(mind, [ICUWorkerAgentActuator()], [ICUWorkerAgentSensor()], env_interface[0], env_interface[1])

def build_manager_agent_mind(managed_group: str, managed_group_info: dict) -> ICUTeleoreactiveMind:
    storage: ICUMindInternalStorage = ICUMindInternalStorage()

    if managed_group == "scales":
        return ICUScaleMind(managed_group=managed_group, managed_group_info=managed_group_info, storage=storage)
    elif managed_group == "pumps_and_tanks":
        return ICUPumpMind(managed_group=managed_group, managed_group_info=managed_group_info, storage=storage)
    elif managed_group == "tracking_widget":
        return ICUTrackingWidgetMind(managed_group=managed_group, managed_group_info=managed_group_info, storage=storage)
    elif managed_group == "warning_lights":
        return ICUWarningLightMind(managed_group=managed_group, managed_group_info=managed_group_info, storage=storage)
    else:
        raise ICUException("Unsupported generator: {}.".format(managed_group))