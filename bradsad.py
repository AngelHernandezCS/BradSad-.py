import time, discord, requests, random
import oauth2 as oauth, urllib
import requests_oauthlib
import json
import pytz
from datetime import datetime, timedelta
from getschoologystuff import schoology as schoology
from db import database as database
import os

path = "https://api.schoology.com/v1"
userChannels = {}
userGuild = ""
keyentered = False
secretentered = False
tempuserkey = ""
tempusersecret = ""
tempusercode = ""
initializing = False
try:
    #creates the table
    database().createTable()
except:
    print("Table exists already")
class MyClient(discord.Client):
    async def on_ready(self):
        #bot logs in
        print('Logged on as {0}!'.format(self.user))
    
    async def on_guild_join(self, guild):
        #sends a welcome message when the bot joins a server
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(embed = welcomeEmbed(discord))
            break
    
    async def on_message(self, message):
        #runs the main functions based off the discord user's messsage
        if(message.author.id == self.user.id):
            return
        args = message.content.split()
        if (args[0]== "+help"):
            #sends an embeded message that shows all the commands if the user sends the command +help
            await message.channel.send(embed = helpEmbed(discord))
        elif(args[0] == "+init"):
            #sends a direct message to the user who sends the +init command and begins the process to get the schoology api key and secret
            db = database()
            if(db.checkguildInDb(message.guild.id) == None):
                #adds a new row to the table, adds the server id and discord user id as well
                db = database()
                db.addGuildID(message.guild.id, message.author.id)
                await message.author.send(embed = initEmbed(discord))
            else:
                #sends a message to the discord channel if a row with the same server id exists, or if someone else called the init command
                await message.channel.send(message.author.mention + "Someone has Already Called This Command")
        elif(args[0] == "+secret"):
            #adds the 'secret' api key to the table
            if(message.guild == None):
                #checks if the user is typing in the direct message the init embed was sent in
                userdb = database().checkuserInDb(message.author.id)
                if(userdb == None and database().getGuildProfile2(message.author.id)['key'] != None):
                    #checks if the init command has been sent yet
                    await message.channel.send("You Have Not used '+init' yet")
                elif(userdb != None and database().getGuildProfile2(message.author.id)['init'] == True and database().getGuildProfile2(message.author.id)['key'] != None):
                    #checks if the key and secret has been entered before in another discord server (or in another row in the table)
                    await message.channel.send("Your Secret and Key is already being used in another server. Please Have Someone else With the same class/classes set up the Bot\nIf You Believe this is a mistake and your key is being used without your permission use '+help' for more info on how to reset your key and secret")
                    database().deleteRow(database().getGuildProfile2(message.author.id)['guild'])  
                elif(userdb != None and database().getGuildProfile2(message.author.id)['init'] == False and database().getGuildProfile2(message.author.id)['secret'] == None and database().getGuildProfile2(message.author.id)['key'] != None):
                    #adds the secret to the table, checks to see if secret is valid as well
                    try:
                        database().addSecret(args[1], message.author.id)
                        try:
                            userkey = database().getGuildProfile2(message.author.id)['key']
                            userSecret = database().getGuildProfile2(message.author.id)['secret']
                            userGuildID = database().getGuildProfile2(message.author.id)['guild']
                            tempschool = schoology(userkey,userSecret)
                            tempuser = tempschool.getusercode()
                            if(tempuser == None):
                                database().deleteRow(database().getGuildProfile2(message.author.id)['guild'])
                                await message.channel.send("Invalid Secret or Key: Please use the command '+init' in your server again")
                            else:
                                #if secret has been successfully added then the schoology user id is added to the table tow as well
                                tempusercode = sortUser(schoology(userkey,userSecret))
                                database().addUsercode_id(tempusercode, userGuildID)
                                await message.author.send("Succesful you can now use the commands in your server\nUse '+help' too see available commands")
                        except:
                            database().deleteRow(database().getGuildProfile2(message.author.id)['guild'])
                            await message.channel.send("Invalid Secret or Key: Please use the command '+init' in your server again")
                    except:
                        await message.channel.send("invalid secret entry")
                elif(userdb != None and database().getGuildProfile2(message.author.id)['init'] == False and database().getGuildProfile2(message.author.id)['secret'] != None and database().getGuildProfile2(message.author.id)['key'] != None):
                    await message.channel.send("Already entered a Secret")
                elif(database().getGuildProfile2(message.author.id)['key'] == None):
                    await message.channel.send("Need to enter Key First with '+key'")       
            else:
                await message.channel.send("Please only use this command in direct messages" )
        elif(args[0] == "+key"):
            #adds the 'key' api key to the table if it is valid, is ran before +secret
            if(message.guild == None):
                userdb = database().checkuserInDb(message.author.id)
                if(userdb == None):
                    await message.channel.send("You Have Not used '+init' yet")
                elif(userdb != None and database().getGuildProfile2(message.author.id)['init'] == True):
                    await message.channel.send("Your Secret or Key is already being used in another server. Please Have Someone else With the same class/classes set up the Bot\nIf You Believe this is a mistake and your key is being used without your permission use '+help' for more info on how to reset your key and secret")
                    database().deleteRow(database().getGuildProfile2(message.author.id)['guild'])  
                elif(userdb != None and database().getGuildProfile2(message.author.id)['init'] == False and database().getGuildProfile2(message.author.id)['key'] == None):
                    try:
                        #adds the key to the row in the table
                        database().addKey(args[1], message.author.id)
                        await message.channel.send("Succesful Key add\n\nPlease use the command '+secret (enter secret here)' to add your Secret'")
                    except:
                        await message.channel.send("invalid key entry")
                elif(userdb != None and database().getGuildProfile2(message.author.id)['init'] == False and database().getGuildProfile2(message.author.id)['key'] != None):
                    await message.channel.send("Already entered a Key")       
            else:
                await message.channel.send("Please only use this command in direct messages" )
        elif(args[0] == "+reset"):
            #deletes the row in the table, and allows the user to user the +init command again
            if(message.guild != None):
                if(database().checkguildInDb(message.guild.id) == None):
                    await message.channel.send("Bot has not been initialized in this server yet")
                else:
                    database().deleteRow(message.guild.id)
                    await message.channel.send("Completed Rest run '+init' again")
        elif(args[0] == "+today"):
            #checks for all assignments due today for the selected class and sends an embeded message of the assignment with a decription
            if(message.guild != None):
                userDb = database().checkguildInDb(message.guild.id)
                if(userDb == None):
                    await message.channel.send("Pleas use '+init' command first and finish setup")
                elif(userDb != None and database().getGuildProfile(message.guild.id)['init'] == False):

                    await message.channel.send("Please finsih setup with '+init' command")
                else:
                    profile = database().getGuildProfile(message.guild.id)
                    userkey = profile['key']
                    usersecret = profile['secret']
                    classcode = profile['class_code']
                    try:
                        #looks through all assignments for the course and returns the assignments due today
                        assignmentDict = sortAssignments(schoology(userkey,usersecret),classcode)
                        cdate = getCurrentDate(False) #if false, then the date the functions sort through is today
                        assignmentDueList = checkDate(assignmentDict, userkey, usersecret, cdate, classcode)
                        if assignmentDueList != []:
                            for i in assignmentDueList:
                                #sends an embed message for every assignment due today
                                temp = assignmentDict[i]
                                await message.channel.send(embed = sendEmbed(discord,i,temp[3],cdate,temp[4], temp[2], temp[1], message.author.display_name, message.author.avatar_url))
                        else:
                            await message.channel.send(message.author.mention + " There are no assignments due today")
                    except KeyError:
                        await message.channel.send(message.author.mention + " There are no assignments due today")
            else:
                await message.channel.send("Please use this command in your Server")
        elif(args[0] == "+nextday"):
            #checks for all assignments due tomorrow and sends the same embed message as before the with assignment info
            if(message.guild != None):
                userDb = database().checkguildInDb(message.guild.id)
                if(userDb == None):
                    await message.channel.send("Pleas use '+init' command first and finish setup")
                elif(userDb != None and database().getGuildProfile(message.guild.id)['init'] == False):
                    await message.channel.send("Please finsih setup with '+init' command")
                else:
                    profile = database().getGuildProfile(message.guild.id)
                    userkey = profile['key']
                    usersecret = profile['secret']
                    classcode = profile['class_code']
                    try:
                        assignmentDict = sortAssignments(schoology(userkey,usersecret),classcode)
                        cdate = getCurrentDate(True) #if true, then the date the functions sort through is tomorrow
                        assignmentDueList = checkDate(assignmentDict, userkey, usersecret, cdate, classcode)
                        for i in assignmentDueList:
                            #sends an embed message for every assignment due tomorrow
                            temp = assignmentDict[i]
                            await message.channel.send(embed = sendEmbed(discord,i,temp[3],cdate,temp[4], temp[2], temp[1], message.author.display_name, message.author.avatar_url))
                    except KeyError:
                        await message.channel.send(message.author.mention + " There are no assignments due today")
            else:
                await message.channel.send("Please use this command in your Server")
        elif(args[0] == "+thisweek"):
            #checks for all assignments due the following seven days (including today) for the selected class
            if(message.guild != None):
                userDb = database().checkguildInDb(message.guild.id)
                if(userDb == None):
                    await message.channel.send("Pleas use '+init' command first and finish setup")
                elif(userDb != None and database().getGuildProfile(message.guild.id)['init'] == False):

                    await message.channel.send("Please finsih setup with '+init' command")
                else:
                    profile = database().getGuildProfile(message.guild.id)
                    userkey = profile['key']
                    usersecret = profile['secret']
                    classcode = profile['class_code']
                    try:
                        assignmentDict = sortAssignments(schoology(userkey,usersecret),classcode)
                        cdate = getCurrentDate(False)
                        week = getWeek() #a list of the seven days the command is based off of
                        for i in range(len(week)):
                            dayof = week[i]
                            assignmentDueList = checkDate(assignmentDict, userkey, usersecret, dayof, classcode)
                            if assignmentDueList != []:
                                await message.channel.send(message.author.mention +" Assignments due on "+ dayof+ ":")
                                for i in assignmentDueList:
                                    temp = assignmentDict[i]
                                    await message.channel.send(embed = sendEmbed(discord,i,temp[3],dayof,temp[4], temp[2], temp[1], message.author.display_name, message.author.avatar_url))
                        await message.channel.send("There are no other assignments due this week for this class")
                    except KeyError:
                        await message.channel.send(message.author.mention + " There are no assignments due this week")
            else:
                await message.channel.send("Please use this command in your Server")
        elif(args[0] == "+classes"):
            #shows a list of all the user's classes
            if(message.guild != None):
                userDb = database().checkguildInDb(message.guild.id)
                if(userDb == None):
                    await message.channel.send("Pleas use '+init' command first and finish setup")
                elif(userDb != None and database().getGuildProfile(message.guild.id)['init'] == False):
                    await message.channel.send("Please finsih setup with '+init' command")
                else:
                    #sorts through the user's classes and returns an embed message with the list of classes
                    profile = database().getGuildProfile(message.guild.id)
                    userkey = profile['key']
                    usersecret = profile['secret']
                    usercode = str(profile['user_code'])
                    classesDict = sortClasses(schoology(userkey, usersecret), usercode)
                    classesList = list(classesDict.values())
                    await message.channel.send(embed = sendClassEmbed(discord, message.author.display_name, message.author.avatar_url, classesList[0], classesList[1], classesList[2], classesList[3], classesList[4], classesList[5], classesList[6]))
            else:
                await message.channel.send("Please use this command in your Server")
        elif(args[0] == "+choose"):
            #chooses the class that the bot reminds assignments for, should ideally be ran after +classes so the user knows which number correlates to which class
            if(message.guild != None):
                userDb = database().checkguildInDb(message.guild.id)
                if(userDb == None):
                    await message.channel.send("Pleas use '+init' command first and finish setup")
                elif(userDb != None and database().getGuildProfile(message.guild.id)['init'] == False):
                    await message.channel.send("Please finsih setup with '+init' command")
                else:
                    profile = database().getGuildProfile(message.guild.id)
                    userkey = profile['key']
                    usersecret = profile['secret']
                    usercode = str(profile['user_code'])
                    classChosenList = sortChosenClass(args[1],userkey,usersecret,usercode)
                    if classChosenList == None:
                        await message.channel.send("Please choose a class within the list, it really isn't that hard.")
                    else:
                        #adds the class code to the table, to change it just run the +choose command again
                        classcode = classChosenList[0]
                        usercode = classChosenList[1]
                        database().addClasscode(classcode, message.guild.id)
                        await message.channel.send("You have selected **"+classChosenList[1]+"**, if this is not the class you want to view please resend the command.")
        else:
            return

