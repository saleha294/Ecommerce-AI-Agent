#transform.py


def transform_product_data(untransformed_data):

    cleaned_product = []

    begin_process = untransformed_data["products"]

    for product in begin_process:
        
        transforming_product_data = {
            "product_id" : product.get("id"),
            "title" : product.get("title"),
            "description" : product.get("description"),
            "category" :  product.get("category"),
            "price" : product.get("price")

        }
        
        cleaned_product.append(transforming_product_data)

    #print(cleaned_product)

    return cleaned_product

def transform_customer_data(untransformed_data):

    cleaned_customers = []

    begin_process = untransformed_data["users"]

    for user in begin_process:

        transforming_customer_data = {
            "customer_id": user.get("id"),
            "name": f'{user.get("firstName")} {user.get("lastName")}',
            "city": user.get("address", {}).get("city"),
            "email": user.get("email")
        }

        cleaned_customers.append(transforming_customer_data)

    return cleaned_customers


def transform_order_data(untransformed_data):

    cleaned_orders = []

    begin_process = untransformed_data["carts"]

    for cart in begin_process:

        transforming_order_data = {
            "order_id": cart.get("id"),
            "customer_id": cart.get("userId")
        }

        cleaned_orders.append(transforming_order_data)

    return cleaned_orders


def transform_order_item_data(untransformed_data):

    cleaned_order_items = []

    begin_process = untransformed_data["carts"]

    for cart in begin_process:

        for product in cart.get("products", []):

            transforming_order_item_data = {
                "order_id": cart.get("id"),
                "product_id": product.get("id"),
                "quantity": product.get("quantity")
            }

            cleaned_order_items.append(transforming_order_item_data)

    return cleaned_order_items