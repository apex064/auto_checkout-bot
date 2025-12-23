import discord
import re
from utils.logger import logger
from utils.config import load_config, get_bot_config

# Load config
config = load_config()
bot_config = get_bot_config(config)
TARGET_PRODUCTS = bot_config["TARGET_PRODUCTS"]  # e.g., ["Elite Trainer Box", "Booster Bundle"]
PRIORITY_SITES = bot_config["PRIORITY_SITES"]    # e.g., ["walmart", "bestbuy", "target"]

class DiscordBot:
    def __init__(self, token, dispatcher):
        self.token = token
        self.dispatcher = dispatcher
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.messages = True
        self.client = discord.Client(intents=self.intents)

        @self.client.event
        async def on_ready():
            logger.info(f'Logged in as {self.client.user}')

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return  # Ignore bot's own messages

            content = message.content
            logger.info(f"Received message: {content}")

            # -----------------------------
            # 1️⃣ Handle !buy command
            # -----------------------------
            if content.startswith('!buy'):
                user_input = content.split(' ')[1] if len(content.split(' ')) > 1 else None
                if user_input:
                    if self._matches_target(user_input):
                        logger.info(f"Manual buy command for target product: {user_input}")
                        success = await self.dispatcher.dispatch(user_input)
                        if success:
                            await message.channel.send(f"✅ Purchase process started for: {user_input}")
                        else:
                            await message.channel.send(f"❌ Could not process product: {user_input}")
                    else:
                        await message.channel.send("❌ This product is not in your target products list.")
                else:
                    await message.channel.send("Please provide a product URL or SKU: !buy <product>")
                return

            # -----------------------------
            # 2️⃣ Keyword Scraping for Target Products
            # -----------------------------
            if self._contains_target_keyword(content):
                urls = self._extract_urls(content)
                if urls:
                    for url in urls:
                        store = self.dispatcher.identify_store(url)
                        if store and store in PRIORITY_SITES:
                            logger.info(f"Detected target product URL via keyword scraping ({store}): {url}")
                            success = await self.dispatcher.dispatch(url)
                            if success:
                                await message.channel.send(f"✅ Autocheckout started for: {url}")
                            else:
                                await message.channel.send(f"❌ Could not process URL: {url}")
                else:
                    # No URL detected, generate search URLs from product keyword
                    product_name = content.split('\n')[1] if '\n' in content else content
                    product_name_clean = re.sub(r'\W+', '+', product_name)
                    for site in PRIORITY_SITES:
                        if site == "target":
                            url = f"https://www.target.com/s?searchTerm={product_name_clean}"
                        elif site == "walmart":
                            url = f"https://www.walmart.com/search/?query={product_name_clean}"
                        elif site == "bestbuy":
                            url = f"https://www.bestbuy.com/site/searchpage.jsp?st={product_name_clean}"
                        else:
                            continue
                        logger.info(f"Generated URL for keyword scraping ({site}): {url}")
                        success = await self.dispatcher.dispatch(url)
                        if success:
                            await message.channel.send(f"✅ Autocheckout started for: {url}")
                        else:
                            await message.channel.send(f"❌ Could not process generated URL: {url}")

                # Detect SKU if present
                sku_match = re.search(r"SKU\s+(\d+)", content)
                if sku_match:
                    sku = sku_match.group(1)
                    product_url = self._sku_to_target_url(sku, content)
                    if product_url:
                        logger.info(f"Detected target SKU via keyword scraping: {sku}, URL: {product_url}")
                        success = await self.dispatcher.dispatch(product_url)
                        if success:
                            await message.channel.send(f"✅ Autocheckout started for SKU: {sku}")
                        else:
                            await message.channel.send(f"❌ Could not process SKU: {sku}")

            # -----------------------------
            # 3️⃣ Detect all URLs in content + embeds
            # -----------------------------
            processed_urls = set()
            url_pattern = r"(https?://[^\s]+)"
            urls = re.findall(url_pattern, content)

            if message.embeds:
                for embed in message.embeds:
                    if embed.description:
                        urls.extend(re.findall(url_pattern, embed.description))
                    if embed.fields:
                        for field in embed.fields:
                            urls.extend(re.findall(url_pattern, field.value))

            for url in set(urls):
                if url in processed_urls:
                    continue
                processed_urls.add(url)

                # Use message content to match, not URL itself
                if self._contains_target_keyword(content):
                    store = self.dispatcher.identify_store(url)
                    if store and store in PRIORITY_SITES:
                        logger.info(f"Detected target product URL: {url}")
                        success = await self.dispatcher.dispatch(url)
                        if success:
                            await message.channel.send(f"✅ Purchase process started for: {url}")
                        else:
                            await message.channel.send(f"❌ Could not process URL: {url}")
                else:
                    logger.info(f"Ignored non-target URL: {url}")

            # -----------------------------
            # 4️⃣ Detect SKUs
            # -----------------------------
            sku_match = re.search(r"SKU\s+(\d+)", content)
            if sku_match:
                sku = sku_match.group(1)
                product_url = self._sku_to_target_url(sku, content)
                if product_url and self._matches_target(product_url):
                    logger.info(f"Detected target SKU: {sku}, URL: {product_url}")
                    success = await self.dispatcher.dispatch(product_url)
                    if success:
                        await message.channel.send(f"✅ Purchase process started for SKU: {sku}")
                    else:
                        await message.channel.send(f"❌ Could not process SKU: {sku}")

    # -----------------------------
    # Helper functions
    # -----------------------------
    def _matches_target(self, value: str) -> bool:
        """Check if value matches any keyword or URL in TARGET_PRODUCTS."""
        if not TARGET_PRODUCTS:
            return False
        return any(keyword.lower() in value.lower() for keyword in TARGET_PRODUCTS)

    def _contains_target_keyword(self, content: str) -> bool:
        """Check if message content contains any target keywords for the sniper."""
        return self._matches_target(content)

    def _extract_urls(self, content: str):
        """Extract all URLs from text."""
        url_pattern = r"(https?://[^\s]+)"
        return re.findall(url_pattern, content)

    def _sku_to_target_url(self, sku: str, content: str):
        """Return the product URL if SKU belongs to a target product and priority site."""
        for site in PRIORITY_SITES:
            if site == "target" and re.search(r'target', content, re.IGNORECASE):
                return f"https://www.target.com/p/-/{sku}"
            elif site == "walmart" and re.search(r'walmart', content, re.IGNORECASE):
                return f"https://www.walmart.com/ip/{sku}"
            elif site == "bestbuy" and re.search(r'bestbuy', content, re.IGNORECASE):
                return f"https://www.bestbuy.com/site/{sku}.p"
        return None

    def run(self):
        self.client.run(self.token)
