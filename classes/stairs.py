# -*- coding: utf-8 -*-
from bot.models import *
from bot.classes.subject import SubjectClass
from bot.classes.task import TaskClass
from bot.classes.message import MessageClass
from bot.classes.user import create_message_roles
from django.utils import timezone
from telebot import types
from datetime import datetime, date, timedelta
from django.core.files import File
from django.core.files.base import ContentFile
import os
import math
import time
import re

from bot.texts.functions import font
from bot.texts.ru import REFERAL_TEXT, SUPPORT_TEXT, INFO_TEXT, START_TEXT, SHARED
from bot.texts.ru import between_text, len_string_text, isint_text, dont_understend
from bot.texts.ru import ready_post

class Stairs:

	def __init__(self, user, bot, bot_name):
		self.COUNT_ROW = 2
		self.user = user
		if(user is None):
			self.client = None
			self.dialog = None
		else:
			self.client = self.user.client
			self.dialog = self.user.dialog
		self.telegram_bot = bot
		self.bot_name = bot_name
		self.delete_dialog = False
		self.data_dialog = ''
		self.answer = ''

		self.buttons_start = [
		]


		self.keyboard_cancel = types.InlineKeyboardMarkup(True)
		self.keyboard_cancel.keyboard = constructor([{'text': 'Отмена', 'callback_data': 'USER888'}], 1)

	def isint(self, s, step):
		try:
			int(s)
			return True
		except ValueError:
			if step in isint_text:
				self.answer = isint_text[step]
			else:
				self.answer = 'Введите число'
			return False

	def isfloat(self, s, step):
		try:
			float(s)
			return True
		except ValueError:
			if step in isint_text:
				self.answer = isint_text[step]
			else:
				self.answer = 'Введите число'
			return False

	def between(self, message, a, b, step):
		if not (a <= float(message) <= b):
			if step in between_text:
				self.answer = between_text[step].format(a, b)
			else:
				self.answer = 'Введите число от {} до {}'.format(a, b)
			return False
		return True

	def len_string(self, message, a, step):
		if (len(message) > a):
			if step in len_string_text:
				self.answer = len_string_text[step].format(a)
			else:
				self.answer = 'Ограничение {} символов'.format(a)
			return False
		return True

	def format_str(self, tpl, message, example, step):
		if re.match(tpl, message) is not None:
			return True
		else:
			if step in dont_understend:
				self.answer = dont_understend[step]
			else:
				self.answer = 'Введите в данном виде {}'.format(example)
			return False

	def quick_response(self, message, data=None):
		print(120, self.bot_name, message)
		if(self.bot_name == ''):
			pass

	def callback_response(self, data, call='outside'):
		if(call == 'inside'):
			step = data['step']
			message_id = data['message_id']
			new_message = data['new_message']
			self.controller = False
		elif(call == 'outside'):
			step = data.data
			message_id = data.message.message_id
			query_id = data.id
			# self.telegram_bot.answer_callback_query(callback_query_id=query_id, text=step)

			new_message = False
			self.controller = False
		elif(call == 'controller'):
			step = data['step']
			message_id = data['message_id']
			new_message = False
			self.controller = True
			
		self.data_controller = step
		
		print(199,step.split('_'))

		
		# if(self.telegram_bot.get_me().username == 'autotextbackbot'):
		if('USER' in step):
			self.delete_dialog = True
			if(step == 'USER777'):
				self.quick_response('', data)
				return

			elif(step == 'USER888'):
				self.answer = ''
				keyboard = types.ReplyKeyboardMarkup(True)
				if(self.bot_name == ''):
					keyboard.keyboard = self.buttons_start
					self.user.del_steper()
				else:
					self.user.role_task()
					if(self.user.role == ''): 
						pass
					elif(self.user.role == ''): 
						pass
					elif(self.user.role == ''): 
						pass

				self.telegram_bot.delete_message(chat_id=self.client.chat_id, message_id=message_id)
				self.telegram_bot.send_message(chat_id=self.client.chat_id, parse_mode="HTML", text=self.answer, reply_markup=keyboard)
				return 

			elif(step == 'USER100'):
				self.answer = ''

			elif(step == 'USER101'):
				self.answer = ''

			elif(step == 'USER102'):
				self.answer = ''
			
			elif(step == 'USER103'):
				self.answer = ''
				
			if(self.controller):
				try: self.telegram_bot.delete_message(chat_id=self.client.chat_id, message_id=message_id)
				except Exception as e: print('000 Error ' + str(e))
				mes = self.telegram_bot.send_message(chat_id=self.client.chat_id, parse_mode="HTML", text=self.answer, reply_markup=self.keyboard_cancel)
				self.data_dialog = step + '|' + str(mes.message_id)	
			else:
				mes = self.telegram_bot.send_message(chat_id=self.client.chat_id, parse_mode="HTML", text=self.answer, reply_markup=self.keyboard_cancel)
				self.data_dialog = step + '|' + str(mes.message_id)	

		elif 'TAGS' in step:
			method = step.split('_')[0]
			self.delete_dialog = True
			if method == 'TAGS100':
				self.user.del_steper()
				self.quick_response('')
				return

			elif method == 'TAGS101':
				self.answer = ''
			elif method == 'TAGS102':
				self.answer = ''
			elif method == 'TAGS103':
				self.answer = ''
			elif method == 'TAGS104':
				self.answer = ''
			elif method == 'TAGS105':
				self.user.clear_tags()
				self.quick_response('')
				return

			message_id = del_send_message(
				telegram_bot=self.telegram_bot, 
				chat_id=self.client.chat_id, 
				text=self.answer,
				user=self.user,
				step_task=method,
			)

			if method != 'TAGS101':
				data_db = [method, str(message_id)]
				self.data_dialog = '|'.join(data_db)
				self.data_controller = '|'.join(data_db)

	def pending_response(self, message):
		if('CUSTOMERSEARCH130' in self.dialog.data or 'CUSTOMER150' in self.dialog.data):
			self.answer = ''
			self.telegram_bot.send_message(chat_id=self.client.chat_id, text=self.answer, parse_mode='HTML')


		elif('USER' in self.dialog.data):
			step = self.dialog.data.split('|')[0]
			message_id = self.dialog.data.split('|')[1]
			if(step == 'USER100'):
				self.client.name = message
				update_fields = ['name']

			elif(step == 'USER101'):
				self.client.city = message
				update_fields = ['city']

			elif(step == 'USER102'):
				self.client.more = message
				update_fields = ['more']

			elif(step == 'USER103'):
				self.client.withdraw = message
				update_fields = ['withdraw']

			self.client.save(update_fields=update_fields)

			self.user.card_raiting()

		elif 'TAGS' in self.dialog.data:
			step = self.dialog.data.split('|')[0]
			message_id = self.dialog.data.split('|')[1]
			if(not self.len_string(message, 50, step)):
				self.telegram_bot.send_message(chat_id=self.client.chat_id, text=self.answer, parse_mode='HTML')
				return

			if(step == 'TAGS102'):
				self.user.delete_tags(message)
			elif(step == 'TAGS103'):
				self.user.add_tags('add', message)
			elif(step == 'TAGS104'):
				self.user.add_tags('remove', message)

			self.quick_response('предметы')

	def file_response(self, data, type_file):
		if(self.dialog and self.bot_name == ''):
			if(self.dialog and self.dialog.data):
				print(1846, type_file)
				if(type_file == 'photo'):
					file_id = data.photo[-1].file_id
					file_info = self.telegram_bot.get_file(file_id)
					file_name = file_info.file_path.split('/')[1]
				else:
					file_id = data.document.file_id
					file_info = self.telegram_bot.get_file(file_id)
					file_name = data.document.file_name

				print(self.dialog.data)
				message_id = self.dialog.data.split('|')[1]
				downloaded_file = self.telegram_bot.download_file(file_info.file_path)
				if('CUSTOMERSEARCH130' in self.dialog.data):
					id_task = self.dialog.data.split('|')[2]
					task = TaskClass(self.client, 'CUSTOMERSEARCH', id_task)
					if(not task.task):
						try: self.telegram_bot.delete_message(message_id=message_id)
						except: pass
						self.telegram_bot.send_message(
							chat_id=self.client.chat_id, 
							text=task.answer
						)
						self.delete_dialog = True
						return

					if('first' in self.dialog.data):
						task.task.files.clear()
						task.task.save()

					task.update_task(action='files', message=downloaded_file, file_name=file_name)
					self.telegram_bot.send_message(chat_id=self.client.chat_id, parse_mode="HTML", text=task.answer, reply_markup=task.keyboard)

				elif('CUSTOMER150' in self.dialog.data):
					task = TaskClass(self.client, 'CUSTOMERCREATE')
					if not task.update_task(action='files', message=downloaded_file, file_name=file_name, type_file=type_file, file_id=file_id):
						self.telegram_bot.send_message(chat_id=self.client.chat_id, parse_mode="HTML", text=task.answer)
						return

					task.text_task('files')

					self.callback_response(
						{
							'step': '{}_more__'.format(task.now_step), 
							'message_id': 0,
							'new_message': True
						}, 
						'inside'
					)
