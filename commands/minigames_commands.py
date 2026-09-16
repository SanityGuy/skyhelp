import discord
from discord.ext import commands
from discord import app_commands
import random

class Minigames(commands.Cog):

    BALL_RESPONSES = ["It is certain", "It is decidedly so", "Without a doubt", "Yes definitely", "You may rely on it", "As I see it yes", "Most likely", "Outlook good", "Yes", "Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now", "Cannot predict now", "Concentrate and ask again", "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.photos = {
            "heads": "./miniassets/coinstails/heads.png",
            "tails": "./miniassets/coinstails/tails.png"
        }

    @app_commands.command(name="magic8ball", description="Ask a question and unveil the answer.")
    async def magic8ball(self, interaction: discord.Interaction, question: str):
        ballembed = discord.Embed(title=question, description=random.choice(self.BALL_RESPONSES), color=discord.Color.random())
        ballembed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=ballembed)

    @app_commands.command(name="coinflip", description="Flip a coin.")
    async def coinflip(self, interaction: discord.Interaction):
        randomchoice = random.choice(["Heads", "Tails"])

        if randomchoice == "Heads":
            coinfile = discord.File(self.photos["heads"], filename="heads.png")
            imageurl = "attachment://heads.png"
        else:
            coinfile = discord.File(self.photos["tails"], filename="tails.png")
            imageurl = "attachment://tails.png"

        coinembed = discord.Embed(title="Coin Flip", description=randomchoice, color=discord.Color.random())
        coinembed.set_thumbnail(url=imageurl)
        coinembed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=coinembed, file=coinfile)

    @app_commands.command(name="ship", description="Ship a person with another person!")
    async def ship(self, interaction: discord.Interaction, first: discord.Member, second: discord.Member):
        lovePercent = random.randint(1, 100)
        yesOrNo = ""
        colorchoice = random.choice([first.color, second.color])

        if lovePercent >= 99:
            yesOrNo = "SOULMATES"
            colorchoice = discord.Color.green()
        elif lovePercent >= 95:
            yesOrNo = "PERFECT MATCH"
        elif lovePercent >= 85:
            yesOrNo = "GOOD MATCH"
        elif lovePercent >= 75:
            yesOrNo = "Fair Match"
        elif lovePercent >= 50:
            yesOrNo = "Eh maybe"
        elif lovePercent >= 25:
            yesOrNo = "Not a good match"
        else:
            yesOrNo = "Quite a bad match"

        shipembed = discord.Embed(title=f"{first.display_name} & {second.display_name}", description=f"{interaction.user.mention} has shipped {first.mention} with {second.mention}!\nLet's see how it goes!", color=colorchoice)
        shipembed.add_field(name="Percentage", value=f"{lovePercent}%")
        shipembed.add_field(name="Possibility", value=yesOrNo)
        shipembed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=shipembed)

    @app_commands.command(name="dice", description="Roll a dice.")
    async def dice(self, interaction: discord.Interaction):
        result = random.randint(1, 6)
        diceembed = discord.Embed(title="Dice Roll", description=f"The dice has been rolled by {interaction.user.mention} and the result is {result}", color=discord.Color.random())
        diceembed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=diceembed)

    @app_commands.command(name="avatar", description="Get an avatar.")
    async def avatar(self, interaction: discord.Interaction, person: discord.Member):
        avatarembed = discord.Embed(title=f"{person.display_name}'s Avatar", description=f"Via link [{person.display_name}'s Avatar]({person.display_avatar.url})", color=person.color)
        avatarembed.set_thumbnail(url=person.display_avatar.url)
        avatarembed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=avatarembed)

    @app_commands.command(name="rate", description="Rate another user from 1 to 10!")
    async def rate(self, interaction: discord.Interaction, person: discord.Member, rating: int | None = None):
        if rating is None:
            rating = random.randint(1, 10)

        if rating < 1 or rating > 10:
            await interaction.response.send_message("Rating must be between 1 and 10!", ephemeral=True)
            return

        rateembed = discord.Embed(title=f"{person.display_name}'s Rating", description=f"{interaction.user.mention} has rated {person.mention} with a rating of **{rating}/10**!", color=person.color)
        rateembed.add_field(name="Rating", value=f"{rating}/10")
        rateembed.set_thumbnail(url=person.display_avatar.url)
        rateembed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=rateembed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Minigames(bot))