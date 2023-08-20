import os
import time
import pymongo
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = '13487236'
API_HASH = 'c869e87de280d98b363fced8e492ab40'
MONGODB_URI = 'mongodb+srv://admin:admin@cluster0.iteow9t.mongodb.net/?retryWrites=true&w=majority'
CHANNEL_USERNAME = 'StartAnimeFF_wallpappers'  # Replace with your channel username
OWNER_ID = 5491384523  # Replace with your own user ID

client = Client("my_account", api_id=API_ID, api_hash=API_HASH)

mongo_client = pymongo.MongoClient(MONGODB_URI)
db = mongo_client['file_renaming_bot']
collection = db['renamed_files']

CHOOSE_FILE, ENTER_NEW_NAME, CUSTOM_THUMBNAIL = range(3)

@client.on_message(filters.command(["start"]))
def start(_, update):
    update.reply_text("Hello! I'm a file renaming bot. Send /rename to get started.")

@client.on_message(filters.command(["rename"]))
def check_subscription(_, update):
    user = update.from_user
    chat_member = client.get_chat_member(CHANNEL_USERNAME, user.id)
    
    if chat_member.status == "member" or chat_member.status == "administrator" or chat_member.status == "creator":
        update.reply_text("Thank you for subscribing! You can now use the bot.")
        return rename_start(_, update)
    else:
        update.reply_text("Please subscribe to my channel to use this bot.")
        update.reply_text(f"Subscribe to the channel here: https://t.me/{CHANNEL_USERNAME}")

@client.on_message(filters.private & filters.command(["rename"]))
def rename_start(_, update):
    update.reply_text("Please send me the file you want to rename.")
    return CHOOSE_FILE

@client.on_message(filters.private & filters.document.mime("application/octet-stream"))
def choose_file(_, update):
    # ...
    return ENTER_NEW_NAME

@client.on_message(filters.private & filters.photo)
def set_thumbnail_and_enter_name(_, update):
    context.user_data['custom_thumbnail'] = True
    file_id = update.photo[-1].file_id
    context.user_data['thumbnail_file_id'] = file_id
    update.reply_text("Great! Please enter the new name for the file.")
    return ENTER_NEW_NAME

@client.on_message(filters.private & filters.text)
def enter_new_name(_, update):
    new_filename = update.text
    context.user_data['new_filename'] = new_filename
    keyboard = [[
        InlineKeyboardButton("Document", callback_data="document"),
        InlineKeyboardButton("Video", callback_data="video"),
    ]]
    markup = InlineKeyboardMarkup(keyboard)
    update.reply_text("Do you want the renamed file back as a Document or a Video?", reply_markup=markup)
    return CUSTOM_THUMBNAIL

@client.on_callback_query(filters.regex("document|video"))
def custom_thumbnail(_, update):
    choice = update.data
    context.user_data['custom_thumbnail'] = (choice == 'document')
    
    file = context.user_data['file']
    new_filename = context.user_data['new_filename']
    
    # Download file with progress
    with update.reply_to_message.document.download(
        file_name='temp_file',
        progress=progress_bar,
        progress_args=(update.chat.id,)
    ):
        pass
    
    if context.user_data.get('custom_thumbnail'):
        thumbnail_file_id = context.user_data.get('thumbnail_file_id')
        if thumbnail_file_id:
            context.bot.download_media(thumbnail_file_id, file_name='thumbnail.jpg')
            # You can implement thumbnail handling here
        
    with open('temp_file', 'rb') as renamed_file:
        if choice == 'document':
            update.message.reply_document(document=renamed_file)
        elif choice == 'video':
            update.message.reply_video(video=renamed_file)
    
    collection.insert_one({'user_id': update.from_user.id, 'old_filename': file.file_name, 'new_filename': new_filename})

@client.on_message(filters.command(["owner"]))
def owner_command(_, update):
    if update.from_user.id == OWNER_ID:
        update.reply_text("Hello Owner! You have special commands available.")
    else:
        update.reply_text("Sorry, you're not the owner of this bot.")

def progress_bar(current, total, chat_id):
    percentage = current * 100 / total
    speed = current // 1024 // (time.time() - context.user_data['start_time'])
    eta = (total - current) // speed
    text = f"Progress: {current} / {total} bytes\nSpeed: {speed} KB/s\nETA: {eta} seconds\nDone: {percentage:.2f}%"
    client.send_message(chat_id, text)

def main():
    client.run()

if __name__ == "__main__":
    main()
