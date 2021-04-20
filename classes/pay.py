# -*- coding: utf-8 -*-
import datetime
import base64
import json
from django.conf import settings
from bot.models import *
from django.utils import timezone
from liqpay.liqpay import LiqPay
from bot.texts.functions import font

class Pay:

	def __init__(self):
		if settings.DEBUG:
			key_1, key_2 = '', ''
		else:
			key_1, key_2 = '', ''

		self.sign_str = ''.format(key_1, key_2)

		self.liqpay = LiqPay(key_1, key_2)
		self.data = ''

	def font(self, type_font, message):
		font_array = {'bold': '<b>' + str(message) + '</b>', 'light': '<i>' + str(message) + '</i>'}
		return font_array[type_font]

	def create_pay(self, amount, order_id, type_tr):
		res = self.liqpay.api("request", {
			"action"    : "invoice_bot",
			"version"   : "3",
			"amount"    : amount,
			"currency"  : "UAH",
			"order_id"  : '_'.join([order_id, type_tr]),
			"phone"  	: "",
			"server_url": '{}/liqpay'.format(settings.URL_HOST)
		})
		
		self.data = res['token']

	def pay(self, json_data):
		data = base64.b64decode(json_data['data']).decode('utf-8')
		sign = self.liqpay.str_to_sign(self.sign_str.format(json_data['data']))
		json_string = json.loads(data)

		print(json_data['signature'])
		print(sign)
		self.state = False
		if(json_data['signature'] == sign and json_string['status'] == 'success'):
			order = json_string['order_id'].split('_')
			pay_liq_id = order[0]
			type_tr = order[1]

			transactions = Payliq.objects.filter(id=pay_liq_id).first()
			if(not transactions.state):
				transactions.state = True
				transactions.json = str(json_string)
				transactions.save(update_fields=['state', 'json'])

				self.client = Clients.objects.filter(id=transactions.client.id).first()
				self.client.balance += transactions.amount_one
				self.client.save(update_fields=['balance'])

				Transactions_log.objects.create(client=self.client, amount=transactions.amount_one, type_transactions='payliq')
				
				if type_tr == 'balance':
					pass
					
				elif type_tr == 'task':
					pass

				self.state = True