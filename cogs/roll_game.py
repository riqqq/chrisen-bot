# Importing libraries
import discord
import os
import asyncio
import random
from discord.ext import commands

class roll_game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gameStarted = False
        self.firstRoll = True
        self.lastNumber = 0

    @commands.command()
    async def start_roll(self, ctx, member: discord.Member = None):
        if member is None:
            await ctx.send('No member specified to roll with!')

        self.gameStarted = True
        await ctx.send(f'{member.mention} you were challenged to deathroll by {ctx.author.mention}!')

    @commands.command()
    async def roll(self, ctx, number: int = 0):
        if self.gameStarted is False:
            await ctx.send('There is no ongoing game! Use !start_roll first')
            return
        
        if self.firstRoll is True and number != 0:
            self.lastNumber = random.randint(1, number)
            self.firstRoll = False
        elif self.firstRoll is False:
            self.lastNumber = random.randint(1, self.lastNumber)
            if number != 0:
                await ctx.send('Don\'t specify a number, you can roll using just !roll after the first one!')
        else:
            await ctx.send(f'{ctx.author.mention} you need to specify a number when using !roll for the first time!')

        if self.lastNumber == 0:
            return
        elif self.lastNumber == 1:
            self.gameStarted = False
            await ctx.send(f'{ctx.author.mention} has rolled {self.lastNumber}')
            await ctx.send(f'End! {ctx.author.mention} has lost deathroll!')
        else:
            await ctx.send(f'{ctx.author.mention} has rolled {self.lastNumber}')

async def setup(bot):
    await bot.add_cog(roll_game(bot))
