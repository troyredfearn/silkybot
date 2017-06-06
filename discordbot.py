import discord
import json
import os
import re
import requests
import subprocess
import time
from string import punctuation
from bs4 import BeautifulSoup

client = discord.Client()

with open('config.json') as config_data:
    config_json = json.load(config_data)
    api_key = config_json['api_key']
    simcraft_path = config_json['path']
    token = config_json['discord_token']

with open('strings.json') as strings_json:
    strings = json.load(strings_json)

# Returns true if character exists on armory, false otherwise
def char_exists(character,server):
    try:
        requests.get('https://us.api.battle.net/wow/character/%s/%s?locale=en_US&apikey=%s' % (server, character, api_key))
        return True
    except:
        return False

# Removes strip from message, and returns Charactername in a message formatted 'charactername-servername'
def char_strip(message, strip):
    character = message.replace("%s" % strip, "")
    head, sep, tail = character.partition('-')
    head = punc_strip(head)
    return head.capitalize()

# Returns Servername from '!command charactername-servername' input
def server_strip(message):
    head, sep, tail = message.partition('-')
    return tail.capitalize()

# Returns string stripped of all punctuation
def punc_strip(string):
    return ''.join(char for char in string if char not in punc)

# Returns a pawn string from simcraft output
def pawn_strip(character, server):
    with open('%s%s-%s.html' % (simcraft_path, character, server), encoding='utf8') as infile:
        soup = BeautifulSoup(infile, "html.parser")
        return soup.find(text=re.compile(' Pawn: v1: '))

# Returns armory update time
def armory_date(character, server):
    armory_json = requests.get(strings["char_url"] % (server, character, api_key))
    armory_json = armory_json.json()
    update_time = armory_json['lastModified']
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(update_time / 1000))

# Returns role
def get_role(character, server):
    armory_json = requests.get(strings["char_url"] % (server, character, api_key))
    armory_json = armory_json.json()
        role = armory_json['talents'][0]['spec']['role']
        return role

# Returns spec
def get_spec(character, server):
    armory_json = requests.get(strings["char_url"] % (server, character, api_key))
    armory_json = armory_json.json()
        spec_name = armory_json['talents'][0]['spec']['name']
        return spec_name

# Returns true if DPS role, false if any other role
def is_dps(character, server):
    role = get_role(character, server)
    if role == "DPS":
        return True
    else:
        return False

# Returns true if Healer role, false if any other role
def is_healer(character, server):
    role = get_role(character, server)
    if role == "HEALER":
        return True
    else:
        return False

# Returns true if Tank role, false if any other role
def is_tank(character, server):
    role = get_role(character, server)
    if role == "TANK":
        return True
    else:
        return False

# On ready, joins all servers in JSON
@client.event
async def on_ready():
    for x in config_json['servers']:
        client.accept_invite(x)
    print('Logged in as')
    print(client.user.name)
    print('---------')

@client.event
async def on_message(message):
    author = message.author
    if message.content.startswith('!sim '):
        character = char_strip(message.content, '!sim ')
        server = server_strip(message.content)
        if char_exists(character, server):
            if not is_healer(character, server):
                await client.send_message(message.channel, strings['start_message'] % (author.mention, character, server))
                await client.send_message(message.channel, strings['updated_message'] % (author.mention, get_spec(character, server), armory_date(character, server)))
                subprocess.Popen('python sim.py %s %s %s %s /C' % (character, server, message.channel.id, author.mention))
            else is_healer(character, server):
                await client.send_message(message.channel, ['healer_message'] % author.mention)
        else:
            await client.send_message(message.channel, strings['not_found_message']  % (author.mention, character, server))

    if message.content.startswith('!help'):
        await client.send_message(message.channel, strings['help_message'])
        await client.send_message(message.channel, strings['armory_disclaimer'])

    if message.content.startswith('!dps '):
        character = char_strip(message.content, '!dps ')
        server = server_strip(message.content)
        if char_exists(character, server):
            if not is_healer(character, server):
                await client.send_message(message.channel, strings['dps_message'] % (author.mention, character, server))
                await client.send_message(message.channel, strings['updated_message'] % (author.mention, get_spec(character, server), armory_date(character, server)))
                subprocess.Popen('python dps.py %s %s %s %s /C' % (character, server, message.channel.id, author.mention))
            else:
                await client.send_message(message.channel, strings['healer_message'] % author.mention)
        else:
            await client.send_message(message.channel, strings['not_found_message'] % (author.mention, character, server))


client.run(token)
