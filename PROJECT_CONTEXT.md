# Project Context

Reference notes for this project: what exists, where it lives, and what is known to be incomplete. Written so I (or an AI assistant) can pick the project up after a break without re-explaining it. For the overview see `README.md`, and for the story of what broke see `DEBUGGING_JOURNEY.md`.

**Run:** `python main.py`
**Needs:** a `.env` file with `GEMINI_API_KEY` and the database connection variables read in `database.py`. `.env` must stay in `.gitignore`.
**Model:** `gemini-3-flash-preview`, via the `/v1beta/interactions` endpoint (the name lives in one `MODEL` constant in `llm.py`).

## What happens when a question is asked

1. `main.py` reads the question and calls `agent()`.
2. `agent.py` sends it to Gemini through `ask_llm` in `llm.py`.
3. Gemini either answers in text or asks for one of the registered tools.
4. `agent.py` looks the tool up in `registry`, runs it, and sends the result back with `continue_interaction`.
5. Steps 3 and 4 repeat up to 5 times. When Gemini replies with text, that text is returned to `main.py`.

## Files

| File | Job |
|---|---|
| `main.py` | Entry point. Catches errors and prints a readable message for each type |
| `agent.py` | The loop: ask Gemini, run the requested tool, send the result back. Capped at 5 rounds |
| `llm.py` | All Gemini communication. `send_request` (30s timeout, 3 attempts, 1s then 2s wait), `parse_response` (finds steps by `type`, never by position), `ask_llm`, `continue_interaction`, and the `tools` list Gemini reads |
| `agent_database_tools.py` | The SQL functions the agent can call |
| `tool_registry.py` | Maps tool names to those functions (`registry`) |
| `errors.py` | Custom exceptions |
| `extract.py` | Fetches data from the DummyJSON API |
| `transform.py` | Cleans and reshapes the raw data |
| `load.py` | Inserts data into PostgreSQL |
| `database.py` | Database connection |

## Schema

| Table | Columns |
|---|---|
| `customers` | customer_id, name, city, email |
| `products` | product_id, name, description, price, title, category |
| `orders` | order_id, customer_id, amount, status |
| `order_items` | order_id, product_id, quantity |

Links: `orders.customer_id` to `customers.customer_id`, and `order_items.product_id` to `products.product_id`.

## Agent tools

| Tool | Parameters | Example question |
|---|---|---|
| `search_products` | category | "Show me beauty products" |
| `get_customer_by_name` | customer_name | "Find customer Emily" |
| `get_orders_by_customer` | customer_name | "What orders did Emily place?" |
| `get_order_details` | order_id | "What's in order 1?" |
| `get_order_total` | order_id | "What's the total of order 104?" |
| `get_top_products` | limit (optional, default 5, max 20) | "Top 3 best-selling products?" |

**Adding a tool takes three changes:** the function in `agent_database_tools.py`, an entry in `registry`, and a definition in the `tools` list in `ask_llm`. Gemini only knows about tools in that list and chooses between them by reading their descriptions, so the wording of a description is part of the behaviour.

## Errors

| Error | Meaning | Retried? |
|---|---|---|
| `LLMBusyError` | Timeout, 429 or 5xx after 3 attempts | Yes, 3 attempts |
| `LLMRequestError` | 400/401/403/404, missing key, bad model name | No |
| `LLMResponseError` | Response was not JSON, or had nothing usable | No |
| `ToolError` | Unknown tool, bad arguments, database failure, or more than 5 tool rounds | No |

All inherit from `AgentError`. `llm.py` raises and never prints; `main.py` decides what the user sees.

## Debug conventions

- `# DEBUG:` marks a commented-out print. Search for it to find them all.
- `# KEEP:` marks an error message that stays on (for example the `print(e)` in `database.py` that says why a connection failed).
- The `[debug]` line under `LLMBusyError` in `main.py` stays on. It shows whether the cause was a 503, a 429 or a timeout.

## Known limitations

These are decisions, not surprises.

- `orders.amount` and `orders.status` are null for every order. `load_orders` only inserts `order_id` and `customer_id`, and the source data has no status. Totals come from `get_order_total`.
- `orders` has no date column, so time-based questions are not possible.
- `order_items` has no price. Totals use current prices from `products`.
- `products.name` is null. Use `products.title`.
- 208 customers. The extract call uses `limit=0`, which returns everything. The Supabase table viewer pages at about 100 rows, which can look like missing data.
- `load_orders` and `load_order_items` return silently if the database connection fails.
- No backup model. Idea if 503s return: keep `PRIMARY_MODEL` and `BACKUP_MODEL` in `.env` and fall back after the primary fails. One open question is whether Gemini accepts a `previous_interaction_id` from a different model.
