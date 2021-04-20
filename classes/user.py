# -*- coding: utf-8 -*-
import datetime
import math
from bot.models import *
from django.utils import timezone
from liqpay.liqpay import LiqPay
from bot.classes.pay import *
from django.db.models import Count, F, Sum, Avg, Q, Value, Case, When
from django.db.models.functions import Coalesce
import uuid
from telebot import types

from bot.texts.ru import REFERAL_TEXT, SHARED
from bot.keyboards.functions import constructor

import base64
import string
import random

class UserClass:

	def __init__(self, chat, bot=None, code=None):
		self.client = Clients.objects.filter(chat_id=chat['chat_id'])
		if(bot is not None):
			if(self.client):
				self.client = self.client[0]
				dialog = DialogControll.objects.filter(client=self.client, bot=bot)
				if(dialog):
					self.dialog = dialog[0]
				else:
					self.dialog = None

				if(not self.client.login):
					self.client.login = chat['login']

				if(not self.client.str_name):
					self.client.str_name = chat['str_name']

				if(not self.client.refer_code):
					self.client.refer_code = ''.join(random.sample((string.ascii_uppercase+string.digits),6))

				self.client.save(update_fields=['login', 'str_name', 'refer_code'])
			else:
				tracking = Tracking.objects.filter(code=code)
				if(tracking):
					self.client = Clients.objects.create(chat_id=chat['chat_id'], refer_code=uuid.uuid4(), login=chat['login'], str_name=chat['str_name'], tracking=tracking[0])
				else:
					self.client = Clients.objects.create(chat_id=chat['chat_id'], refer_code=uuid.uuid4(), login=chat['login'], str_name=chat['str_name'])
				self.dialog = None

		self.commissions = Commissions.objects.filter().first()
	
	def create_dialog(self, data, bot, controller=None, counter=0):
		self.dialog = DialogControll.objects.create(client=self.client, data=data, bot=bot, controller=controller, counter=counter)

	def delete_dialog(self):
		if(self.dialog):
			self.dialog.delete()
			self.dialog = None

	def balance_replenishment(self, message):
		amount = math.ceil(float(message))
		
		self.order = Payliq.objects.create(client=self.client, amount_one=amount, amount_two=amount / self.commissions.amount_one)
		pay = Pay()
		pay.create_pay(
			amount=amount / self.commissions.amount_one,
			order_id=str(self.order.id),
			type_tr='balance'
		)
		self.order.token = pay.data
		self.order.save(update_fields=['token'])

	def give_pay(self, message):
		self.sum_waited = math.floor(float(message) * self.commissions.amount_two)
		self.client.balance -= float(message)
		self.client.save(update_fields=['balance'])
		self.order = Withdrawal.objects.create(client=self.client, amount_one=float(message), amount_two=self.sum_waited)

	def withdrawal_list(self):
		self.withdrawal_sum = Withdrawal.objects.filter(client=self.client, state=False).aggregate(Sum('amount_two'))

	def role_task(self):
		cabinet = Cabinet.objects.filter(client=self.client, active=True, state=True)
		if(cabinet):
			self.cabinet = cabinet[0]
			self.role = self.cabinet.role
			translate = TRANSLATE_ROLE[self.role]
			self.role_interlocutor = translate[1]
			self.name_interlocutor = translate[0]
			self.name_rolemessage = translate[2]
		else:
			cabinet = Cabinet.objects.filter(client=self.client, active=True).first()
			if(cabinet):
				self.role = cabinet.role
			else:
				self.role = None

	def shared(self):
		code = self.client.refer_code
		self.answer = REFERAL_TEXT
		
		buttons = []
		buttons.append({
			'text': '', 
			'url': 'https://vk.com/share.php?url={}'.format(
				SHARED['url'].format(code),
			)
		})
		buttons.append({
			'text': '', 
			'url': 'https://t.me/share/url?url={}'.format(
				SHARED['url'].format(code),
			)
		})
		buttons.append({
			'text': '',
			'url': 'https://www.facebook.com/sharer.php?&u={}'.format(
				SHARED['url'].format(code),
			)
		})
		buttons.append({
			'text': '',
			'url': 'http://twitter.com/share?url={}'.format(
				SHARED['url'].format(code),
			)
		})
		buttons.append({
			'text': '',
			'callback_data': 'BALANCE121'
		})

		self.keyboard = types.InlineKeyboardMarkup(True)
		self.keyboard.keyboard = constructor(buttons, 2)

	def referal(self, code):
		refer = Clients.objects.filter(refer_code__iexact=code.lower()).first()
		if(refer):
			if(not self.client.refer_code and self.client.id != refer.id):
				self.client.refer = refer
				self.client.bonuse = True
				self.client.save(update_fields=['refer', 'bonuse'])
				self.answer = ''.format(math.ceil((1 - self.commissions.amount_four) * 100))
			else:
				self.answer = ''
		else:
			self.answer = ''

	def referal_statistics(self):
		referals = Clients.objects.filter(refer=self.client).values('id')
		task = Tasks.objects.filter(client__in=referals).aggregate(
			all=Count('id'),
			finish=Count('id', filter=Q(finish=True)),
		)
		money = Transactions_log.objects.filter(client=self.client, type_transactions='referalka').aggregate(
			rise=Coalesce(
				Sum('amount'), Value(0)
			)
		)
		self.answer = ''.format(
							len(referals),
							task['all'],
							task['finish'],
							round(money['rise'], 2)
						)
		
		self.keyboard = types.InlineKeyboardMarkup(True)
		self.keyboard.keyboard.append([{'text': 'Назад', 'callback_data': 'BALANCE122'}])

	def get_steper(self):
		self.step = Stepers.objects.filter(client=self.client).first()
	
	def set_steper(self, step_task, message_id):
		self.step = Stepers.objects.filter(client=self.client).first()
		if(self.step):
			self.step.callback_data = step_task
			self.step.message_id = message_id
			self.step.save(update_fields=['callback_data', 'message_id'])
		else:
			self.step = Stepers.objects.create(
				client=self.client,
				callback_data=step_task,
				message_id=message_id
			)

	def del_steper(self):
		Stepers.objects.filter(client=self.client).delete()


	def add_tags(self, type_tag, message):
		message_set = set(message.split())
		tags_set = set(self.client.add_tags.split() if type_tag == 'add' else self.client.remove_tags.split())
		
		difference_tags = message_set.difference(tags_set)
		if difference_tags:
			tags_set = tags_set.union(difference_tags)
			tags_str = str(' '.join(tags_set))

			if type_tag == 'add':
				self.client.add_tags = tags_str
				update_fields = ['add_tags']
			else:
				self.client.remove_tags = tags_str
				update_fields = ['remove_tags']

			self.client.save(update_fields=update_fields)
			return True
		else:
			self.answer = ''
			return False

	def delete_tags(self, message):
		add_tags = set(self.client.add_tags.split())
		remove_tags = set(self.client.remove_tags.split())
		message = set(message.split())

		add_tags = add_tags.difference(message)
		remove_tags = remove_tags.difference(message)

		self.client.add_tags = str(' '.join(add_tags))
		self.client.remove_tags = str(' '.join(remove_tags))
		self.client.save(update_fields=['add_tags', 'remove_tags'])

	def clear_tags(self):
		self.client.add_tags = ''
		self.client.remove_tags  = ''
		self.client.save(update_fields=['add_tags', 'remove_tags'])



