import json

def load_config():
    """Load the main JSON config file."""
    with open("config.json", "r") as f:
        return json.load(f)

def get_store_config(config, store_type, product_url=None):
    """
    Extract store-specific configuration.
    Includes account info, product URL, payment, and shipping info.
    """
    store_config = {
        "email": config["email"],
        "password": config["password"],
        "account_name": config.get("account_name"),
        "headless": config.get("headless", False),
        "place_order": config.get("place_order", False),
        "refresh_interval": config.get("refresh_interval", 10)
    }

    # Use provided URL or fall back to config
    if product_url:
        store_config["product_url"] = product_url
    else:
        url_key = f"{store_type}_product_url"
        if url_key in config:
            store_config["product_url"] = config[url_key]

    # Add payment info
    if "card" in config:
        store_config.update({
            "card_number": config["card"]["number"],
            "card_exp": config["card"]["exp"],
            "card_cvv": config["card"]["cvv"]
        })

    # Add shipping info
    if "shipping" in config:
        store_config.update({
            "full_name": config["shipping"]["name"],
            "address": config["shipping"]["address"],
            "city": config["shipping"]["city"],
            "state": config["shipping"]["state"],
            "zip": config["shipping"]["zip"],
            "phone": config["shipping"]["phone"]
        })

    return store_config


# ==============================
# Additional fields for your bot
# ==============================

def get_bot_config(config):
    """
    Return bot-specific settings:
    - TARGET_PRODUCTS: list of product keywords to buy
    - PRIORITY_SITES: list of sites in order of priority
    """
    return {
        "TARGET_PRODUCTS": config.get("target_products", ["Elite Trainer Box", "Booster Bundle"]),
        "PRIORITY_SITES": config.get("priority_sites", ["walmart", "bestbuy", "target"])
    }
