# llm.py
# Handles all communication with the Gemini API.
# ask_llm sends the initial user prompt; continue_interaction sends tool results back.

import requests
import json
import os
import time
from dotenv import load_dotenv
from errors import LLMBusyError, LLMConfigError, LLMResponseError

load_dotenv()

# Single source of truth for the model name — change here and both functions pick it up.
MODEL = "gemini-3-flash-preview"

URL = "https://generativelanguage.googleapis.com/v1beta/interactions"

TOOLS = [
    {
        "type": "function",
        "name": "search_products",
        "description": "A function to search all the products in the database based on any category asked by the user",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "The category used to search products, e.g. beauty"
                }
            },
            "required": ["category"]
        }
    },
    {
        "type": "function",
        "name": "get_customer_by_name",
        "description": "A function to search a customer the user asked for using the name provided by the user. Use this function whenever a user mentioned a customer's name.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "The name used to search and filter customers e.g Jennifer"
                }
            },
            "required": ["customer_name"]
        }
    },
    {
        "type": "function",
        "name": "get_orders_by_customer",
        "description": "Finds all orders placed by a customer, searched by name. Use when the user asks about a customer's orders or purchases.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "The name used to find a customer's orders, e.g. Emily"
                }
            },
            "required": ["customer_name"]
        }
    },
    {
        "type": "function",
        "name": "get_order_details",
        "description": "Gets the items inside one order (product, quantity, price), given an order ID. Use after finding an order ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The ID of the order to retrieve items for, e.g. 42"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "type": "function",
        "name": "get_order_total",
        "description": "Gets the total cost and item count of one order, given an order ID. Always use this for totals instead of adding numbers yourself.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The ID of the order to calculate the total for, e.g. 42"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "type": "function",
        "name": "get_top_products",
        "description": "Lists the best-selling products by units sold.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "How many top products to return, e.g. 5"
                }
            },
            "required": []
        }
    }
]

# Why: Google's error bodies come in different shapes (dict, list, or not JSON at all).
# This pulls out a readable message from any of them without crashing.
def _error_message(response):
    try:
        body = response.json()
    except ValueError:            # body isn't JSON at all
        return response.text

    if isinstance(body, list) and body:   # unwrap [ {...} ] into {...}
        body = body[0]

    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            return error.get("message", response.text)

    return response.text                  # fallback: raw text

    
# Sends a payload to the Gemini API with up to 3 retries.
# Handles transient failures (timeout, connection error, 429, 5xx) with backoff.
# Raises specific errors so the caller knows exactly what went wrong.
def send_request(payload):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise LLMConfigError("GEMINI_API_KEY is not set in environment variables.")
        #. Raising stops the function and hands an error upward, so main.py can decide what to do.
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    wait_times = [1, 2]  # seconds to wait before retry 2 and retry 3
    last_error = None

    for attempt in range(3):
        try:
            response = requests.post(URL, headers=headers, json=payload, timeout=30)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_error = e
            if attempt < 2:
                time.sleep(wait_times[attempt]) #i.e time.sleep(1) delay for a sec. Without it, the retries would fire instantly and hammer a server that is already overloaded. 
            continue

        # Permanent client errors — no point retrying these.
        if response.status_code in (400, 401, 403, 404):
            try:
               message = _error_message(response)
            except ValueError:
                message = response.text
            raise LLMConfigError(f"API returned {response.status_code}: {message}")

        # Transient(temporary) server errors or rate limiting(sending too many requests, slow down) — retry.
        if response.status_code == 429 or response.status_code >= 500:
            last_error = f"{response.status_code}: {_error_message(response)}"
            if attempt < 2:
                time.sleep(wait_times[attempt])
            continue

        # Any other non-200 we didn't anticipate.
        if response.status_code != 200:
            raise LLMConfigError(f"Unexpected status {response.status_code}: {response.text}")

        # Successful response — parse and return.
        try:
            return response.json()
        except ValueError:
            raise LLMResponseError("API returned a non-JSON response body.")

    raise LLMBusyError(
        f"Gemini API is unavailable after 3 attempts. Last error: {last_error}"
    )

#when all goes well, send_request returns Gemini’s whole response as a Python dictionary (the big package with steps, status and so on). It doesn’t pick out the useful part. That’s parse_response’s job.

# Extracts the meaningful step from Gemini's response body.
# Looks for a function_call step first (tool use), then model_output (text answer).
# Never relies on positional indexing — searches by step type instead.
def parse_response(body):
    steps = body.get("steps")
    if not steps:
        raise LLMResponseError("Response body contains no steps.")

    # Prefer function_call — the model wants to use a tool.
    for step in steps:
        if step.get("type") == "function_call":
            return {
                "kind": "function_call",
                "interaction_id": body["id"],
                "function_call": step
            }

    # Fall back to model_output — the model returned a direct text answer.
    for step in steps:
        if step.get("type") == "model_output":
            try:
                text = step["content"][0]["text"]
            except (KeyError, IndexError):
                raise LLMResponseError("model_output step has no readable text content.")
            return {"kind": "text", "text": text}

    raise LLMResponseError("Response contained no function_call or model_output step.")


# Sends the user's initial prompt to Gemini along with the available tools.
# Returns a parsed response dict with 'kind' set to either 'function_call' or 'text'.
def ask_llm(prompt):
    payload = {
        "model": MODEL,
        "input": prompt,
        "tools": TOOLS
    }

    body = send_request(payload)
    return parse_response(body)


# Sends a tool result back to Gemini and returns whatever parse_response gives back.
# This may be a final text answer or another function_call — the agent loop decides what to do next.
def continue_interaction(database_result, llm_response):
    payload = {
        "model": MODEL,
        "previous_interaction_id": llm_response["interaction_id"],
        "input": [
            {
                "type": "function_result",
                "name": llm_response["function_call"]["name"],
                "call_id": llm_response["function_call"]["id"],
                "result": [
                    {
                        "type": "text",
                        "text": json.dumps(database_result, default=str)
                    }
                ]
            }
        ]
    }

    body = send_request(payload)
    return parse_response(body)
