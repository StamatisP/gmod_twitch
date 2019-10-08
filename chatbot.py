from twitchobserver import Observer
from collections import namedtuple
import asyncio
import websockets
import time
import os
import sys
import configparser
from colorama import Fore, Back, init, deinit

init()

global inc_msg
inc_msg = "null"
global chatMessages
chatMessages = []
global votes
votes = []
ChatMessage = namedtuple('Chat', 'nick message')
global voting_time
voting_time = False
global anarchy_mode
anarchy_mode = False
global obs_created
obs_created = False
try:
    with open("config.ini") as f:
        config = configparser.ConfigParser()
        config.read('config.ini')
        TwitchChannel = config['tgm']['twitchchannel']
        BotName = config['tgm']['botname']
        BotOauth = config['tgm']['botoauth']
        f.close()
except FileNotFoundError:
    print("File does not exist, user input time.")
    config = configparser.ConfigParser()
    config.read("config.ini")
    TwitchChannel = input("Enter the name of your Twitch channel (where you will stream), in lowercase: ")
    TwitchChannel.lower()
    BotName = input("Now enter the name of your bot account, in lowercase: ")
    BotName.lower()
    BotOauth = input("Now copy-paste the bot's oauth token (http://twitchapps.com/tmi/): ")
    BotOauth.lower()
    config.add_section('tgm')
    config.set('tgm', 'twitchchannel', TwitchChannel)
    config.set('tgm', 'botname', BotName)
    config.set('tgm', 'botoauth', BotOauth)
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

#clear = lambda: os.system('cls')
#clear()
print("\n")
print(Fore.GREEN + "------------------------")
print(Fore.WHITE + "STARTUP AT " + time.strftime("%H:%M:%S", time.gmtime()))
print(Fore.GREEN + "------------------------")
print("\n")


def do_command(cmd, user):
    global inc_msg
    if voting_time:
        inc_msg = "VoteInfo"
        return
    if cmd == "votetime":
        if user == TwitchChannel:
            inc_msg = cmd
    else:
        inc_msg = "null"


def handle_event(event):
    global votes
    global voting_time
    if event.type != 'TWITCHCHATMESSAGE':
        return

    if event.message[:1] == "!":
        cmd = event.message.split(' ')[0][1:].lower()
        print(Fore.CYAN + "received command " + cmd)
        if voting_time:
            votes.append(ChatMessage(event.nickname, event.message))
        do_command(cmd, event.nickname)
    else:
        global inc_msg
        inc_msg = "PrintTwitchChat"
        chatMessages.append(ChatMessage(event.nickname, event.message))


async def main_program(websocket, path):
    global inc_msg
    global voting_time
    global anarchy_mode
    global obs_created
    if not obs_created:
        print(Fore.CYAN + "creating observer")
        obs = Observer(BotName, BotOauth)
        obs.start()
        obs.join_channel(TwitchChannel)
        obs.send_message('hello!', TwitchChannel)
        obs.subscribe(handle_event)
        print(Fore.CYAN + "done creating")
        obs_created = True
    async for message in websocket:
        if message != "ConnTest": print(Fore.YELLOW + message + " " + time.strftime("%H:%M:%S", time.gmtime()))
        if inc_msg != "null": print(Fore.MAGENTA + inc_msg)
        if message == "Connected Message!":
            await websocket.send("Serv connect!")
            print(Fore.YELLOW + "connected!")
        elif message == "ConnTest":
            if inc_msg == "votetime":
                print(Fore.YELLOW + "time to vote!")
                voting_time = True
                await websocket.send(inc_msg)
            elif inc_msg == "VoteInfo":
                print("sending info")
                for i in votes:
                    #print(i)
                    await websocket.send("VoteInfo\n" + i.nick + "\n" + i.message)
                votes.clear()
            elif inc_msg == "PrintTwitchChat":
                for i in chatMessages:
                    #print(i)
                    await websocket.send("PrintTwitchChat\n" + i.nick + "\n" + i.message)
                chatMessages.clear()
            else:
                if anarchy_mode: await websocket.send(inc_msg)
            inc_msg = "null"
        elif message == "VoteTime":
            voting_time = True
        elif message == "VoteOver":
            voting_time = False
        elif message == "anarchymode":
            anarchy_mode = True
        elif message == "democracymode":
            anarchy_mode = False
        elif message == "shutdown":
            obs.send_message('shutting down!', TwitchChannel)
            start_server.ws_server.close()
            asyncio.get_event_loop().stop()
            obs.leave_channel(TwitchChannel)
            obs.stop()
            deinit()
            os.execv(sys.executable, ['python'] + ['chatbot.py'])
            #os.startfile(__file__)
            #print(os.path.abspath(os.path.dirname(__file__)))
            #print(__file__)
            #os.execv(__file__, *sys.argv)


start_server = websockets.serve(main_program, "localhost", 8765)
'''serv_t = threading.Thread(target=start_server)
serv_t.daemon = True
serv_t.start()'''
print(Fore.YELLOW + "starting websocket")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()