def sendEmbed(disc, title, desc, date, typeof, points, time, author, authorurl):
    #Creates embed and returns it 
    embedVar = disc.Embed(title= title, description= desc, color=0x42f5f5)
    embedVar.set_author(name= author, icon_url= authorurl) #shows the user name and their avator at the top of the embed for aesthetic purposes 
    embedVar.set_thumbnail(url = "https://p11cdn4static.sharpschool.com/UserFiles/Servers/Server_141067/Image/sgy%20logo%20resized.png") #shows the schoology logo for aesthetic purposes
    embedVar.add_field(name="Assignment Type", value=typeof, inline=False)
    embedVar.add_field(name="Points Worth", value= points, inline=False)    
    embedVar.add_field(name="Time Due", value= time, inline=False)
    return embedVar

def sendClassEmbed(disc, author, authorurl, class1, class2, class3, class4, class5, class6, class7):
    #creates the embed to show the selected user's classes
    #should be followed by bot seeing which class it chose in classesList and set the class code accordingly
    embed= disc.Embed(title="Your Classes", description="Please choose which class you would like to view", color=0x5119d4)
    embed.set_author(name= author, icon_url= authorurl)
    embed.set_thumbnail(url="https://p11cdn4static.sharpschool.com/UserFiles/Servers/Server_141067/Image/sgy%20logo%20resized.png")
    embed.add_field(name="1. " , value=class1, inline=False)
    embed.add_field(name="2. " , value=class2, inline=False)
    embed.add_field(name="3. " , value=class3, inline=False)
    embed.add_field(name="4. " , value=class4, inline=False)
    embed.add_field(name="5. " , value=class5, inline=False)
    embed.add_field(name="6. " , value=class6, inline=False)
    embed.add_field(name="7. " , value=class7, inline=False)
    embed.set_footer(text="Please choose your class by typing +choose (1-7). Ex: '+choose 2' ")
    return embed

