from database import get_database_connection
from errors import ToolError

def search_products(category = "beauty"):
    connection = get_database_connection()

    if connection:
        # DEBUG: uncomment to see successful database connection confirmation
        # print("Database tool access successful.")
        pass
    else:
        return

    cursor = connection.cursor()

    sql_query = """
        SELECT product_id, title, description, price
        FROM products
        WHERE category =  %s
    """

    cursor.execute(sql_query, (category,))

    rows = cursor.fetchall()

    products_result = []

    for row in rows:
        product = {
            "product_id": row[0],
            "title":  row[1],
            "description":  row[2],
            "price":  row[3]

        }

        products_result.append(product)

    cursor.close()
    connection.close()

    return products_result


def get_customer_by_name(customer_name): 
    
    connection = get_database_connection()
    
    if connection:
        # DEBUG: uncomment to see successful database connection confirmation
        # print("Database tool access successful.")
        pass
    else:
        return
            
    cursor = connection.cursor()

    sql_query = """
        SELECT customer_id, name, city, email 
        FROM customers
        WHERE name ILIKE %s
    """

    cursor.execute(sql_query, ("%" + customer_name + "%",))

    rows = cursor.fetchall()

    customer_name_result = []

    for row in rows:
        customer = {
            "customer_id": row[0],
            "name":  row[1],
            "city":  row[2],
            "email":  row[3]

        }
        customer_name_result.append(customer)

    cursor.close()
    connection.close()

    return customer_name_result


# Fetches all orders belonging to a customer searched by name.
# Joins orders and customers so the result is self-contained and readable.
def get_orders_by_customer(customer_name):
    connection = get_database_connection()

    if not connection:
        raise ToolError("Database connection failed in get_orders_by_customer.")

    cursor = connection.cursor()

    sql_query = """
        SELECT o.order_id, c.name
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE c.name ILIKE %s
    """

    cursor.execute(sql_query, ("%" + customer_name + "%",))

    rows = cursor.fetchall()

    orders_result = []

    for row in rows:
        order = {
            "order_id": row[0],
            "customer_name": row[1]
        }
        orders_result.append(order)

    cursor.close()
    connection.close()

    return orders_result

# Fetches the individual line items inside a single order.
# Joins order_items with products so each row shows what was bought, how many, and at what cost.
def get_order_details(order_id):
    connection = get_database_connection()

    if not connection:
        raise ToolError("Database connection failed in get_order_details.")

    cursor = connection.cursor()

    sql_query = """
        SELECT p.title, oi.quantity, p.price, oi.quantity * p.price AS line_total
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
    """

    cursor.execute(sql_query, (order_id,))

    rows = cursor.fetchall()

    order_details_result = []

    for row in rows:
        item = {
            "title": row[0],
            "quantity": row[1],
            "price": row[2],
            "line_total": row[3]
        }
        order_details_result.append(item)

    cursor.close()
    connection.close()

    return order_details_result

# Calculates the total cost and item count for a single order.
# Uses SUM in SQL rather than summing in Python so the database does the arithmetic once.
def get_order_total(order_id):
    connection = get_database_connection()

    if not connection:
        raise ToolError("Database connection failed in get_order_total.")

    cursor = connection.cursor()

    sql_query = """
        SELECT SUM(oi.quantity * p.price), SUM(oi.quantity)
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
    """

    cursor.execute(sql_query, (order_id,))

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None or row[0] is None:
        return []

    return [{"order_id": order_id, "total": row[0], "item_count": row[1]}]


# Returns the best-selling products by units sold across all orders.
# Useful for understanding which products are most popular without scanning every order manually.
def get_top_products(limit=5):
    connection = get_database_connection()

    if not connection:
        raise ToolError("Database connection failed in get_top_products.")

    limit = max(1, min(limit, 20))

    cursor = connection.cursor()

    sql_query = """
        SELECT p.title, SUM(oi.quantity) AS total_sold
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.product_id, p.title
        ORDER BY total_sold DESC, p.title
        LIMIT %s
    """

    cursor.execute(sql_query, (limit,))

    rows = cursor.fetchall()

    top_products_result = []

    for row in rows:
        item = {
            "title": row[0],
            "total_sold": row[1]
        }
        top_products_result.append(item)

    cursor.close()
    connection.close()

    return top_products_result
