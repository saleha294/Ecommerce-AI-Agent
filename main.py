from extract import get_products_data, get_users_data, get_carts_data
from transform import (
    transform_product_data,
    transform_customer_data,
    transform_order_data,
    transform_order_item_data,
)
from load import load_product_data, load_customers, load_orders, load_order_items
from agent import agent
from errors import LLMBusyError, LLMConfigError, AgentError

# --- Products (already loaded, skipped for now) ---
# product_data = get_products_data()
# transformed_product_data = transform_product_data(product_data)
# load_data(transformed_product_data)

# --- Customers ---
#users_data = get_users_data()
#transformed_customers = transform_customer_data(users_data)
#load_customers(transformed_customers)

# --- Orders and order items (one fetch, two transforms) ---
#carts_data = get_carts_data()

#transformed_orders = transform_order_data(carts_data)
#load_orders(transformed_orders)

#transformed_order_items = transform_order_item_data(carts_data)
#load_order_items(transformed_order_items)


# Entry point — takes the user's question and prints the agent's answer.
# Catches known error types and prints a short, readable message for each.
user_prompt = input("Ask any question: ")

try:
    final_answer = agent(user_prompt)
    print(final_answer)

except LLMBusyError as e:
    print("The AI service is currently unavailable due to high demand. Please try again in a moment.")
    print("[debug]", e)

except LLMConfigError as e:
    print(f"There was a problem with the request to the AI service: {e}")

except AgentError as e:
    print(f"Something went wrong while processing your question: {e}")