def helpEmbed(disc):
    #embeded message for the +help command, shows all the commands along with descriptions
    embed= disc.Embed(title = "HELP", description = ":arrow_down: :arrow_down: :arrow_down: :arrow_down: :arrow_down: :arrow_down:" , color=0xdc6f09)
    embed.set_thumbnail(url = "https://p11cdn4static.sharpschool.com/UserFiles/Servers/Server_141067/Image/sgy%20logo%20resized.png")
    embed.add_field(name="Setup Commands:", value=":tools:", inline=False)
    embed.add_field(name="+init", value="Initialization of the bot (Should be ran first).", inline=False)
    embed.add_field(name="+key ", value="Only used in direct messages with bot.", inline=True)
    embed.add_field(name="+secret", value="Only used in direct messages with bot.", inline=False)
    embed.add_field(name="+classes", value="Displays the list of classes you can see updates for.\n------------------------------------------------------------", inline=False)
    embed.add_field(name="General Commands:", value = ":gem:", inline=False)
    embed.add_field(name="+choose (#1-7)", value="Choose the number that corresponds with the class you would like to view. :warning: Note: *+classes should be ran first to see which class is what number.*", inline=False)
    embed.add_field(name="+today", value="Shows all assignments due today for the class you have selected.", inline=False)
    embed.add_field(name="+nextday", value="Shows all assignments due tomorrow for the class you have selected.", inline=False)
    embed.add_field(name="+thisweek", value="Shows all assignments due for the following week for the class you have selected.", inline=False)
    embed.add_field(name="+reset", value="Deletes your info from the bot's database. +init should be called again.\n----------------------------------------------------------- ", inline=True)
    embed.set_footer(text="If you have any further questions or suggestions contact BrandoWithTheLambo#3469")
    return embed

