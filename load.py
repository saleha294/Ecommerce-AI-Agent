from database import get_database_connection


def load_product_data(cleaned_data):
    connection = get_database_connection()

    if not connection:
        # DEBUG: uncomment to see database connection failure in load
        # print("Database connection failed.")
        return

    # DEBUG: uncomment to see successful database connection in load
    # print("Database connection successful.")

    cursor = connection.cursor()

    sql_query = """
    INSERT INTO products
    (product_id, title, description, category, price)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (product_id) DO UPDATE
    SET title = EXCLUDED.title,
        description = EXCLUDED.description,
        category = EXCLUDED.category,
        price = EXCLUDED.price

        """

        
    for product in cleaned_data:
        cursor.execute(
            sql_query,
            (
                product["product_id"],
                product["title"],
                product["description"],
                product["category"],
                product["price"]
            )
        )

    connection.commit()

    cursor.close()
    connection.close()

    # DEBUG: uncomment to see products load confirmation
    # print("Data loaded successfully.")


def load_customers(rows):
    connection = get_database_connection()
    if not connection:
        return
    cursor = connection.cursor()
    sql = """
        INSERT INTO customers (customer_id, name, city, email)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (customer_id) DO UPDATE
        SET name = EXCLUDED.name, city = EXCLUDED.city, email = EXCLUDED.email
    """
    for r in rows:
        cursor.execute(sql, (r["customer_id"], r["name"], r["city"], r["email"]))
    connection.commit()
    cursor.close()
    connection.close()
    # DEBUG: uncomment to see customers load confirmation
    # print("Customers loaded.")


def load_orders(rows):
    connection = get_database_connection()
    if not connection:
        return
    cursor = connection.cursor()
    sql = """
        INSERT INTO orders (order_id, customer_id)
        VALUES (%s, %s)
        ON CONFLICT (order_id) DO UPDATE
        SET customer_id = EXCLUDED.customer_id
    """
    for r in rows:
        cursor.execute(sql, (r["order_id"], r["customer_id"]))
    connection.commit()
    cursor.close()
    connection.close()
    # DEBUG: uncomment to see orders load confirmation
    # print("Orders loaded.")


def load_order_items(rows):
    connection = get_database_connection()
    if not connection:
        return
    cursor = connection.cursor()
    sql = """
        INSERT INTO order_items (order_id, product_id, quantity)
        VALUES (%s, %s, %s)
        ON CONFLICT (order_id, product_id) DO UPDATE
        SET quantity = EXCLUDED.quantity
        
    """
    for r in rows:
        cursor.execute(sql, (r["order_id"], r["product_id"], r["quantity"]))
    connection.commit()
    cursor.close()
    connection.close()
    # DEBUG: uncomment to see order items load confirmation
    # print("Order items loaded.")