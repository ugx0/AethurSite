import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import asyncio
import time

# Define the bot owner ID
TOKEN = "MTI0MjI5MDQxNzE3MzY2MzkwNA.GmobQd.1qQNHPD7FcKHZVum5OG0yNmd_JM40ixJ38N764"

BOT_OWNER_ID = 902049253919186995

# Initialize bot client with command prefix and intents
client = commands.Bot(command_prefix='$', help_command=None, intents=discord.Intents.all())

# Event: Bot is ready
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    client.start_time = time.time()
    # Set custom status
    game = discord.Game("Playing $play")
    await client.change_presence(status=discord.Status.online, activity=game)

# Function to convert human-readable duration to seconds
def convert_to_seconds(duration):
    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    return int(duration[:-1]) * multipliers[duration[-1]]

# Function to create an embed for action details
def create_action_embed(author, action, reason=None, duration=None):
    embed = discord.Embed(title=f'{action.capitalize()} Details', color=discord.Color.red())
    embed.add_field(name='Author', value=author.name, inline=False)
    
    # Use the name of the highest displayed role if found
    if highest_displayed_role:
        embed.add_field(name='Author Role', value=highest_displayed_role.name, inline=False)
    if reason:
        embed.add_field(name='Reason', value=reason, inline=False)
    if duration:
        embed.add_field(name='Duration', value=duration, inline=False)
    return embed

# Define the categories and commands
categories = {
    "Moderation": {
        "mute": "Mute a member.",
        "unmute": "Unmute a member.",
        "kick": "Kick a member from the server.",
        "ban": "Ban a member from the server."
    },
    "Utility": {
        "role": "Add or remove a role from a member.\nUsage: $role <member> <role>",
        "pu": "Delete messages sent by a specific user.\nUsage: $pu <member> <amount>",
        "nickname": "Change a member's nickname.\nUsage: $nickname <member> [new_nickname]",
        "pb": "Delete messages sent by bots.\nUsage: $pb <amount>",
        "pt": "Delete messages until a specific message ID.\nUsage: $pt <message_id>",
        "p": "Delete a specific number of messages.\nUsage: $p <amount>"
    },
    "Voice": {
        "vcmute": "Mute a member in a voice channel.\nUsage: $vcmute <member>",
        "vcunmute": "Unmute a member in a voice channel.\nUsage: $vcunmute <member>",
        "vckick": "Kick a member from a voice channel.\nUsage: $vckick <member>",
        "vcdeafen": "Deafen a member in a voice channel.\nUsage: $vcdeafen <member>",
        "vcundeafen": "Undeafen a member in a voice channel.\nUsage: $vcundeafen <member>"
    },
    "Spam": {
        "spam": "Spam messages in the current channel.\nUsage: $spam <message>",
        "dmspam": "Spam messages to a specific user.\nUsage: $dmspam <member> <message>",
        "sspam": "Stop ongoing spamming tasks.\nUsage: $sspam"
    }
}

# Command: Help
@client.command()
async def help(ctx):
    # Create the initial embed with category buttons
    embed = discord.Embed(title="Categories", description="Please select a category:", color=discord.Color.blue())
    for category in categories:
        embed.add_field(name=category, value="Click to view commands", inline=False)
    message = await ctx.send(embed=embed)

    # Define a callback function to handle button clicks
    async def callback(interaction: discord.Interaction):
        selected_category = interaction.component.label
        category_commands = categories[selected_category]

        # Create an embed for the selected category with detailed command information
        embed = discord.Embed(title=f"{selected_category} Commands", color=discord.Color.blue())
        for command, description in category_commands.items():
            embed.add_field(name=f"**{command}**", value=description, inline=False)

        # Edit the original message to display the detailed embed
        await interaction.response.edit_message(embed=embed)

    # Add buttons for each category
    for category in categories:
        bbutton = discord.ui.Button(style=discord.ButtonStyle.secondary, label=category, custom_id=category)
        message.components[0].append_row(button)

    # Wait for button interactions
    try:
        interaction = await client.wait_for("button_click", timeout=60.0, check=lambda i: i.message.id == message.id and i.user == ctx.author)
        await callback(interaction)
    except asyncio.TimeoutError:
        await message.edit(embed=discord.Embed(title="Timed out", description="You took too long to respond.", color=discord.Color.red()), components=[])

