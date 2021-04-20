from django.shortcuts import render
from django.http import HttpResponse
import telebot
from telebot import TeleBot, types
import json
import time
import random
import sqlite3
from django.views.decorators.csrf import csrf_exempt
from bot.classes.user import *
from bot.classes.stairs import *
from bot.classes.pay import *
from bot.classes.message import MessageClass
import django.db
from telebot import apihelper

from bot.keyboards import task as task_keyboard
from bot.keyboards import tags as tags_keyboard


# # Logger
# logger = telebot.logger
# telebot.logger.setLevel(logging.DEBUG)

# Set proxy
# apihelper.proxy = {'http': '162.159.242.248:80'}


@csrf_exempt
def webhook(request):
	if request.method == 'POST':
		json_str = request.body.decode('UTF-8')
		update = types.Update.de_json(json_str)
		process_new_updates([update])
		return HttpResponse(status=200)
	return HttpResponse(status=403)


@csrf_exempt
def pay(request):
	if request.method == 'POST':
		pay = Pay()
		pay.pay(request.POST)
		if(pay.state):
			send_message(chat_id=pay.client.chat_id, text=pay.answer, parse_mode='HTML')
		return HttpResponse(status=200)
	return HttpResponse(status=403)

@astudy.message_handler(content_types=['text'])
def main(message):
	if(message.chat.type != 'private'):
		return
		
	chat = {'chat_id': message.chat.id, 'login': message.chat.username,
			'str_name': '{} {}'.format(message.chat.first_name, message.chat.last_name)}

	user.get_steper()

	exit_commands = list(set(tags_keyboard.exit_commands + task_keyboard.exit_commands))
	if user.step and user.step.callback_data in task_keyboard.dict_callback and message.lower() in task_keyboard.dict_callback[user.step.callback_data]:
		step = task_keyboard.dict_callback[user.step.callback_data][message.lower()]
	elif user.step and user.step.callback_data in tags_keyboard.dict_callback and message.lower() in tags_keyboard.dict_callback[user.step.callback_data]:
		step = tags_keyboard.dict_callback[user.step.callback_data][message.lower()]
	else:
		step = None

	if(not message in exit_commands and step):
		stairs.callback_response(
			{
				'step': step, 
				'message_id': user.step.message_id,
				'new_message': True
			}, 
			'inside'
		)

	elif(user.dialog):
		stairs.pending_response(message)
	else:
		stairs.quick_response(message.lower())


	if(stairs.delete_dialog):
		user.delete_dialog()

	if(stairs.data_dialog):
		user.create_dialog(stairs.data_dialog, bot_name,
						   stairs.data_controller)

	django.db.close_old_connections()


@astudy.callback_query_handler(func=lambda call: True)
def text(call):
	chat = {'chat_id': call.message.chat.id, 'login': call.message.chat.username,
			'str_name': '{} {}'.format(call.message.chat.first_name, call.message.chat.last_name)}
	user = UserClass(chat, bot_name)
	user.check_chat_member(astudy)
	if(not user.state):
		astudy.send_message(
			chat_id=chat['chat_id'], text=user.text, parse_mode='HTML'
		)
		return

	stairs = Stairs(user, astudy, bot_name)
	stairs.callback_response(call)

	if(stairs.delete_dialog):
		user.delete_dialog()

	if(stairs.data_dialog):
		user.create_dialog(stairs.data_dialog, bot_name,
						   stairs.data_controller)

	django.db.close_old_connections()


@astudy.message_handler(content_types=['document', 'photo'])
def handle_docs_photo(message):
	chat = {'chat_id': message.chat.id, 'login': message.chat.username,
			'str_name': '{} {}'.format(message.chat.first_name, message.chat.last_name)}
	user = UserClass(chat, bot_name)
	user.check_chat_member(astudy)
		
	stairs = Stairs(user, astudy, bot_name)
	stairs.file_response(message, message.content_type)

	if(stairs.delete_dialog):
		user.delete_dialog()

	if(stairs.data_dialog):
		user.create_dialog(stairs.data_dialog, bot_name)

	django.db.close_old_connections()
