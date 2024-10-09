from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
import datetime
import pickle, os, sys

TOKEN = os.getenv('BOT_TOKEN')
if TOKEN == None:
    print(f'Error, run script with BOT_TOKEN=xxxxx python bot.py')
    sys.exit(1)

# ID du topic où envoyer le message après confirmation
THREAD_ID = 488  # Remplace cet ID par l'ID réel du thread/topic

# ID du groupe où se trouve le topic (groupe supergroupe ou forum)
GROUP_ID = -1002227661495  # Remplace cet ID par l'ID de ton supergroupe ou forum

# Les états pour la conversation
CHOOSING_CLUB, CHOOSING_DATE, CHOOSING_HOUR, CHOOSING_MINUTE, CHOOSING_DURATION, CHOOSING_LEVEL, CONFIRMATION = range(7)

# La liste des clubs
CLUBS = ["Garisart", "Bonnevoie", "CK", "Sports4Lux", "Lexy", "Léglise", "Saint-Mard"]
DATES = [(datetime.date.today() + datetime.timedelta(days=i)).strftime('%d-%m-%Y') for i in range(10)]
HOURS = [f"{i:02d}" for i in range(9, 23)]
MINUTES = ["00", "30"]
DURATIONS = [60, 90, 120]
LEVELS = [str(x / 2) for x in range(2, 21)]

# Variable pour garder la référence du message posté et son contenu
#posted_message_info = None

#CACHE_MATCH_MSG = {}
CACHE_FILE = '/tmp/bot-telegram-cache.pickle'

def commit_cache():
    global CACHE_MATCH_MSG
    newcache = CACHE_MATCH_MSG.copy()
    for i in CACHE_MATCH_MSG:
        date = CACHE_MATCH_MSG[i]['date']
        if datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) > datetime.datetime.strptime(date, "%d-%m-%Y"):
            del(newcache[i])
            print(f'Match {i} removed from cached, expired, {date}')
    CACHE_MATCH_MSG = newcache
    del(newcache)
    with open(CACHE_FILE, "wb") as outfile:
        pickle.dump(CACHE_MATCH_MSG, outfile)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Démarrer la conversation et poser la première question."""
    keyboard = [[InlineKeyboardButton(club, callback_data=club)] for club in CLUBS]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Club ?", reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text("Club ?", reply_markup=reply_markup)

    return CHOOSING_CLUB

async def choose_club(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Récupérer la réponse du club et passer à la question suivante."""
    query = update.callback_query
    await query.answer()
    context.user_data['club'] = query.data
    keyboard = [[InlineKeyboardButton(date, callback_data=date)] for date in DATES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Club : {context.user_data.get('club')}\nDate ?", reply_markup=reply_markup)
    return CHOOSING_DATE


async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Récupérer la date et passer à la confirmation."""
    query = update.callback_query
    await query.answer()
    user_date = query.data
    context.user_data['date'] = user_date
    keyboard = [[InlineKeyboardButton(hour, callback_data=hour)] for hour in HOURS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Select Hour :", reply_markup=reply_markup)    
    await query.edit_message_text(f"Club : {context.user_data.get('club')}\nDate : {context.user_data.get('date')}\nHour ?", reply_markup=reply_markup)
    return CHOOSING_HOUR

async def choose_hour(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['hour'] = query.data
    keyboard = [[InlineKeyboardButton(minute, callback_data=minute)] for minute in MINUTES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Club : {context.user_data.get('club')}\nDate : {context.user_data.get('date')}\nHour : {context.user_data.get('hour')}\nMinute ?", reply_markup=reply_markup)  
    return CHOOSING_MINUTE

async def choose_minute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['minute'] = query.data
    keyboard = [[InlineKeyboardButton(str(length), callback_data=str(length))] for length in DURATIONS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Club : {context.user_data.get('club')}\nDate : {context.user_data.get('date')}\nHour : {context.user_data.get('hour')}\nMinute : {context.user_data.get('minute')}\nDuration ?", reply_markup=reply_markup)  
    return CHOOSING_DURATION

async def choose_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['duration'] = query.data
    keyboard = [[InlineKeyboardButton(level, callback_data=level)] for level in LEVELS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Club : {context.user_data.get('club')}\nDate : {get_horaire(context.user_data.get('date'), context.user_data.get('hour'), context.user_data.get('minute'), context.user_data.get('duration'))}\nLevel ?", reply_markup=reply_markup)  
    return CHOOSING_LEVEL

def get_horaire(date, hour, minute, duration):
    start_time = datetime.datetime.strptime(
        f"{date} {hour}:{minute}", '%d-%m-%Y %H:%M'
    )
    end_time = start_time + datetime.timedelta(minutes=int(duration))
    start_time = start_time.strftime('%H:%M')
    end_time = end_time.strftime('%H:%M')
    return f'{date} {start_time}-{end_time}'

async def choose_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    club = context.user_data.get('club')
    user_date = context.user_data.get('date')
    hour = context.user_data.get('hour')
    minute = context.user_data.get('minute')
    duration = context.user_data.get('duration')
    level = query.data
    context.user_data['level'] = query.data
    confmsg = f"Club: {club} \nDate: {get_horaire(user_date, hour, minute, duration)}\nLevel: {level}\nConfirm ?"
    await query.edit_message_text(confmsg,
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirm", callback_data="confirm")],
                                                                       [InlineKeyboardButton("Cancel", callback_data="cancel")]]))
    return CONFIRMATION


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Finaliser et confirmer les réponses, puis poster dans un topic spécifique."""
    query = update.callback_query
    await query.answer()

    user_name = query.from_user.full_name  # Récupération du prénom pour le message de confirmation

    if query.data == "confirm":  
        club = context.user_data.get('club')
        user_date = context.user_data.get('date')
        hour = context.user_data['hour']
        minute = context.user_data['minute']
        duration = context.user_data['duration']
        level = context.user_data['level']   
        matchid  = str(datetime.datetime.now().timestamp())

        CACHE_MATCH_MSG[matchid] = {
            'players' : [user_name], 
            'club' : context.user_data.get('club'), 
            'date': context.user_data.get('date'), 
            'owner': user_name, 
            'hour':  context.user_data.get('hour'), 
            'minute':  context.user_data.get('minute'), 
            'duration':  context.user_data.get('duration'), 
            'level':  context.user_data.get('level')
        }

        await query.edit_message_text(f"Slot automatically created on group :\n{format_slot(matchid)}")
        print(f'User {user_name} confirm slot:\n{format_slot(matchid)}')

        response_message = await context.bot.send_message(
            chat_id=GROUP_ID,
            text=format_slot(matchid),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("(Un)Register", callback_data=f"participate_{matchid}")],
                [InlineKeyboardButton("Delete (owner)", callback_data=f"cancel_{matchid}")],
                [InlineKeyboardButton("(Un)Full (owner)", callback_data=f"full_{matchid}")]
                ]),
            message_thread_id=THREAD_ID
        )
        
        print(f'Message sent to group, matchid : {matchid} / msgid: {response_message.message_id}')
        CACHE_MATCH_MSG[matchid]['msgid'] = response_message.message_id
        commit_cache()
        return ConversationHandler.END
    else:
        return await start(update, context)  # restart

