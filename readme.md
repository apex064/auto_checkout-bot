Discord Auto-Checkout Bot – User Manual
This bot automatically detects product restock alerts, matches them to your target products, and starts checkout using the appropriate store bot (Target, Walmart, BestBuy). It can also process manual purchase commands through Discord.

Installation & Setup
 Requirements
Python 3.10+
pip (Python package manager)
A Discord Bot Token (create one in Discord Developer Portal)

⚙️ Config Setup
Edit config.json with your details:

{
  "discord_token": "YOUR_DISCORD_BOT_TOKEN", // Get from Discord Dev Portal
  "email": "your_email@example.com", // Account email for checkout
  "password": "your_password", // Account password
  "account_name": "Your Name", // Display name for logs
  "headless": false, // true = run browser in background, false = visible
  "place_order": false, // true = actually place order, false = test mode
  "refresh_interval": 10, // seconds between stock checks

  "TARGET_PRODUCTS": [
    "Elite Trainer Box",
    "Booster Bundle",
    "PlayStation 5"
  ],

  "PRIORITY_SITES": [
    "walmart",
    "bestbuy",
    "target"
  ],

  "card": {
    "number": "4111111111111111",
    "exp": "12/25",
    "cvv": "123"
  },

  "shipping": {
    "name": "Your Name",
    "address": "123 Main St",
    "city": "Your City",
    "state": "CA",
    "zip": "12345",
    "phone": "555-123-4567"
  }
}
🔑 Key Settings Explained:
discord_token – Authenticates your bot to your Discord server
TARGET_PRODUCTS – Keywords to look for in messages (case-insensitive)
PRIORITY_SITES – Which stores to prioritize when multiple URLs are found
place_order – Set to true only when you are ready to actually buy items
headless – Set to true if you don’t want a browser window to open

Running the Bot
Start the bot:

python wmain.py
✅ You should see a message like:

INFO - Logged in as MyCheckoutBot#1234

3️⃣ Using the Bot in Discord
🔹 1. Manual Purchase Command
Use !buy followed by a product URL or keyword.
Example:

!buy https://www.target.com/p/some-product/12345
or

!buy Elite Trainer Box
✅ The bot will:
Check if the product matches any of your TARGET_PRODUCTS
Dispatch it to the correct bot (TargetBot, WalmartBot, or BestBuyBot)
Send a confirmation message:    ✅ Purchase process started for: Elite Trainer Box
  

🔹 2. Auto-Checkout from Restock Alerts
When someone posts a message like:

Item Restocked!
Fall Plaid Lightweight Throw Blanket Brown - Hearth & Hand™ with Magnolia
https://www.target.com/p/123456
✅ The bot will:
Scan for keywords & URLs
If URL matches a priority site and product matches TARGET_PRODUCTS, it will run checkout automatically.

🔹 3. SKU Detection
If a message contains a SKU like:

SKU 123456
The bot will convert it to a product URL:
Target → https://www.target.com/p/-/123456
Walmart → https://www.walmart.com/ip/123456
BestBuy → https://www.bestbuy.com/site/123456.p
Then attempt checkout automatically.

4️⃣ Logging & Debugging
All bot actions are logged (usually to postback.log or bot.log depending on your logger setup). If something fails, check logs for:
❌ Unsupported store URL
❌ Could not process product
⚠️ Could not resolve product URL

5️⃣ Tips & Best Practices
✅ Start with place_order = false to avoid accidental purchases while testing ✅ Run in a test Discord server before using in production ✅ Add the bot to your server with correct permissions (read messages, send messages) ✅ Keep your discord token secret – if leaked, regenerate it in Discord Developer Portal ✅ Regularly update TARGET_PRODUCTS to reflect what you want to buy
NOTE THAT IF YOU WANT A PRODUCT DONT CHANGE ANY URL CHANGE THE TARGET PRODUCT IN THE JSON CHANGE ONLY THE TARGET PRODUCT THIS FEILD 

  "target_products": [
    "Pokemon Prismatic Evolutions 8 Mini-Tins with Promo Cards",
    "Booster Bundle",
    "Fall Plaid Lightweight Throw Blanket Brown - Hearth & Hand™ with Magnolia"
  ], AS YO CAN SEE THE TARGET PRODUCT NAME ARE Pokemon Prismatic Evolutions 8 Mini-Tins with Promo Cards",
    "Booster Bundle",
    "Fall Plaid Lightweight Throw Blanket Brown - Hearth & Hand™ with Magnolia YOU CAN ADD ANY AMOUNT OF PRODUCT YOU WANT BUT DONT CHANGE THE FORMATING WHEN E MESSAGE FROM THE DISCORD SERVER CONTAINS THE TARGET PRODUCT IT SEARCHES FOR THE PRODUCT URL AND KNOWS WHAT TO DO THIS README SHOULD EXPLAIN EVERYTHING 
    