# Command: Mute
@client.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, duration, *, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
    if not muted_role:
        muted_role = await ctx.guild.create_role(name='Muted')
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False)

    await member.add_roles(muted_role)
    await ctx.send(f'{member.name} has been muted for {duration}.')

    duration_seconds = convert_to_seconds(duration)
    await asyncio.sleep(duration_seconds)
    await member.remove_roles(muted_role)
    await ctx.send(f'{member.name} has been unmuted.')

    # Send DM to the user
    if reason:
        dm_reason = reason
    else:
        dm_reason = "Expired"  # Use "Expired" as reason when mute duration ends
    dm_embed = create_action_embed(ctx.author, 'mute', dm_reason, duration)
    await member.send(embed=dm_embed)

# Command: Unmute
@client.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member, *, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f'{member.name} has been unmuted.')

        # Send DM to the user
        if reason:
            dm_reason = reason
        else:
            dm_reason = "None"  # Use "None" as reason when manually unmuted
        dm_embed = create_action_embed(ctx.author, 'unmute', dm_reason)
        await member.send(embed=dm_embed)
    else:
        await ctx.send(f'{member.name} is not muted.')

# Command: Role
@client.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, *, role_arg: str):
    # Check if role_arg is a role mention
    if len(ctx.message.role_mentions) > 0:
        role_to_add = ctx.message.role_mentions[0]
    else:
        # Check if role_arg is a valid role ID
        try:
            role_id = int(role_arg)
            role_to_add = ctx.guild.get_role(role_id)
        except ValueError:
            # Search for roles that contain the provided string (case-insensitive)
            role_to_add = None
            for role in ctx.guild.roles:
                if role_arg.lower() in role.name.lower():
                    role_to_add = role
                    break

    # If role is found, toggle it for the member
    if role_to_add:
        if role_to_add in member.roles:
            await member.remove_roles(role_to_add)
            await ctx.send(f'Removed {role_to_add.name} from {member.name}.')
        else:
            await member.add_roles(role_to_add)
            await ctx.send(f'Added {role_to_add.name} to {member.name}.')
    else:
        await ctx.send(f'Role not found.')

# Command: Purge User
@client.command()
@commands.has_permissions(manage_messages=True)
async def pu(ctx, member: discord.Member, amount: int):
    deleted = await ctx.channel.purge(limit=amount, check=lambda msg: msg.author == member)
    await ctx.send(f"Deleted {len(deleted)} messages from {member.display_name}.", delete_after=3)
    await asyncio.sleep(3)
    await ctx.message.delete()

# Command: Nickname
@client.command()
@commands.has_permissions(manage_nicknames=True)
async def nickname(ctx, member: discord.Member, *, new_nickname=None):
    if new_nickname is None:
        await member.edit(nick=None)
        await ctx.send(f"Reset nickname for {member.name}.")
    else:
        await member.edit(nick=new_nickname)
        await ctx.send(f"Set nickname for {member.name} to {new_nickname}.")

# Command: Purge Bot
@client.command()
@commands.has_permissions(manage_messages=True)
async def pb(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount, check=lambda msg: msg.author.bot)
    await ctx.send(f"Deleted {len(deleted)} bot messages.", delete_after=3)
    await asyncio.sleep(3)
    await ctx.message.delete()

# Command: Purge Till
@client.command()
@commands.has_permissions(manage_messages=True)
async def pt(ctx, message_id: int):
    def check(msg):
        return msg.id > message_id

    deleted = await ctx.channel.purge(limit=None, check=check, before=ctx.message)
    await ctx.send(f"Deleted {len(deleted)} messages till message ID {message_id}.", delete_after=3)
    await asyncio.sleep(3)
    await ctx.message.delete()

# Command: Simple Purge
@client.command()
@commands.has_permissions(manage_messages=True)
async def p(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount+1)  # +1 to also delete the command message
    await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=3)
    await asyncio.sleep(3)
    await ctx.message.delete()

# Command: Kick
@client.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'{member.name} has been kicked.')

    # Send DM to the user
    dm_embed = create_action_embed(ctx.author, 'kick', reason)
    await member.send(embed=dm_embed)

# Command: Ban
@client.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'{member.name} has been banned.')

    # Send DM to the user
    dm_embed = create_action_embed(ctx.author, 'ban', reason)
    await member.send(embed=dm_embed)

# Command: VCMute
@client.command()
@commands.has_permissions(administrator=True)
async def vcmute(ctx, member: discord.Member):
    if member.voice is None:
        await ctx.send("User is not in a voice channel.")
        return

    await member.edit(mute=True)
    await ctx.send(f"Muted {member.display_name} in the voice channel.")

# Command: VCUnmute
@client.command()
@commands.has_permissions(administrator=True)
async def vcunmute(ctx, member: discord.Member):
    if member.voice is None:
        await ctx.send("User is not in a voice channel.")
        return

    await member.edit(mute=False)
    await ctx.send(f"Unmuted {member.display_name} in the voice channel.")

