import subprocess
import sys
import discord
import json
from bs4 import BeautifulSoup
import re
import os
import datetime

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

def damagestrip(character, server):
    with open('%s%s-%s-dps.html' % (simcraft_path, character, server), encoding='utf8') as infile:
        soup = BeautifulSoup(infile, "html.parser")
        return soup.find(text=re.compile(' dps'))
    
def mod_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

@client.event
async def on_ready():
        for x in config_json['servers']:
            client.accept_invite(x)
        await client.send_message(client.get_channel(channel), '%s: DPS simulation on %s completed.' % (author, character))
        await client.send_message(client.get_channel(channel), '%s: %s' % (author, damagestrip(character, server)))
        await client.logout()

subprocess.call('%ssimc.exe armory=us,%s,%s calculate_scale_factors=0 iterations=10000 html=%s-%s-dps.html output=%s-dps.txt fight_style=LightMovement' % (simcraft_path, server, character, character, server, character), cwd=simcraft_path)
client.run(token)