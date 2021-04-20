import json

from celery import Celery, shared_task
from datetime import timedelta, date, datetime
from django.utils import timezone

from telebot import TeleBot, types
from telebot.types import InputMediaPhoto, InputMediaVideo

import app
import settings
from bot.classes.task import TaskClass

@app.task
def sending():
	from bot.models import Sending

	send_dict = Sending.objects.filter().select_related('obj_task')

	counter = 0
	wall = 3

	for x in send_dict:
		clients_dict = json.loads(x.clients)
		buttons = json.loads(x.buttons)
		keyboard = types.InlineKeyboardMarkup(True)
		keyboard.keyboard = buttons

		if(counter > wall):
			break

		if(x.type_action == 'send_user'):
			for key in clients_dict.copy():
				print(36, key)
				try:
					telegram_bot.send_message(
						chat_id=clients_dict[key], 
						text=x.text, 
						parse_mode=x.parse_mode,
						reply_markup=keyboard
					)

				except Exception as e:
					print(59, e)

				clients_dict.pop(str(key))
				counter += 1

				if(counter > wall):
					break

		elif(x.type_action == 'send_task_group'):
			for key in clients_dict.copy():
				try:
					message_id = send_message(
						chat_id=clients_dict[key],
						text=x.text, 
						parse_mode=x.parse_mode,
						reply_markup=keyboard,
						disable_web_page_preview=None
					).message_id

					x.obj_task.message_id = message_id
					x.obj_task.save(update_fields=['message_id'])

				except Exception as e:
					print(59, e)

				clients_dict.pop(str(key))
				counter += 1

				if(counter > wall):
					break

		elif(x.type_action == 'edit_task_group'):
			for key in clients_dict.copy():
				try:
					edit_message_text(
						chat_id=clients_dict[key]['chat_id'],
						message_id=clients_dict[key]['message_id'],
						text=x.text, 
						parse_mode=x.parse_mode,
						reply_markup=keyboard,
						disable_web_page_preview=False
					)

				except Exception as e:
					print(59, e)

				clients_dict.pop(str(key))
				counter += 1

				if(counter > wall):
					break

		elif(x.type_action == 'edit'):
			for key in clients_dict.copy():
				try:
					edit_message_text(
						chat_id=clients_dict[key]['chat_id'],
						message_id=clients_dict[key]['message_id'],
						text=x.text, 
						parse_mode=x.parse_mode,
						reply_markup=keyboard,
					)
				except Exception as e:
					print(90, e)

				clients_dict.pop(str(key))
				counter += 1

				if(counter > wall):
					break

		print(clients_dict)

		if(clients_dict):
			x.clients = json.dumps(clients_dict)
			x.save(update_fields=['clients'])
		else:
			x.delete()

@app.task
def ticker():
	task = TaskClass(None, None)
	task.garant_deadline()
	task.task_delete()