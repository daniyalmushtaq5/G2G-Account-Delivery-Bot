from g2gbot import G2GDeliveryBot
import datetime

file = open(r'C:\Users\BABAR\Desktop\g2g-delivery-bot-modified\log_5.txt','a')

file.write(f'{datetime.datetime.now()} - the script start running \n')

bot = G2GDeliveryBot("Profile 5")
bot.run()

file = open(r'C:\Users\BABAR\Desktop\g2g-delivery-bot-modified\log_5.txt','a')

file.write(f'{datetime.datetime.now()} - the script has successfully ran\n')