# Command: VCKick
@client.command()
@commands.has_permissions(administrator=True)
async def vckick(ctx, member: discord.Member):
    if member.voice is None:
        await ctx.send("User is not in a voice channel.")
        return

    await member.edit(voice_channel=None)
    await ctx.send(f"Kicked {member.display_name} from the voice channel.")

# Command: VCDeafen
@client.command()
@commands.has_permissions(administrator=True)
async def vcdeafen(ctx, member: discord.Member):
    if member.voice is None:
        await ctx.send("User is not in a voice channel.")
        return

    await member.edit(deafen=True)
    await ctx.send(f"Deafened {member.display_name} in the voice channel.")

# Command: VCUndeafen
@client.command()
@commands.has_permissions(administrator=True)
async def vcundeafen(ctx, member: discord.Member):
    if member.voice is None:
        await ctx.send("User is not in a voice channel.")
        return

    await member.edit(deafen=False)
    await ctx.send(f"Undeafened {member.display_name} in the voice channel.")

# Global variables to hold the spamming tasks
channel_spam_task = None
dm_spam_task = None

# Command: Spam
@client.command()
async def spam(ctx, *, message: str):
    global channel_spam_task

    # Check if the command is invoked by the bot owner
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("Only the bot owner can run this command.")
        return

    # Check if the spamming task is already running
    if channel_spam_task and not channel_spam_task.done():
        await ctx.send("A channel spamming task is already running.")
        return

    # Start the spamming task
    async def spam_channel():
        for _ in range(1000):
            await ctx.send(message)
            await asyncio.sleep(0.01)  # Adjust the sleep duration to control message sending speed

    channel_spam_task = asyncio.create_task(spam_channel())

# Command: DM Spam
@client.command()
async def dmspam(ctx, member: discord.Member, *, message: str):
    global dm_spam_task

    # Check if the command is invoked by the bot owner
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("Only the bot owner can run this command.")
        return

    # Check if the spamming task is already running
    if dm_spam_task and not dm_spam_task.done():
        await ctx.send("A DM spamming task is already running.")
        return

    # Start the spamming task
    async def spam_dm():
        for _ in range(1000):
            await member.send(message)
            await asyncio.sleep(0.01)  # Adjust the sleep duration to control message sending speed

    dm_spam_task = asyncio.create_task(spam_dm())

# Command: Stop Spam
@client.command()
async def sspam(ctx):
    global channel_spam_task
    global dm_spam_task

    # Check if the command is invoked by the bot owner
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("Only the bot owner can run this command.")
        return

    # Check if the channel spamming task is running
    if channel_spam_task and not channel_spam_task.done():
        channel_spam_task.cancel()
        await ctx.send("Stopped channel spamming.")
    else:
        await ctx.send("No channel spamming task is currently running.")

    # Check if the DM spamming task is running
    if dm_spam_task and not dm_spam_task.done():
        dm_spam_task.cancel()
        await ctx.send("Stopped DM spamming.")
    else:
        await ctx.send("No DM spamming task is currently running.")

# Command: Copy Channel Permissions
@client.command()
@commands.has_permissions(manage_channels=True)
async def copy(ctx, source_channel: discord.abc.GuildChannel, target_channel: discord.abc.GuildChannel):
    # Get source channel permissions
    source_permissions = source_channel.overwrites

    # Apply source channel permissions to the target channel
    for overwrite in source_permissions:
        # Check if the overwrite is for a role
        if isinstance(overwrite, discord.Role):
            target = discord.utils.get(ctx.guild.roles, id=overwrite.id)
        # Check if the overwrite is for a member
        elif isinstance(overwrite, discord.Member):
            target = ctx.guild.get_member(overwrite.id)
        else:
            continue

        # Get the permissions
        permissions = source_permissions[overwrite]

        # Apply the permissions to the target channel
        await target_channel.set_permissions(target, overwrite=permissions)

    await ctx.send(f"Permissions copied from {source_channel.mention} to {target_channel.mention}.")

# Command: Ping
@client.command()
async def ping(ctx):
    latency = round(client.latency * 1000)  # Convert to milliseconds
    await ctx.send(f'Pong! Latency: {latency}ms')

# Command: Uptime
@client.command()
async def uptime(ctx):
    # Calculate the uptime
    uptime_seconds = int(time.time() - client.start_time)
    uptime_str = format_time(uptime_seconds)

    # Send the uptime to the user
    await ctx.send(f"My uptime is {uptime_str}")

def format_time(seconds):
    # Format seconds into days, hours, minutes, and seconds
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

# Run the bot with your token
client.run(TOKEN)
