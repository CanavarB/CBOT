import json
import os
from discord.ext import commands
import discord

def read_json(path) -> dict:
    with open(path, 'r', encoding="utf-8") as jsonFile:
        db = json.load(jsonFile)
        jsonFile.close()
        return db

def upper(string : str) -> str:
    
    PAIRS = [('i','İ'), ('ğ','Ğ'),('ü','Ü'), ('ş','Ş'), ('ö','Ö'),('ç','Ç'),('ı','I')]
    
    for low, up in PAIRS:
        string = string.replace(low, up)

    return string.upper()

def bold(string : str) -> str:
    return f'**{string}**'
def italic(string: str) -> str:
    return f'*{string}*'
def quote(string: str) -> str:
    return f'>>> {string}'

def get_Cogs(cogspath):
    cogs = list()
    for filename in os.listdir(cogspath):
        if filename.endswith('.py') and not filename.startswith('_'):
            cogs.append(f'extensions.cogs.{filename[:-3]}') #TODO:fix path
    return cogs
def get_Commands(commandpath):
    commands = list()
    for filename in os.listdir(commandpath):
        if filename.endswith('.py'):
            commands.append(f'extensions.commands.{filename[:-3]}')
    return commands
def get(iterable, /, **attrs):
    return discord.utils.get(iterable=iterable, attrs=attrs)