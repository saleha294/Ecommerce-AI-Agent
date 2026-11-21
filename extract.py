# extract. py
#extract api response

import requests


def get_products_data():
    response = requests.get('https://dummyjson.com/products?limit=0') #get the response

    product_data = response.json()
    
    # DEBUG: uncomment to see products API response status code
    # print(response.status_code)

    #print(product_data)

    return product_data

def get_users_data():
    response = requests.get('https://dummyjson.com/users?limit=0')
    # DEBUG: uncomment to see users API response status code
    # print(response.status_code)
    return response.json()


def get_carts_data():
    response = requests.get('https://dummyjson.com/carts?limit=0')
    # DEBUG: uncomment to see carts API response status code
    # print(response.status_code)
    return response.json()
