import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, time, timedelta
import tracker

'''
img_link = "https://i.etsystatic.com/24589365/r/il/5a7378/3329746240/il_fullxfull.3329746240_dxht.jpg"

                for player in myTeamList:
                    if name.split('#')[0].lower() == player.name.lower():
                        img_link = tracker.get_image_link(player.character)'''


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

    @client.tree.command(name = "get_match_history")
    @app_commands.describe(name = "Prints match history of a certain user", mode = "What mode? (competitive, unrated, deathmatch, spikerush, swiftplay, escalation, replication)")
    async def get_match_history(interaction: discord.Interaction, name: str, mode: str='competitive'):
        await interaction.response.defer()
        resp = tracker.get_match_history(name, mode)
        if resp == "broke":
            await interaction.response.send_message("Fuck you your inputs are wrong")
        else:
            embed = discord.Embed(
                colour=discord.Colour.dark_purple(),
                description=f"{ mode.capitalize() } match history (5 games)",
                title=f"{ name }",
            )

            embed.set_footer(text="DM Teddygat0r#8612 for suggestions to bot")
            embed.set_author(name="Teddygat0r", url="https://github.com/Teddygat0r/pst-tracker-bot")
            embed.set_thumbnail(url="https://www.valorantpcdownload.com/wp-content/uploads/2021/08/TX_CompetitiveTier_Large_11.png")

            for index, game in zip(range(len(resp)), resp):
                if name.split('#')[0].lower() in [player.name.lower() for player in game.players.red]:
                    myteam = game.teams.red
                    myTeamList = game.players.red
                    theirTeamList = game.players.blue
                else: 
                    myteam = game.teams.blue
                    myTeamList = game.players.blue
                    theirTeamList = game.players.red

                teamliststr = "```"
                for p1, p2 in zip(myTeamList, theirTeamList):
                    teamliststr += f"{ p1.name.ljust(16) } |  { p2.name.ljust(16) }\n"
                teamliststr += "```"

                embed.add_field(name=f"{ game.metadata.map }   |   { myteam.rounds_won } : { myteam.rounds_lost }", value=teamliststr, inline=False)

            await interaction.followup.send(embed=embed)

    @client.tree.command(name = "detail_match")
    @app_commands.describe(name = "Select User", mode = "What mode? (competitive, unrated, deathmatch, spikerush, swiftplay, escalation, replication)", index="Index of game (1-5)")
    async def detail_match(interaction: discord.Interaction, name: str = "", mode: str='competitive', index: int=1):
        await interaction.response.defer()
        if name == "":
            name = get_username_from_discord(interaction)
        if name == "":
            await interaction.response.send_message("Fuck you give a username or register with /list_tracked_users")
            return

        if index > 5 or index < 1:
            await interaction.response.send_message("Fuck you index 1-5 only")
            return
        resp = tracker.get_match_history(name, mode, index)
        if resp == "broke":
            await interaction.response.send_message("Fuck you your inputs are wrong")
        else:
            game = resp[index - 1]
            me = game.players.all_players[0]

            if name.split('#')[0].lower() in [player.name.lower() for player in game.players.red]:
                myteam = game.teams.red
                myTeamList = game.players.red
                theirTeamList = game.players.blue
            else: 
                myteam = game.teams.blue
                myTeamList = game.players.blue
                theirTeamList = game.players.red
            for player in myTeamList:
                if name.split('#')[0].lower() == player.name.lower():
                    me = player
                    img_link = tracker.get_image_link(player.character)
            
            headshots = round(me.stats.headshots / (me.stats.bodyshots + me.stats.headshots + me.stats.legshots) * 100, 2 )
            kast = 0
            L_rds = []

            for rounds in game.rounds:
                if tracker.getKAST(me.puuid, rounds):
                    kast += 1
                else:
                    L_rds.append(rounds)
                
            
            kast = round(kast / len(game.rounds) * 100, 2)

            embed = discord.Embed(
                colour=discord.Colour.dark_purple(),
                description=f"{ me.stats.kills } / { me.stats.deaths } / { me.stats.assists } / HS: { headshots }% / KAST: { kast }%",
                title=f"{ mode.capitalize() }  |  { game.metadata.map }",
            )

            for count, rounds in enumerate(game.rounds):
                for pl in rounds.player_stats:
                    if pl.player_puuid == me.puuid:
                        myRoundStats = pl
                    
                assists, traded, survived = tracker.statKast(me.puuid, rounds)

                trd_emoji = "✅" if traded else "❌"
                svd_emoji = "✅" if survived else "❌"
                l_rd_emoji = "❗❗❗ No KAST! ❗❗❗" if rounds in L_rds else ""
                win_emoji = "🏆" if rounds.winning_team == myteam else ""

                val = f"```{ myRoundStats.kills } / { assists } / Survived: { svd_emoji } / Traded: { trd_emoji }\n"
                val += f"{ myRoundStats.economy.weapon.name } + { myRoundStats.economy.armor.name } | ${ myRoundStats.economy.spent + myRoundStats.economy.remaining } - ${ myRoundStats.economy.spent } = ${ myRoundStats.economy.remaining }"
                val += "```"

                embed.add_field(name=f"Round { count + 1 } { win_emoji }     { l_rd_emoji }", value=val, inline=False)

            embed.set_footer(text="DM Teddygat0r#8612 for suggestions to bot")
            embed.set_author(name="Teddygat0r", url="https://github.com/Teddygat0r/pst-tracker-bot")
            embed.set_thumbnail(url=img_link)

            await interaction.followup.send(embed=embed)

    @tasks.loop(minutes=1)
    async def once_a_day():
        now = datetime.utcnow()
        
        if now.hour == 8 and now.minute==0:
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

    def get_username_from_discord(interaction: discord.Interaction):
        discord_uuid = interaction.user.id
        if discord_uuid in current_discord_ids:
            return current_users[current_discord_ids.index(discord_uuid)]
        return ""



    client.run(TOKEN)