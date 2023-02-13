import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, time, timedelta
import tracker

def run_discord_bot():
    TOKEN = open(".env", "r").read()
    client = commands.Bot(command_prefix='!', intents=discord.Intents.default())
    current_users = []
    current_discord_ids = []
    current_dm_count = []
    DEATHMATCH_COUNT_PER_DAY = 3
    CHN_ID = 1073884425793847398

    with open('users.txt') as myfile:
        for line in myfile:
            content = line.strip().split(' ')
            current_users.append(content[0])
            current_discord_ids.append(int(content[1]))
            current_dm_count.append(int(content[2]))

    @client.event
    async def on_ready():
        print(f'{ client.user } is now running!')

        try:
            synced = await client.tree.sync()
            print(f'Synced { len(synced) } command(s)')
            
            once_a_day.start()

        except Exception as e:
            print(e)

    @client.tree.command(name = "hello")
    async def hello(interaction: discord.Interaction):
        await interaction.response.send_message(f"{ interaction.user.mention }! Bitch wassup")

    @client.tree.command(name = "match_count")
    @app_commands.describe(name = "What is your username", mode = "What mode? (competitive, unrated, deathmatch, spikerush, swiftplay, escalation, replication)")
    async def match_count(interaction: discord.Interaction, name: str, mode: str):
        resp = tracker.get_match_count(name, mode)
        if resp == "broke":
            await interaction.response.send_message("Fuck you your inputs are wrong")
        else:
            await interaction.response.send_message(f"{ name } has played { resp } games of { mode }.")

    @client.tree.command(name = "add_tracked_user")
    @app_commands.describe(name = "Username of user to add to dm tracker", member="User's discord")
    async def add_tracked_user(interaction: discord.Interaction, name: str, member: discord.Member):
        resp = tracker.get_match_count(name, "deathmatch")
        if resp == "broke":
            await interaction.response.send_message("Fuck you the user doesn't exist")
        else:
            if(name.lower() in [x.lower() for x in current_users]):
                await interaction.response.send_message(f"{ name } is already tracked!")
                return

            with open("users.txt", "a") as myfile:
                myfile.write(f"{ name } { member.id } { resp }\n")
            current_users.append(name)
            current_discord_ids.append(member.id)
            current_dm_count.append(int(resp))
            await interaction.response.send_message(f"{ name } added to list!")

    @client.tree.command(name = "remove_tracked_user")
    @app_commands.describe(name = "Username of user to remove from dm tracker")
    async def remove_tracked_user(interaction: discord.Interaction, name: str):
        with open("users.txt", "r") as f:
            lines = f.readlines()
        with open("users.txt", "w") as f:
            for line in lines:
                if name.lower() not in line.strip("\n").lower():
                    f.write(line)
        index = [x.lower() for x in current_users].index(name.lower())
        del current_discord_ids[index]
        del current_dm_count[index]
        del current_users[index]

        await interaction.response.send_message(f"{ name } deleted from list!")

    @client.tree.command(name = "list_tracked_users")
    async def list_tracked_users(interaction: discord.Interaction):

        msg = "```\n"
        for user, discordId, pastDMCount in zip(current_users, current_discord_ids, current_dm_count):
            msg += f"{ user } | { await interaction.guild.fetch_member(discordId) } \n"
        msg += "```"
        await interaction.response.send_message(msg)


    @tasks.loop(minutes=1)
    async def once_a_day():
        now = datetime.utcnow()
        
        if now.hour == 8 and now.minutes==0:
            channel = client.get_channel(CHN_ID)
            await check_dm_status(channel)

    async def check_dm_status(channel):
        victims = []
        with open("users.txt", "w") as f:
            for user, discordId, pastDMCount in zip(current_users, current_discord_ids, current_dm_count):
                nowDMCount = tracker.get_match_count(user, mode="deathmatch")
                if int(nowDMCount) - DEATHMATCH_COUNT_PER_DAY < pastDMCount:
                    victims.append(discordId)
                f.write(f"{ user } {discordId} { nowDMCount }\n")
            
        msg = "Get fukt losers yall didn't play ur daily 3 dms :skull: :skull: :clown: :clown:"
        for id in victims:
            msg += f"<@{ id }> "
        await channel.send(msg)



    client.run(TOKEN)