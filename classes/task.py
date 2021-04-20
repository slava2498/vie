# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
import calendar
import os
import math
import locale

from bot.models import *
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils import timezone
from django.core.paginator import Paginator
from telebot import types
from io import BytesIO
from telebot.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument
from django.db.models import Avg
from bot.classes.user import UserClass, create_message_roles
from bot.classes.pay import Pay

from bot.texts.functions import font
from bot.texts.ru import PAY_SUCCESS
from bot.keyboards.functions import constructor

class TaskClass:
	keyboard = ''
	answer = ''
	client = ''
	count_list = 9
	COUNT_ROW = 2
	lenght_preview = 20
	state = True
	task = ''
	docs = []

	def __init__(self, client, user='', id_task=None):
		self.client = client
		self.user = user
		self.commissions = Commissions.objects.filter().first()

	def payment_feedback(self, id_feedback):
		feedback = Feedback.objects.filter(id=id_feedback).first()
		if(self.client.bonuse): 
			price = feedback.price_two
		else: 
			price = feedback.price_two / self.commissions.amount_four

		self.client.bonuse = False
		self.client.save(update_fields=['bonuse'])
		if(self.client.bonuse):
			self.answer = '💲 Цена с учетом комиссии сервиса: {} (Без скидки {})'.format(font('bold', str(math.ceil(price)) + ' грн'), font('bold', str(math.ceil(feedback.price_two / self.commissions.amount_four)  + ' грн')))
		else:
			self.answer = '💲 Цена с учетом комиссии сервиса: {}'.format(font('bold', str(math.ceil(price)) + ' грн'))
		self.keyboard = types.InlineKeyboardMarkup(True)

		self.keyboard.keyboard.append([{'text': 'Оплатить ✔️', 'callback_data': 'CUSTOMER180_' + str(feedback.id) + '____'}])

	def task_payment(self, id_feedback):
		feedback = Feedback.objects.filter(id=id_feedback).first()
		self.keyboard = types.InlineKeyboardMarkup(True)

		amount = feedback.price_two / self.commissions.amount_four
		if self.client.balance >= amount:
			return self.accept_feedback(feedback.id)
		else:
			amount_one = math.ceil(amount - self.client.balance)
			amount_two = math.ceil(amount_one / self.commissions.amount_three / self.commissions.amount_one)
			self.order = Payliq.objects.create(
				client=self.client, 
				amount_one=amount_one, 
				amount_two=amount_two,
				feedback=feedback
			)
			
			pay = Pay()
			pay.create_pay(
				amount=amount_two, 
				order_id=str(self.order.id), 
				type_tr='task'
			)

			self.order.token = pay.data
			self.order.save(update_fields=['token'])
			
			self.client.balance = 0
			self.client.save(update_fields=['balance'])
			return True

	def accept_feedback(self, id_feedback):
		feedback = Feedback.objects.filter(id=id_feedback).select_related('task', 'client').first()
		if(self.client.bonuse): 
			price = feedback.price_two
		else: 
			price = feedback.price_two / self.commissions.amount_four

		feedback.state = True
		feedback.state_money = True
		feedback.save(update_fields=['state', 'state_money'])
		self.task = feedback.task
		if(self.task.executor):
			return False

		self.task.executor = feedback.client
		self.task.price_one = feedback.price_two
		self.task.price_two = price
		self.task.state = True

		self.task.save(update_fields=['executor', 'price_one', 'price_two', 'state'])
		self.client.balance -= price
		self.client.save(update_fields=['balance'])

		Transactions_log.objects.create(client=self.client, 
										amount=price, 
										type_transactions='paytask',
										task=self.task,
										balance=self.client.balance,
										zero=price,
										)

		self.answer = PAY_SUCCESS.format(font('bold', '#{} {}'.format(feedback.task.id, feedback.task.subject)))
		return True

		
