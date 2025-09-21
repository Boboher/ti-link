import discord
from discord.ext import commands, tasks
from discord.commands import Option
import threading
import asyncio

# Import your main_controller module (replace with actual import)
import main_controller  # Ensure this has .discord_loop(), .discord_message_in, and .discord_message_out

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Replace with your actual channel and guild IDs
CHANNEL_ID = 1412860288679546975  # 🔁 REPLACE THIS
GUILD_ID = 1412860287828361248    # 🔁 REPLACE THIS


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    # Start TI-84 comms loop in background
    threading.Thread(target=main_controller.discord_loop, daemon=True).start()

    # Start checking for messages from TI-84
    check_for_outgoing_message.start()

    # Run comms check
    await comms_check_sequence()


async def comms_check_sequence():
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print("⚠️ Could not find the target channel for comms check.")
        return

    await channel.send(
        "**Initiating TI-84 Communications Check**...\n"
        "Establishing uplink with TI-84 calculator...\n"
        "Please do not send any messages until link is verified...\n"
        "--------------------------------------"
    )

    # Send test message to TI-84
    main_controller.discord_message_in.append({
        "title": "CHECK",
        "text": "SYSTEM: Initiate comms confirmation sequence."
    })
    main_controller.discord_message_in.append({
        "title": "QUESTION",
        "text": "Comms confirmed"
    })
    main_controller.discord_message_in.append({
        "title": "SEND",
        "text": "SEND"
    })

    print("📡 Sent test message to TI-84. Waiting for confirmation...")

    # Wait for "Comms confirmed" message for up to 30 seconds
    for _ in range(30):  # Check every 1 seconds
        await asyncio.sleep(1)

        if main_controller.discord_message_out:
            if "Comms confirmed" in main_controller.discord_message_out:
                await channel.send(
                    "**TI-84 Link Established**\n"
                    "Comms link with TI-84 has been successfully confirmed.\n"
                    "Message relay is now operational.\n"
                    "--------------------------------------\n"
                    "**You may now submit messages using** `/send-message`."
                )
                print("✅ Comms confirmed.")
                main_controller.discord_message_out = None
                return

    # Timeout fallback
    await channel.send(
        "**Comms Check Failed**\n"
        "Did not receive confirmation from TI-84 within expected time.\n"
        "Please check hardware connection and restart the bot."
    )
    print("Comms check failed.")


@bot.slash_command(
    name="send-message",
    description="Submit message to TI-84",
    guild_ids=[GUILD_ID]  # Replace with your actual guild ID
)
async def send_message(
    ctx: discord.ApplicationContext,
    title: str = Option(str, "Title", max_length=8),  # type: ignore
    message: str = Option(str, "Message")  # type: ignore
):
    # Print to terminal
    print("\n----- New Message Submitted -----")
    print(f"Author : {ctx.author}")
    print(f"Title  : {title}")
    print(f"Message: {message}")
    print("--------------------------------")

    # Send to TI-84
    main_controller.discord_message_in.append({
        "title": title,
        "text": f"author: {ctx.author}ENTER{message}"
    })

    await ctx.respond(f"{message.replace("ENTER", "\n")}\n✅ Your message has been sent to the TI-84!")


@tasks.loop(seconds=5)
async def check_for_outgoing_message():
    if main_controller.discord_message_out is not None:
        channel = bot.get_channel(CHANNEL_ID)

        if channel is None:
            print("⚠️ Could not find the target channel.")
            return

        message_text = main_controller.discord_message_out

        if message_text.strip() == "Lost connection with TI84":
            try:
                await channel.send(
                    "**Connection to TI-84 has been lost.**\n"
                    "Shutting down bot systems...\n"
                    "--------------------------------------"
                )
                print("TI-84 connection lost. Shutting down...")
                await bot.close()
            except Exception as e:
                print(f"Failed to send shutdown message: {e}")

        elif message_text.strip().upper() == "DELETE ALL CHATS":
            try:
                await channel.send("⚠️ **Destructive command received: `DELETE ALL CHATS`**\nInitiating message purge protocol...")

                deleted = await channel.purge(limit=100, check=lambda m: m.author == bot.user)
                await channel.send(f"🧹 **Purge complete.** `{len(deleted)}` messages deleted.")
                print(f"🧹 Deleted {len(deleted)} messages.")
            except Exception as e:
                print(f"Failed to delete messages: {e}")

        else:
            try:
                await channel.send(f"**Message from TI-84**:\n{message_text}")
                print("✅ Sent message from TI-84.")
            except Exception as e:
                print(f"Failed to send message: {e}")

        main_controller.discord_message_out = None



# Run the bot
bot.run("")  # 🔁 REPLACE THIS

