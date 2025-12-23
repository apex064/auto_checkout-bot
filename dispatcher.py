# dispatcher.py
import asyncio
from bots import TargetBot, WalmartBot, BestBuyBot
from utils.config import load_config, get_store_config
from utils.logger import logger
import re

class BotDispatcher:
    def __init__(self):
        self.config = load_config()
        self.bots = {
            'target': TargetBot,
            'walmart': WalmartBot,
            'bestbuy': BestBuyBot
        }

    def identify_store(self, url):
        """Identify which store the URL belongs to"""
        url_lower = url.lower()
        if 'target.com' in url_lower:
            return 'target'
        elif 'walmart.com' in url_lower:
            return 'walmart'
        elif 'bestbuy.com' in url_lower:
            return 'bestbuy'
        else:
            return None

    async def dispatch(self, url):
        """Dispatch a single URL to the correct store bot"""
        store_type = self.identify_store(url)
        if not store_type:
            logger.error(f"Unsupported store URL: {url}")
            return False

        # Ensure URL is a valid product page
        product_url = await self._resolve_product_url(url, store_type)
        if not product_url:
            logger.warning(f"Could not resolve product URL for {url}")
            return False

        logger.info(f"Dispatching to {store_type} bot for URL: {product_url}")

        # Get store-specific config
        store_config = get_store_config(self.config, store_type, product_url)
        if not store_config:
            logger.error(f"No configuration found for {store_type}")
            return False

        # Initialize and run the appropriate bot
        bot_class = self.bots.get(store_type)
        if not bot_class:
            logger.error(f"No bot class found for store type: {store_type}")
            return False

        try:
            bot = bot_class(store_config)
            # Run the blocking bot in a background thread
            success = await asyncio.to_thread(bot.run)
            return success
        except Exception as e:
            logger.error(f"Error running {store_type} bot for URL {product_url}: {e}")
            return False

    async def dispatch_multiple(self, urls):
        """Dispatch multiple URLs to their respective store bots concurrently"""
        tasks = [self.dispatch(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return list(zip(urls, results))

    # -----------------------------
    # Helper functions
    # -----------------------------
    async def _resolve_product_url(self, url, store_type):
        """
        If URL is a search URL or general page, attempt to resolve to the actual product page.
        Currently basic logic: if it looks like a search, return the first matching SKU/product.
        For exact product URLs, just return the URL.
        """
        # Simple heuristic: exact product pages contain /p/ for Target, /ip/ for Walmart, /site/ for BestBuy
        url_lower = url.lower()
        if store_type == 'target' and '/p/' in url_lower:
            return url
        elif store_type == 'walmart' and '/ip/' in url_lower:
            return url
        elif store_type == 'bestbuy' and '/site/' in url_lower:
            return url

        # Otherwise, return the URL as-is (future: can implement scraping logic)
        return url
