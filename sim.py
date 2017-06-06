import discord
import json
import os
import re
import subprocess
import sys
from bs4 import BeautifulSoup

client = discord.Client()
with open('config.json') as config_data:
    config_json = json.load(config_data)
    api_key = config_json['api_key']
    simcraft_path = config_json['path']
    token = config_json['discord_token']
character = str(sys.argv[1])
server = str(sys.argv[2])
channel = str(sys.argv[3])
author = sys.argv[4]

def pawn_strip(character, server):
    with open('%s%s-%s.html' % (simcraft_path, character, server), encoding='utf8') as infile:
        soup = BeautifulSoup(infile, "html.parser")
        return soup.find(text=re.compile(' Pawn: v1: '))

@client.event
async def on_ready():
        for x in config_json['servers']:
            client.accept_invite(x)
        await client.send_message(client.get_channel(channel), '%s: Stat weight simulation on %s completed.' % (author, character))
        await client.send_message(client.get_channel(channel), '%s: %s' % (author, pawn_strip(character, server)))
        await client.logout()

subprocess.call('%ssimc.exe armory=us,%s,%s calculate_scale_factors=1 scale_only=strength,agility,intellect,crit_rating,haste_rating,mastery_rating,versatility_rating iterations=10000 html=%s-%s.html output=%s.txt' % (simcraft_path, server, character, character, server, character), cwd=simcraft_path)
client.run(token)