def welcomeEmbed(disc):
    #embeded message which should be sent when the bot joins the server
    embed = disc.Embed(title = "Thank you for adding me! :pray:", description = "My prefix is +", color=0x000000)
    embed.set_thumbnail(url = "https://p11cdn4static.sharpschool.com/UserFiles/Servers/Server_141067/Image/sgy%20logo%20resized.png")
    embed.add_field(name="See a list of commands by typing +help", value=":tools:", inline=True)
    embed.add_field(name = "Start up the bot by typing +init", value = ":magic_wand:", inline=True)
    embed.set_footer(text="If you have any further questions or suggestions contact BrandoWithTheLambo#3469")
    embed.set_image(url="https://cdn.discordapp.com/attachments/461448421320949764/512005978108067850/image0.gif")
    return embed

def initEmbed(disc):
    #embeded message that should be sent to the user in dm's 
    embed = disc.Embed(title = "For the following steps please vist your own Schoology page :computer:", description = 'The one you use everyday', color = 0xc738e0)
    embed.set_thumbnail(url = "https://p11cdn4static.sharpschool.com/UserFiles/Servers/Server_141067/Image/sgy%20logo%20resized.png")
    embed.add_field(name = "Then in the browser URL after the .com type /api :globe_with_meridians:", value = "The url should look like image at the bottom", inline = False)
    embed.set_image(url = "https://cdn.discordapp.com/attachments/795530791915749378/798278609760026714/unknown.png")
    embed.add_field(name = "Next type +key (your key from the site) :key: ", value = "Your message should look like '+key sdlfk332j22' ", inline = True)
    embed.add_field(name = "After the successful key add, type +secret (your secret from the api site) :lock:", value = "Your message should look like '+secret bvnxm321r'", inline = True)
    embed.set_footer(text="If you have any further questions or suggestions contact BrandoWithTheLambo#3469")
    return embed
    
