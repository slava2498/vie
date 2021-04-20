from django.shortcuts import render
from django.http import HttpResponse
import telebot
from settings import ASTUDY_TOKEN, CABINET_TOKEN, REQUEST_TOKEN
from telebot import TeleBot, types
import json
import time
import random
import math
import sqlite3
from django.views.decorators.csrf import csrf_exempt
import django.db
from bot.models import *
from datetime import datetime, date, timedelta
from bot.classes.user import *
from bot.classes.stairs import *
from rest_framework import serializers
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, F, Sum, Avg, Q, Value, Case, When
from django.db.models.functions import Coalesce

from django.core.serializers.json import DjangoJSONEncoder

class TransactionsSerializer(serializers.ModelSerializer):
	transaction = serializers.SerializerMethodField(method_name='get_type')
	chat_id = serializers.SerializerMethodField(method_name='get_chat_id')
	date = serializers.SerializerMethodField(method_name='get_date')

	login = serializers.SerializerMethodField(method_name='get_login')
	strname = serializers.SerializerMethodField(method_name='get_strname')

	class Meta:
		model = Transactions_log
		fields = '__all__'

	def get_type(self, instance):
		if(instance.task_id and instance.type_transactions == 'finish'):
			return ''.format(instance.task_id)
		elif(instance.task_id and instance.type_transactions == 'paytask'):
			return ''.format(instance.task_id)
		else:
			return TRANSLATE_PAYS[instance.type_transactions]

	def get_chat_id(self, instance):
		return instance.client.chat_id

	def get_date(self, instance):
		tz = timezone.pytz.timezone('Europe/Kiev')
		return str(instance.date_add.astimezone(tz))

	def get_login(self, instance):
		if(instance.client.login):
			return '@' + instance.client.login
		else:
			return '-'

	def get_strname(self, instance):
		return instance.client.str_name.replace('None', '')


class RisePeopleTaskSerializer(serializers.Serializer):
	count = serializers.IntegerField()
	date_add = serializers.CharField()

class TaskSerializer(serializers.Serializer):
	count = serializers.IntegerField()
	date_add = serializers.CharField()

class RiseSerializer(serializers.Serializer):
	rise = serializers.FloatField()
	date_add = serializers.CharField()

class CirculatingSerializer(serializers.Serializer):
	rise = serializers.FloatField()
	date_add = serializers.CharField()

