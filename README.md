# The ICU Agent Platform

The ICU agent platform is an agent framework based on a Python3.8 implementation of the [GOLEM](https://dl.acm.org/doi/10.1145/1619258.1619275) reference model for agents and the agent environment. It also further specialises the agent architecture with a [teleo-reactive](https://dl.acm.org/doi/abs/10.5555/1618595.1618602) decision making programming style. Such paradigm enables any agent that uses it to process incoming events from an environment object called ICU. This object can be thought of as an application whose display simulates NASA’s well known [MATB-II](https://matb.larc.nasa.gov/) system. ICU is also further connected to an eye-tracker. Agents in the platfrom environment monitor changes to the ICU display. If, combining GUI events with eye tracking events, the agents find that the user is required to attend to a particular part of the ICU’s display, they advise the user by annotating the display with useful user feedback.

## Basic structure

Updated diagrams coming soon (the current ones are outdated).

## The environment

The environment is the place where everything resides. It is home to a pool of agents, and the ICU application simulator. The environment is effectively the mediator between the agents and the application simulator. Every interaction between them passes through it. The components which are responsible for connecting the pool of agents and the application simulator are the [dispatcher](#the-dispatcher) and the feedback [listeners](#the-feedback-listeners).

### The enviroment configuration

The  environment, the application simulator, and the eye tracker rely on certain parameters to work properly. The configuration can be found in [config.json](https://github.com/dicelab-rhul/icu_agent_framework/blob/master/config.json).

### The application simulator

The `ICUApplicationSimulator` is a wrapper around the ICU system. It is responsible for starting it, and provides an immediate API to get events (see `get_event(self)`), and push feedback (see `push_feedback(self, feedback: dict)`).

### The agents

The environment is home to the so called `ICUManagerAgent`s which, on a high level, receive events from the environment, reason about them, and provide feedback to the environment when necessary. See [below](#the-agent-architecture) for further details on the agent architecture.

### The dispatcher

The dispatcher is a wrapper over a `Process` which continuously pulls events from the application simulator, decodes the event type, and forwards each event to its intended recipient(s). The wrapper class is `ICUEnvironmentDispatcher`, and its main function is `__pull_and_dispatch(self)`. The dispatcher itself is created in the `__init__()` method of the environment (see [below](#environment-life-cycle)).

### The feedback listeners

The feedback listeners are a list of wrappers over `Process`es which continuously wait for feedback from the pool of agents. Whenever a feedback is received, they forward it to the application simulator. The wrapper class is `ICUAgentListener`, and its main function is `__forward_feedback(self, agent_interface: socket)`. The listeners are created in the `__init__()` method of the environment (see [below](#environment-life-cycle)).

### Communication via socket

The agents, the dispatcher, and the feedback listeners all communicate via sockets. On a high level, the agents send data to the feedback listeners, and read data sent by the dispatcher. The dispatcher pulls (without using a socket) data from the application simulator (via `get_event()`), and sends data (via socket) to the various agents. Each feedback listeners reads data sent by a specific agent, and forwards such data to the application simulator (without using a socket). The `icu_socket_utils.py` module provides a quick interface for sending data through a socket (see `send_utf8_str(s: socket, content: str)`), and to read data from a socket (see `read_utf8_str(s: socket, read_timeout: int=-1)`). Currently, only utf-8 strings are supported. Therefore, whenever a complex object needs to be sent via socket, it mus be serialisable to a string. Most of the times, such complex object is a `dict`, and the serialisation consists of calling the `dumps(raw_dict)` method of the `json` module. When reading, the `dict` is reconstructed by means of the `loads(s)` method of the `json` module.

### Environment life cycle

1) The configuration is loaded.
2) The server socket (w.r.t. agents) is initialised.
3) The ICU application simulator is created and booted, together with the eye tracker.
4) For each event generator group (see config file) a new agent is spawned.
5) The agent listerner processes are created, one for each agent. They wait for feedback, and forward it to the ICU simulator
    - wait for feedback
    - send the received feedback to the ICU
6) The environment dispatcher is created, and put into a loop (see __pull_and_dispatch()):
    - pull an event
    - decode the event type
    - dispatch the event to its intended recipients
        - if the event comes from the eye tracker, or it is a highlight event, then it is broadcasted
        - otherwise, the event is only sent to the appropriate agent

## The agent architecture

An agent consists of a body (see `ICUManagerAgent`) which wraps a mind (see `ICUTeleoreactiveMind`, and its subclasses), a sensor, and an actuator. The sensor (see `ICUWorkerAgentSensor`) is used to fetch incoming perceptions from the environment (by means of wrapping the socket with the environment). The actuator (see `ICUWorkerAgentActuator`) is used to send feedback to the environemnt (again, by means wrapping the socket with the environment).

### The agent mind

The mind is the core component of an agent. Its core component is a working memory consisting of a belief (see `ICUBelief`, and its subclasses) and a goal (see `ICUMindGoal`). The agent mind is in a perpetual cycle of 4 primitives: `perceive()`, `revise()`, `decide()`, and `execute()`. Note that, as the body and the mind share the same process, the primitives are completely synchronous. The implementation differs depending on the group of event generators that the agent is supposed to manage. In general, `perceive()` is called by the agent body to provide the mind with new perceptions when they are available. In general, `revise()` performs a backup of the previous cycle perceptions, and uses the new ones to update the state of the mind belief. In general, `decide()` queries the mind belief, in order to either determine that feedback need to be provided, or nothing needs to be done (i.e., stay idle). In the former case, the feedback is constructed on the fly, and wrapped with a `FeedbackAction`. Finally, `execute()` kickstarts the execution of the `FeedbackAction`, if such action has been decided.

#### The mind belief

Each agent mind contains a working memory which wraps a belief. A mind belief represents the state of the event generators group that the agent is supposed to manage. It also contains the up-to-date position of the user eyes, a set of methods to update the state (used by `revise()`), and a set of methods to check whether the user needs to intervene (used by `decide()`). Each different subclass of `ICUTeleoreactiveMind` has a different kind of belief (which is always a subclass of `ICUBelief`).

#### The decide() primitive

`decide()` is implemented with a teleo-reactive paradigm in mind (no pun intended). The order of the rules is the following:

- If a warning shape is already displayed on the GUI, then stay idle.
- Else if (multiple rules to detect a widget that needs attention), then consider to send a feedback.
- Else, stay idle.

If an agent mind is "considering to send a feedback", it is simply going through a second set of teleo-reactive rules:

- If the user is noot looking at the problematic widget, then a feedback must be sent.
- Else if the grace period has expired, then a feedback must be sent.
- Else, stay idle.