def getCurrentDate(tomorrow):
    #gets the current date if tomorrow = False, gets the next day if tomorrow = True
    pst = pytz.timezone('America/Los_Angeles')
    tempDate = datetime.now(pst)
    tempLeapyear = tempDate.year % 4
    if tomorrow:
        if (tempDate.day == 31 and (tempDate.month == 1 or tempDate.month == 3 or tempDate.month == 5 or tempDate.month == 7 or tempDate.month == 8 or tempDate.month == 10 or tempDate.month == 12)):
            tempDate = tempDate.replace(month = tempDate.month + 1)
            tempDate = tempDate.replace(day = 1)
        elif (tempDate.day == 30 and (tempDate.month == 4 or tempDate.month == 6 or tempDate.month == 9 or tempDate.month == 11)):
            tempDate = tempDate.replace(month = tempDate.month + 1)
            tempDate = tempDate.replace(day = 1)
        elif (tempDate.day == 28 and tempDate.month == 2 and tempLeapyear != 0):
            tempDate = tempDate.replace(month = tempDate.month + 1)
            tempDate = tempDate.replace(day = 1)
        elif (tempDate.day == 29 and tempDate.month == 2 and tempLeapyear == 0):
            tempDate = tempDate.replace(month = tempDate.month + 1)
            tempDate = tempDate.replace(day = 1)
        else: 
            tempDate = tempDate.replace(day = tempDate.day + 1)
    dateAndTime = str(tempDate).split()
    currentDate = dateAndTime[0]
    print("The current date is:", currentDate)
    return currentDate

