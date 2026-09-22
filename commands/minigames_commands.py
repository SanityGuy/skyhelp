import discord
from discord.ext import commands
from discord import app_commands
import random
from pathlib import Path
from typing import Literal
class Minigames(commands.Cog):

    BALL_RESPONSES = ["It is certain", "It is decidedly so", "Without a doubt", "Yes definitely", "You may rely on it", "As I see it yes", "Most likely", "Outlook good", "Yes", "Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now", "Cannot predict now", "Concentrate and ask again", "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
    
    def __init__(self, bot: commands.Bot):
        BASE_DIR = Path(__file__).resolve().parent.parent
        ASSETS = BASE_DIR / "commands" / "miniassets"
        
        self.bot = bot
        self.photos = {
            # Coin Flip
            "heads": ASSETS / "coinsheads" / "heads.png",
            "tails": ASSETS / "cointails" / "tails.png",

            #8Ball
            "8ball": ASSETS / "balls" / "8ball.png",

            # DICE
            "dice1": ASSETS / "dices" / "dice_1.png",
            "dice2": ASSETS / "dices" / "dice_2.png",
            "dice3": ASSETS / "dices" / "dice_3.png",
            "dice4": ASSETS / "dices" / "dice_4.png",
            "dice5": ASSETS / "dices" / "dice_5.png",
            "dice6": ASSETS / "dices" / "dice_6.png"
        }

    @staticmethod
    def set_requester_helper(embed: discord.Embed, interaction: discord.Interaction) -> discord.Embed:
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        return embed

    @app_commands.command(name="magic8ball", description="Ask a question and unveil the answer.")
    async def magic8ball(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()

        ballfile = discord.File(self.photos["8ball"], filename="8ball.png")
        imageurl = "attachment://8ball.png"
        
        ballembed = discord.Embed(title=question, description=random.choice(self.BALL_RESPONSES), color=discord.Color.random())
        ballembed.set_thumbnail(url=imageurl)
        self.set_requester_helper(ballembed, interaction)

        await interaction.followup.send(embed=ballembed, file=ballfile)

    @app_commands.command(name="coinflip", description="Flip a coin.")
    async def coinflip(self, interaction: discord.Interaction, choice: Literal["Heads", "Tails"] | None = None):
        await interaction.response.defer()

        result = random.choice(["Heads", "Tails"])
        
        if choice is not None:
            isCorrect = choice == result
            verdict = "Correct!" if isCorrect else "Incorrect!"
            color = discord.Color.green() if isCorrect else discord.Color.red()
        else:
            color = discord.Color.random()

        if result == "Heads":
            coinfile = discord.File(self.photos["heads"], filename="heads.png")
            imageurl = "attachment://heads.png"
        else:
            coinfile = discord.File(self.photos["tails"], filename="tails.png")
            imageurl = "attachment://tails.png"

        coinembed = discord.Embed(title="Coin Flip", description="You can bet a coinflip or make it fully random!\nUsage: */coinflip <heads/tails>* **(optional)**", color=color)
        coinembed.set_thumbnail(url=imageurl)
        coinembed.add_field(name="Result", value=result)
        if choice is not None:
            coinembed.add_field(name="Verdict", value=verdict)

        self.set_requester_helper(coinembed, interaction)

        await interaction.followup.send(embed=coinembed, file=coinfile)

    @app_commands.command(name="ship", description="Ship a person with another person!")
    async def ship(self, interaction: discord.Interaction, first: discord.Member, second: discord.Member):
        await interaction.response.defer()

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
        shipembed.set_thumbnail(url=random.choice([first.display_avatar.url, second.display_avatar.url]))

        self.set_requester_helper(shipembed, interaction)

        await interaction.followup.send(embed=shipembed)

    @app_commands.command(name="dice", description="Roll a dice.")
    async def dice(self, interaction: discord.Interaction):
        await interaction.response.defer()

        result = random.randint(1, 6)

        dicefile = discord.File(self.photos[f"dice{result}"], filename=f"dice_{result}.png")
        imageurl = f"attachment://dice_{result}.png"


        diceembed = discord.Embed(title="Dice Roll", description=f"The dice has been rolled by {interaction.user.mention}!", color=discord.Color.random())
        diceembed.add_field(name="Dice Result", value=f"{result}")
        diceembed.set_thumbnail(url=imageurl)

        self.set_requester_helper(diceembed, interaction)

        await interaction.followup.send(embed=diceembed, file=dicefile)

    @app_commands.command(name="avatar", description="Get an avatar.")
    async def avatar(self, interaction: discord.Interaction, person: discord.Member | None = None):
        await interaction.response.defer()

        if person is None:
            person = interaction.user
        
        avatarembed = discord.Embed(title=f"{person.display_name}'s Avatar", description=f"This is the profile picture of the user. {person.mention}", color=person.color)
        avatarembed.set_thumbnail(url=person.display_avatar.url)
        avatarembed.add_field(name="The User", value=person.mention)
        avatarembed.add_field(name="Profile URL", value=f"[{person.display_name}'s Profile]({person.display_avatar.url})")

        self.set_requester_helper(avatarembed, interaction)

        await interaction.followup.send(embed=avatarembed)

    @app_commands.command(name="rate", description="Rate another user from 1 to 10!")
    async def rate(self, interaction: discord.Interaction, person: discord.Member, rating: int | None = None):
        await interaction.response.defer()

        if rating is None:
            rating = random.randint(1, 10)

        if rating < 1 or rating > 10:
            await interaction.followup.send("Rating must be between 1 and 10!", ephemeral=True)
            return

        rateembed = discord.Embed(title=f"{person.display_name}'s Rating", description=f"{interaction.user.mention} has rated {person.mention}!", color=person.color)
        rateembed.add_field(name="Rating", value=f"{rating}/10")
        rateembed.set_thumbnail(url=person.display_avatar.url)

        self.set_requester_helper(rateembed, interaction)

        await interaction.followup.send(embed=rateembed)

    @app_commands.command(name="rps", description="Play rock paper scissors with a bot!")
    async def rockpaperscissors(self, interaction: discord.Interaction, choice: Literal["Rock", "Paper", "Scissors"] | None = None):
        await interaction.response.defer()
        
        botresult = random.choice(["rock", "paper", "scissors"])
        userresult = choice.lower() if choice else random.choice(["rock", "paper", "scissors"])

        beats = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }

        if botresult == userresult:
            finalresult = "It's a tie!"
            wincolor = discord.Color.gold()
        elif beats[userresult] == botresult:
            finalresult = f"{interaction.user.mention} has won the match!"
            wincolor = discord.Color.green()
        else:
            finalresult = f"{self.bot.user.mention} has won the match!"
            wincolor = discord.Color.red()

        rpsembed = discord.Embed(
            title="RPS Results",
            description="Here are the final results of the game Rock, Paper, & Scissors",
            color=wincolor
        )

        rpsembed.add_field(name=f"{self.bot.user.display_name}", value=botresult)
        rpsembed.add_field(name=f"{interaction.user.display_name}", value=userresult)
        rpsembed.add_field(name="Result", value=finalresult)

        self.set_requester_helper(rpsembed, interaction)

        await interaction.followup.send(embed=rpsembed)




    # ALIASES
    @app_commands.command(name="rockpaperscissors", description="Play rock paper scissors with a bot!")
    async def rps_alias(self, interaction: discord.Interaction, choice: Literal["Rock", "Paper", "Scissors"] | None = None):
        await self.rockpaperscissors(interaction, choice)


async def setup(bot: commands.Bot):
    await bot.add_cog(Minigames(bot))