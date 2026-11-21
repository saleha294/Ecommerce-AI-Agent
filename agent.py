# agent.py
# The orchestrator — sits between the user, the LLM, and the database tools.
# It decides which tool to call based on what Gemini asks for, runs it, and
# sends the results back to get the final answer.

from llm import ask_llm, continue_interaction
from tool_registry import registry
from errors import ToolError


# Runs the full agent loop for a single user prompt.
# Handles both tool-use responses (function_call) and direct text responses from Gemini.
def agent(user_prompt):

    result = ask_llm(user_prompt)

    # Goes at 5 tool calls per question — prevents an infinite loop if Gemini keeps
    # requesting tools without ever producing a final text answer.
    for _ in range(5):

        # Gemini answered directly — return immediately.
        if result["kind"] == "text":
            return result["text"]

        # Gemini wants to use a tool — look it up in the registry.
        function_name = result["function_call"]["name"]
        

        if function_name not in registry:
            raise ToolError(
                f"Gemini requested tool '{function_name}' but it is not registered."
            )

        function = registry[function_name]
        arguments = result["function_call"]["arguments"]
        # DEBUG: uncomment to see which tool Gemini called and with what arguments
        # print("TOOL CALLED:", function_name, arguments)

        

        # Run the tool — wrap errors so the caller always gets a clean ToolError.
        try:
            database_result = function(**arguments)
        except TypeError as e:
            raise ToolError(
                f"Tool '{function_name}' was called with unexpected arguments: {e}"
            )
        except Exception as e:
            raise ToolError(
                f"Tool '{function_name}' failed during execution: {e}"
            )

        # Send the tool result back and get the next response — text or another tool call.
        result = continue_interaction(database_result, result)

    # Exited the loop without a text answer — Gemini kept requesting tools past the cap.
    if result["kind"] == "text":
        return result["text"]

    # DEBUG: uncomment to see which tool was last called before hitting the cap
    # print("TOOL CALLED:", function_name, arguments)

    raise ToolError("Too many tool calls in one question.")