@csrf_exempt
def _(request):
	customer_rise = Cabinet.objects.filter(role='customer').extra({'date_add':"date(date_add)"}).values('date_add').order_by('date_add').annotate(count=Count('id'))
	executor_rise = Cabinet.objects.filter(role='executor').extra({'date_add':"date(date_add)"}).values('date_add').order_by('date_add').annotate(count=Count('id'))

	serializer = RisePeopleTaskSerializer(data=executor_rise, many=True)
	serializer.is_valid()
	customer_data = serializer.data

	counter = 0
	for user in customer_data:
		user['count'] += counter
		counter = user['count']

	serializer = RisePeopleTaskSerializer(data=customer_rise, many=True)
	serializer.is_valid()
	executor_data = serializer.data

	counter = 0
	for user in executor_data:
		user['count'] += counter
		counter = user['count']

	task_all = Tasks.objects.filter().extra({'date_add':"date(date_add)"}).values('date_add').annotate(
		count=Count('id')
	)

	
	task_finish = Tasks.objects.filter(finish=True).extra({'date_add':"date(date_add)"}).values('date_add').order_by('date_add').annotate(count=Count('id'))
	task_work = Tasks.objects.filter(finish=False).exclude(executor=None).extra({'date_add':"date(date_add)"}).values('date_add').order_by('date_add').annotate(count=Count('id'))

	serializer = TaskSerializer(data=task_all, many=True)
	serializer.is_valid()
	task_all_data = serializer.data

	counter = 0
	for task in task_all_data:
		task['count'] += counter
		counter = task['count']

	serializer = TaskSerializer(data=task_finish, many=True)
	serializer.is_valid()
	task_finish_data = serializer.data


	serializer = TaskSerializer(data=task_work, many=True)
	serializer.is_valid()
	task_work_data = serializer.data



	rise = Transactions_log.objects.filter().extra({'date_add':"date(date_add)"}).values('date_add').order_by('date_add').annotate(
		rise=0.9725 * (
			Coalesce(Sum(
			'amount', filter=Q(type_transactions='paytask')
			), Value(0)) -
			Coalesce(Sum(
				'amount', filter=Q(type_transactions='finish')
			), Value(0))
			 -
			Coalesce(Sum(
				'amount', filter=Q(type_transactions='referalka')
			), Value(0))
		)
	)
	
	circulating = Transactions_log.objects.filter().extra({'date_add':"date(date_add)"}).values('date_add').order_by('date_add').annotate(
		rise=Coalesce(Sum('amount'), Value(0)),
	)

	serializer = RiseSerializer(data=rise, many=True)
	serializer.is_valid()
	rise_data = serializer.data

	counter = 0
	for rise in rise_data:
		rise['rise'] += counter
		counter = rise['rise']

	serializer = CirculatingSerializer(data=circulating, many=True)
	serializer.is_valid()
	circulating_data = serializer.data

	counter = 0
	for rise in circulating_data:
		rise['rise'] += counter
		counter = rise['rise']


	task = Tasks.objects.filter().aggregate(
		all=Count('id'),
		waited=Count('id', filter=Q(finish=False, state=True)),
		work=Count('id', filter=Q(finish=False), exclude=Q(executor=None)),
		garant=Count('id', filter=Q(finish=False, request=True)),
		finish=Count('id', filter=Q(finish=True)),
		problem=Count('id', filter=Q(problem=True)),
	)

	# balance = Feedback.objects.filter(state_money=True, state_user_accept=True, task__finish=True).aggregate(rise=Sum(F('task__price_two') - F('price_one')), avg_rise=Avg(('task__price_two')))
	balance = Transactions_log.objects.filter().aggregate(
		rise=Coalesce(Sum(
			'amount', filter=Q(type_transactions='paytask')
		), Value(0)) -
		Coalesce(Sum(
			'amount', filter=Q(type_transactions='paytask')
		), Value(0)) / 2.75 -
		Coalesce(Sum(
			'amount', filter=Q(type_transactions='withdrawal')
		), Value(0)),
		avg_rise=Avg('amount', filter=Q(type_transactions='paytask'))
	)
	
	coversion = task['finish'] / task['all']

	all_money = Transactions_log.objects.filter().aggregate(
		liqpay=Coalesce(Sum('amount', filter=Q(type_transactions='payliq')), Value(0)),
		paytask=Coalesce(Sum('amount', filter=Q(type_transactions='paytask')), Value(0)),
		finish=Coalesce(Sum('amount', filter=Q(type_transactions='finish')), Value(0)),
		refer=Coalesce(Sum('amount', filter=Q(type_transactions='referalka')), Value(0)),
		rise=0.9725 * (
			Coalesce(Sum(
			'amount', filter=Q(type_transactions='paytask')
			), Value(0)) -
			Coalesce(Sum(
				'amount', filter=Q(type_transactions='finish')
			), Value(0))
			-
			Coalesce(Sum(
				'amount', filter=Q(type_transactions='referalka')
			), Value(0))
		),
		none=Coalesce(Sum('amount', filter=Q(type_transactions='payliq')), Value(0)) -
			Coalesce(Sum('amount', filter=Q(type_transactions='paytask')), Value(0)),
		withdr=Coalesce(Sum('amount', filter=Q(type_transactions='withdrawal')), Value(0)),
	)
	all_money_zero = Feedback.objects.filter(task__finish=False, state_money=True, state_user_accept=True).exclude(task__executor=None).aggregate(rise=Coalesce(Sum('price_one'), Value(0)))
	all_money_withdr = Withdrawal.objects.filter(state=False).aggregate(rise=Coalesce(Sum('amount_two'), Value(0)))

	check_balance = Clients.objects.filter().aggregate(balance=Coalesce(Sum('balance'), Value(0)))

	data = {
		'customer_executor_time': {
			'customer_data': customer_data,
			'executor_data': executor_data,
		},
		'task_data_time': {
			'task': task_all_data,
			'task_finish': task_finish_data,
			'task_work': task_work_data,
		},
		'rise_time': {
			'rise_data': rise_data,
			'circulating_data': circulating_data,
		},
		'task_good_count': {
			'task_all_count': task['all'],
			'task_all_waited': task['waited'],
			'task_all_work': task['work'],
			'task_all_garant': task['garant'],
			'task_all_finish': task['finish'],
		},
		'task_problem_count': {
			'task_all_count': task['all'],
			'task_all_problem': task['problem'],
		},
		'rise_count': {
			'balance': round(balance['rise'], 2),
			'balance_rise': round(balance['avg_rise'], 2),
			'coversion': round(coversion * 100, 2),
		},
		'finance': {
			'all_money_liqpay': round(all_money['liqpay'], 2),
			'all_money_task': round(all_money['paytask'], 2),
			'all_money_finish': round(all_money['finish'], 2),
			'all_money_refer': round(all_money['refer'], 2),
			'all_money_rise': round(all_money['rise'], 2),
			'all_money_none': round(all_money['none'], 2),
			'all_money_zero': round(all_money_zero['rise'], 2),
			'all_money_withdr': round(all_money_withdr['rise'], 2),
		},
		'check': all_money['liqpay'] - all_money['withdr']
	}

	json_data = json.dumps({'success': True, 'data': json.loads(json.dumps(data))})
	return HttpResponse(json_data, content_type="application/json")