def convertTime(milTime):
    #function that changes the time from military to standard so it is legible
    temptime = milTime[1].split(':')
    temptime[0] = int(temptime[0]) 
    if (temptime[0] > 12):
        temptime[0] -= 12
        temptime[2] = "PM"
    else:
        temptime[2] = "AM"
    standardTime = str(temptime[0]) + ':' + temptime[1] + ' '+ temptime[2]
    return standardTime

def sortAssignments(school, classcode):
    #loops through all assignments and assigns the tite and date to a dictionary where the keys are the titles and the values are the date, points, dassignment description, and assignment type
    sc = school
    starter = 0
    limiter = 20
    assignmentCounter = 0
    scgetcourses = sc.getassignments(starter, limiter, classcode)
    scgetassignments = scgetcourses['assignment']
    tempDict = {}
    for i in scgetassignments:
        assignmentDueDateandTime = i['due'].split()
        assignmentDueDateandTime[1] = convertTime(assignmentDueDateandTime)
        tempDict[i['title']] = [assignmentDueDateandTime[0], assignmentDueDateandTime[1],i['max_points'],i['description'],i['type']]
        assignmentCounter += 1
        if(assignmentCounter == 20):
            #resets the limit and calls the getassignments module again to get all assignments 
            #schoology puts a limit on how much you can call from the site
            assignmentCounter = 0
            starter += 20
            limiter += 20
            scgetcourses = sc.getassignments(starter, limiter, classcode)
            for x in scgetcourses['assignment']:
                #gets the next set of assignments 
                scgetassignments.append(x)
    return tempDict

def sortClasses(school, userscode):
    #sorts through the user's courses and places them in a dictionary with the course name and the class id
    sc = school 
    scgetuserinfo = sc.getusercourses(userscode)
    scgetallcourses = scgetuserinfo['section']
    tempDict = {}
    for i in scgetallcourses:
        tempDict[i['id']] = i['course_title']
    return tempDict

def sortUser(school):
    #sorts through the user's information and gets the user's id
    sc = school 
    scgetusercode = sc.getusercode()
    tempList = [""]
    tempList[0] = scgetusercode['uid']
    return tempList[0]

def sortChosenClass(num,key,secret,usercode):
    #takes the input of the user which is a number 1-7 and and matches the class to the class code
    classesDict = sortClasses(schoology(key, secret), usercode)
    classesList = list(classesDict.values())
    classesID = list(classesDict.keys())
    classchoiceName = ''
    classchoiceCode = ''
    if (num == '1'):
        classchoiceName = classesList[0]
        classchoiceCode = classesID[0]
    elif (num == '2'):
        classchoiceName = classesList[1]
        classchoiceCode = classesID[1]
    elif (num == '3'):
        classchoiceName = classesList[2]
        classchoiceCode = classesID[2]
    elif (num == '4'):
        classchoiceName = classesList[3]
        classchoiceCode = classesID[3]
    elif (num == '5'):
        classchoiceName = classesList[4]
        classchoiceCode = classesID[4]
    elif (num == '6'):
        classchoiceName = classesList[5]
        classchoiceCode = classesID[5]
    elif (num == '7'):
        classchoiceName = classesList[6]
        classchoiceCode = classesID[6]
    else:
        return None
    return [classchoiceCode, classchoiceName]

def getWeek():
    #returns a list of the days of the following week
    weekList = []
    pst = pytz.timezone('America/Los_Angeles')
    cdate = datetime.now(pst)
    for i in range(7):
        tdate = cdate + timedelta(days = i)
        dateAndTime = str(tdate).split()
        weekList.append(dateAndTime[0])
    return weekList

def checkDate(dict, key, secret, date, classc):
    #sorts through the dates of the assignment and returns a list of the assignments that are due regardless if the date is the same
    times = list(sortAssignments(schoology(key, secret),classc).values())
    names = list(sortAssignments(schoology(key, secret),classc).keys())
    listofdue = []
    for i in range(len(times)):
        templist = times[i]
        if date == templist[0]:
            listofdue.append(names[i])
    return listofdue

client = MyClient()
client.run(os.environ['token'])
