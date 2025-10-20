import discord
from discord.ext import commands

# Channel ID where the bot will post the thank-you message and the ranking
BOOST_CHANNEL_ID = 1397020269482082314

# Enable required intents
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.members = True

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Global data
valid_count = 0
recorded_addresses = set()  # Store all unique Solana addresses
user_addresses = {}  # Map user_id -> address (so each user can only participate once)

def is_valid_solana_address(address: str) -> bool:
    """
    Check if the message looks like a valid Solana address.
    Solana addresses are Base58 encoded and typically 32–44 characters long.
    """
    base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    if not (32 <= len(address) <= 44):
        return False
    return all(c in base58_chars for c in address)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    """
    Triggered when a member’s data changes (e.g., they start boosting).
    """
    if before.premium_since is None and after.premium_since is not None:
        guild = after.guild
        channel = guild.get_channel(BOOST_CHANNEL_ID)
        if channel:
            msg = (
                f"🎉 Thank you for boosting the server, {after.mention}! "
                "Please send me a DM with your **Solana address** to receive your reward."
            )
            await channel.send(msg)
            print(f"📢 Announced boost by {after} in {guild.name}")

@bot.event
async def on_member_join(member):
    """
    Triggered when a new member joins the server.
    """
    guild = member.guild
    channel = guild.get_channel(BOOST_CHANNEL_ID)
    if channel:
        await channel.send(
            f"👋 Welcome {member.mention}! Please DM me your **Solana address** to participate. "
            "(# numbering follows order of submission)"
        )
        print(f"👋 Welcome message sent for {member} in {guild.name}.")

@bot.event
async def on_message(message):
    """
    Handle DMs containing Solana addresses.
    """
    global valid_count, recorded_addresses, user_addresses

    # Process only DMs from real users (ignore bots)
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        content = message.content.strip()
        user_id = message.author.id

        # Check if user has already submitted an address
        if user_id in user_addresses:
            await message.channel.send(
                f"⚠️ You have already submitted a Solana address: `{user_addresses[user_id]}`. "
                "Only one submission is allowed."
            )
            print(f"⚠️ {message.author} tried to submit a second address: {content}")
            return

        # Validate the Solana address
        if is_valid_solana_address(content):
            # Check if address was already used
            if content in recorded_addresses:
                # Fetch mutual guilds to check boosting status
                mutual_guilds = [g for g in bot.guilds if g.get_member(user_id)]
                boosted = any(
                    g.get_member(user_id).premium_since is not None for g in mutual_guilds
                )
                member_on_server = any(g.get_member(user_id) is not None for g in mutual_guilds)

                if boosted and member_on_server:
                    valid_count += 1
                    user_addresses[user_id] = content
                    print(f"{valid_count:02d}. ✅ Duplicate address allowed for booster {message.author}: {content}")
                    await message.channel.send(
                        f"✅ Your address has been accepted because you boosted the server! (#{valid_count:02d})"
                    )

                    # Post also in the boost channel
                    for g in bot.guilds:
                        channel = g.get_channel(BOOST_CHANNEL_ID)
                        if channel:
                            await channel.send(f"#{valid_count:02d} • {message.author.mention} – `{content}` ✅ (Booster)")
                            break

                else:
                    print(f"⚠️ Duplicate address from {message.author}: {content}")
                    await message.channel.send(
                        "⚠️ This Solana address is already registered and cannot be used again."
                    )
            elif valid_count < 99:
                valid_count += 1
                recorded_addresses.add(content)
                user_addresses[user_id] = content
                print(f"{valid_count:02d}. ✅ Valid Solana address from {message.author}: {content}")
                await message.channel.send(
                    f"✅ Address #{valid_count:02d} successfully registered. Thank you!"
                )

                # Post in the public channel in order
                for g in bot.guilds:
                    channel = g.get_channel(BOOST_CHANNEL_ID)
                    if channel:
                        await channel.send(f"#{valid_count:02d} • {message.author.mention} – `{content}` ✅")
                        break

            else:
                await message.channel.send("⚠️ The limit of 99 addresses has been reached.")
        else:
            await message.channel.send("❌ That doesn’t look like a valid Solana address.")

    # Keep command system working
    await bot.process_commands(message)

# ---- Insert your bot token below ----
bot.run("")