def format_slot(matchid):
    players = CACHE_MATCH_MSG[matchid]['players']
    players_tmp = players.copy()
    while len(players_tmp) < 4:
        players_tmp.append('')
    club = CACHE_MATCH_MSG[matchid]['club']
    date = CACHE_MATCH_MSG[matchid]['date']
    level = CACHE_MATCH_MSG[matchid]['level']
    hour = CACHE_MATCH_MSG[matchid]['hour']
    minute = CACHE_MATCH_MSG[matchid]['minute']
    duration = CACHE_MATCH_MSG[matchid]['duration']
    start_time = datetime.datetime.strptime(
        f"{date} {hour}:{minute}", '%d-%m-%Y %H:%M'
    )
    end_time = start_time + datetime.timedelta(minutes=int(duration))
    start_time = start_time.strftime('%H:%M')
    end_time = end_time.strftime('%H:%M')

    msg =  f'{club} - {date} {start_time}-{end_time} - Level {level} :\n'+''.join(f'- {player}\n' for player in players_tmp)

    del(players_tmp)
    return msg

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_name = query.from_user.full_name 
    matchid = query.data.split('_')[1]
    if matchid not in CACHE_MATCH_MSG:
        print(f'unable to find matchid {matchid} in cache, return')
        return
    owner = CACHE_MATCH_MSG[matchid]['owner']
    msgid = CACHE_MATCH_MSG[matchid]['msgid']
    print(f'Player {user_name} request to delete matchid {matchid}')
    if owner != user_name:
        print(f'Cannot delete matchid {matchid}, Player {user_name} is not the current owner {owner}')
        return
    
    await context.bot.delete_message(chat_id=GROUP_ID, message_id=msgid)
    del(CACHE_MATCH_MSG[matchid])
    commit_cache()
    print(f'Player {user_name} delete matchid {matchid}')
    return

