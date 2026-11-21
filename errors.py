# errors.py
# Custom exception hierarchy for the agent pipeline.
# Using a shared parent (AgentError) lets main.py catch everything
# with one broad handler, or specific subclasses for targeted handling.


# Parent for all agent-related errors — catch this if you want to handle any failure.
class AgentError(Exception):
    pass


# Raised when the LLM API is temporarily unavailable or rate-limited.
# The caller should inform the user to try again later.
class LLMBusyError(AgentError):
    pass


# Raised when the request itself is malformed or rejected by the API
# (e.g. missing API key, bad model name, auth failure).
class LLMConfigError(AgentError):
    pass


# Raised when the API returns a response we cannot parse or make sense of.
class LLMResponseError(AgentError):
    pass


# Raised when the agent cannot find or successfully execute a database tool.
class ToolError(AgentError):
    pass
