#tool_registry.py


from agent_database_tools import search_products
from agent_database_tools import get_customer_by_name
from agent_database_tools import get_orders_by_customer
from agent_database_tools import get_order_details
from agent_database_tools import get_order_total
from agent_database_tools import get_top_products

registry = {
    
    "search_products" : search_products,
    "get_customer_by_name" : get_customer_by_name,
    "get_orders_by_customer" : get_orders_by_customer,
    "get_order_details" : get_order_details,
    "get_order_total" : get_order_total,
    "get_top_products" : get_top_products

}