async def full(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_name = query.from_user.full_name 
    matchid = query.data.split('_')[1]
    if matchid not in CACHE_MATCH_MSG:
        print(f'unable to find matchid {matchid} in cache, return')
        return
    owner = CACHE_MATCH_MSG[matchid]['owner']
    msgid = CACHE_MATCH_MSG[matchid]['msgid']
    players = CACHE_MATCH_MSG[matchid]['players']
    print(f'Player {user_name} request to fulfill matchid {matchid}')
    if owner != user_name:
        print(f'Cannot fulfill matchid {matchid}, Player {user_name} is not the current owner {owner}')
        return
    if len(players) == 4:
        print(f'Matchid {matchid} already full, removing Unknow player from members')
        players = [i for i in players if i != 'Unknown player']
        CACHE_MATCH_MSG[matchid]['players'] = players
    else:
        while len(players) < 4:
            players.append('Unknown player')
    commit_cache()
    await context.bot.edit_message_text(
        chat_id=GROUP_ID,
        message_id=msgid,
        text=format_slot(matchid),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("(Un)Register", callback_data=f"participate_{matchid}")],
            [InlineKeyboardButton("Delete (owner)", callback_data=f"cancel_{matchid}")],
            [InlineKeyboardButton("(Un)Full (owner)", callback_data=f"full_{matchid}")]
        ])
    )

    

async def participate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ajouter l'utilisateur au message de participation."""
    query = update.callback_query
    await query.answer()
    user_name = query.from_user.full_name 
    matchid = query.data.split('_')[1]
    print(f'Player {user_name} request to join matchid {matchid}')
    if matchid not in CACHE_MATCH_MSG:
        print(f'unable to find matchid {matchid} in cache, return')
        return
    msgid = CACHE_MATCH_MSG[matchid]['msgid']
    players = CACHE_MATCH_MSG[matchid]['players']
    owner = CACHE_MATCH_MSG[matchid]['owner']
    if user_name in players:
        if owner == user_name and len(players) == 1:
            print(f'Player {user_name} try to unjoin from matchid {matchid} but he is alone, skipping')
            return
        else:
            print(f'Player {user_name} already joined matchid {matchid}, removing player')
            CACHE_MATCH_MSG[matchid]['players'].remove(user_name)
    else:
        if len(players) == 4:
            print(f'Matchid {matchid} already have 4 players, disacarding registration')
            return
        print(f'Player {user_name} added to matchid {matchid}')
        CACHE_MATCH_MSG[matchid]['players'].append(user_name)
    commit_cache()

    btn = [
        [InlineKeyboardButton("(Un)Register", callback_data=f"participate_{matchid}")],
        [InlineKeyboardButton("Delete (owner)", callback_data=f"cancel_{matchid}")],
        [InlineKeyboardButton("(Un)Full (owner)", callback_data=f"full_{matchid}")]
    ]

    print(f'Sending update message {msgid}')
    await context.bot.edit_message_text(
        chat_id=GROUP_ID,
        message_id=msgid,
        text=format_slot(matchid),
        reply_markup=InlineKeyboardMarkup(btn)
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Réinitialiser le contexte si l'utilisateur tape 'stop'."""
    user_name = update.message.from_user.full_name  # Récupération du prénom de l'utilisateur
    await update.message.reply_text(f"Commande stop reçue, {user_name}. Recommençons depuis le début.")
    return await start(update, context)  # Recommencer depuis le début

def main():
    """Lancer le bot."""
    global CACHE_MATCH_MSG

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "rb") as infile:
                CACHE_MATCH_MSG = pickle.load(infile)
                print(f'CACHE_MATCH_MSG loaded from {CACHE_FILE} : {CACHE_MATCH_MSG}')
        except Exception as e:
            CACHE_MATCH_MSG = {}
            print(f"Unable to load cache: {e}")
    else:
        CACHE_MATCH_MSG = {}

    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_CLUB: [CallbackQueryHandler(choose_club)],
            CHOOSING_DATE: [CallbackQueryHandler(choose_date)],
            CHOOSING_HOUR: [CallbackQueryHandler(choose_hour)],
            CHOOSING_MINUTE: [CallbackQueryHandler(choose_minute)],
            CHOOSING_DURATION: [CallbackQueryHandler(choose_duration)],
            CHOOSING_LEVEL: [CallbackQueryHandler(choose_level)],
            CONFIRMATION: [CallbackQueryHandler(confirm)],
        },
        fallbacks=[MessageHandler(filters.Regex("^stop$"), stop)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(participate, pattern="participate"))
    application.add_handler(CallbackQueryHandler(cancel, pattern="cancel"))
    application.add_handler(CallbackQueryHandler(full, pattern="full"))
    try:
        application.run_polling()
    except Exception as e:
        print(f"Erreur lors de l'exécution du bot : {e}")

if __name__ == '__main__':
    main()
