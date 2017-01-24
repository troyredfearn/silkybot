import discord
import json
import subprocess
import os
import datetime
import requests
import re
from string import punctuation
from bs4 import BeautifulSoup
import time

client = discord.Client()
with open('config.json') as config_data:
    config_json = json.load(config_data)
    api_key = config_json['api_key']
    simcraft_path = config_json['path']
    token = config_json['discord_token']

#Returns true if character exists on armory, false otherwise
def char_exists(character,server):
    try:
        requests.get('https://us.api.battle.net/wow/character/%s/%s?locale=en_US&apikey=%s' % (server, character, api_key))
        return True
    except:
        return False

#Removes strip from message, and returns Charactername in a message formatted 'charactername-servername'
def charstrip(message, strip):
    character = message.replace("%s" % strip, "")
    head, sep, tail = character.partition('-')
    head = puncstrip(head)
    return head.capitalize()

#Returns Servername from '!command charactername-servername' input
def serverstrip(message):
    head, sep, tail = message.partition('-')
    return tail.capitalize()

#Returns s stripped of all punctuation
def puncstrip(s):
    return ''.join(c for c in s if c not in punctuation)

#Returns a pawn string from simcraft output
def pawnstrip(character, server):
    with open('%s%s-%s.html' % (simcraft_path, character, server), encoding='utf8') as infile:
        soup = BeautifulSoup(infile, "html.parser")
        return soup.find(text=re.compile(' Pawn: v1: '))

#Returns modified date of a file in local time        
def mod_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

#Returns armory update time
def armory_date(character, server):
    armory_json = requests.get('https://us.api.battle.net/wow/character/%s/%s?locale=en_US&apikey=%s' % (server, character, api_key))
    armory_json = armory_json.json()
    update_time = armory_json['lastModified']
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(update_time / 1000))

#Returns true if DPS role, false if any other role
def is_dps(character, server):
    armory_json = requests.get('https://us.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_US&apikey=%s' % (server, character, api_key))
    armory_json = armory_json.json()
    for i in range(0,7):
        try:
            armory_json['talents'][0]['talents'][i]['spec']['role'] == 'DPS'
            return armory_json['talents'][0]['talents'][i]['spec']['role'] == 'DPS'
        except:
            print('No spec identifier in tier %s.' % i)

#Returns role            
def get_role(character, server):
    armory_json = requests.get('https://us.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_US&apikey=%s' % (server, character, api_key))
    armory_json = armory_json.json()
    for i in range(0,7):
        try:
            x = armory_json['talents'][0]['talents'][i]['spec']['role']
            return x
        except:
            print('No role identifier in tier %s.' % i)

#Returns spec    
def get_spec(character, server):
    armory_json = requests.get('https://us.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_US&apikey=%s' % (server, character, api_key))
    armory_json = armory_json.json()
    for i in range(0,7):
        try:
            x = armory_json['talents'][0]['talents'][i]['spec']['name']
            return x
        except:
            print('No spec identifier in tier %s.' % i)

@client.event
async def on_ready():
#On ready, joins all servers in JSON
    for x in config_json['servers']:
        client.accept_invite(x)
    print('Logged in as')
    print(client.user.name)
    print('---------')
    
@client.event
async def on_message(message):
    author = message.author
    if message.content.startswith('!sim '):
        character = charstrip(message.content, '!sim ')
        server = serverstrip(message.content)
        if char_exists(character, server):
            if is_dps(character, server):
                await client.send_message(message.channel, '%s: Simming stats for %s - %s. Concurrent simulations will slow me down, so wait your turn! Please be gentle... I\'m delicate :^)' % (author.mention, character, server))
                await client.send_message(message.channel, '%s: Current spec: %s. Armory info last updated %s' % (author.mention, get_spec(character, server), armory_date(character, server)))
                subprocess.Popen('python sim.py %s %s %s %s /C' % (character, server, message.channel.id, author.mention))
            else:
                if (get_role(character, server) == 'TANK'):
                    await client.send_message(message.channel, '%s: Simming stats for %s - %s. These stats are for DPS, not survivability. Concurrent simulations will slow me down, so wait your turn! Please be gentle... I\'m delicate :^)' % (author.mention, character, server))
                    await client.send_message(message.channel, '%s: Current spec: %s. Armory info last updated %s' % (author.mention, get_spec(character, server), armory_date(character, server)))
                    subprocess.Popen('python sim.py %s %s %s %s /C' % (character, server, message.channel.id, author.mention))
                if (get_role(character, server) == 'HEALING'):
                    await client.send_message(message.channel, '%s: Sorry, sims do not work for healers. This is a limitation of SimulationCraft.' % author.mention)
        else:
            await client.send_message(message.channel, '%s: Character %s-%s not found. Make sure your format is \'!sim charactername-servername\'.' % (author.mention, character, server))    
    if message.content.startswith('!help'):
        await client.send_message(message.channel, 'To simulate: \'!sim charactername-servername\'. Takes a few minutes depending on load. You will get a message when it is completed.')    
        await client.send_message(message.channel, 'Character data is pulled from the Armory, so it may not always be up to date.')
    if message.content.startswith('!dps '):
        character = charstrip(message.content, '!dps ')
        server = serverstrip(message.content)
        if char_exists(character, server):
            if(get_role(character, server) != 'HEALING'):
                await client.send_message(message.channel, '%s: Simming DPS for %s - %s. Concurrent simulations will slow me down, so wait your turn! Please be gentle... I\'m delicate :^)' % (author.mention, character, server))
                await client.send_message(message.channel, '%s: Current spec: %s. Armory info last updated %s' % (author.mention, get_spec(character, server), armory_date(character, server)))
                subprocess.Popen('python dps.py %s %s %s %s /C' % (character, server, message.channel.id, author.mention))
            else:
                await client.send_message(message.channel, '%s: Sorry, sims are not available for healers. This is a limitation of SimulationCraft.' % author.mention)
        else:
            await client.send_message(message.channel, '%s: Character %s-%s not found. Make sure your format is \'!sim charactername-servername\'.' % (author.mention, character, server))


client.run(token)