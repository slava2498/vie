import logging
import math
import json
import os
import telebot
import locale

from telebot import TeleBot, types
from telebot.types import InputMediaPhoto, InputMediaDocument

from datetime import datetime

from django.db import models
from django.shortcuts import reverse
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete, m2m_changed, pre_save, post_delete
from django.utils.html import format_html
from django.utils import timezone

from settings import search_list, ASTUDY_TOKEN, CABINET_TOKEN, MEDIA_ROOT, URL_HOST, ID_MEDIA_GROUP
from settings import ASTUDY_LOGIN, CABINET_LOGIN, MEDIA_LOGIN
from settings import tz as local_time

from bot.texts.functions import font
from bot.texts.ru import CABINET_START


TYPE_FILE = (
	('photo', 'Фотография'),
	('document', 'Документ'),
)

class CommonInfo(models.Model):
	date_add = models.DateTimeField(
		verbose_name="Дата добавления", auto_now_add=True)
	date_change = models.DateTimeField(
		verbose_name="Дата изменения", auto_now=True)

	class Meta:
		abstract = True


class Files(CommonInfo):
	upload = models.FileField(upload_to='uploads/')
	type_file = models.CharField(verbose_name="Тип файла", max_length=100, choices=TYPE_FILE, blank=True, null=True)
	file_id = models.CharField(verbose_name="file_id", max_length=200, blank=True, null=True)

	def __str__(self):
		return '{}.{}'.format(str(self.id), self.upload)

@receiver(post_delete, sender=Files)
def delete_file(sender, **kwargs):
	instance = kwargs['instance']
	if instance.upload:
		if os.path.isfile(instance.upload.path):
			os.remove(instance.upload.path)


class Tracking(CommonInfo):
	name = models.CharField(verbose_name="Название",
							max_length=100, blank=True, null=True)
	code = models.CharField(
		verbose_name="Код", max_length=50, blank=True, null=True)
	link = models.CharField(verbose_name="Ссылка",
							max_length=100, blank=True, null=True)

	class Meta:
		verbose_name = "Трекинг"
		verbose_name_plural = "Трекинг"

	def __str__(self):
		return '{}'.format(self.name)


class Clients(CommonInfo):
	tracking = models.ForeignKey(Tracking, on_delete=models.SET_NULL,
								 verbose_name="Трекер", blank=True, null=True)
	refer = models.ForeignKey('Clients', on_delete=models.SET_NULL,
							  verbose_name="Рефер", blank=True, null=True)
	refer_code = models.CharField(
		verbose_name="Реферальный код", max_length=255, default='')
	chat_id = models.CharField(verbose_name="chat_id", max_length=100)
	login = models.CharField(verbose_name="login",
							 max_length=100, blank=True, null=True)
	str_name = models.CharField(
		verbose_name="Имя", max_length=100, blank=True, null=True)

	name = models.CharField(
		verbose_name="Имя", max_length=100, blank=True, null=True)
	city = models.CharField(verbose_name="Город",
							max_length=100, blank=True, null=True)
	more = models.CharField(verbose_name="Подробнее",
							max_length=299, blank=True, null=True)
	balance = models.FloatField(verbose_name="Баланс", default=0)
	bonus_balance = models.FloatField(verbose_name="Бонусный баланс", default=0)

	withdraw = models.TextField(
		verbose_name="Куда выводить средства", max_length=255, blank=True, null=True)

	bonuse = models.BooleanField(
		verbose_name="Использовать бонус", default=False)
	active = models.BooleanField(verbose_name="Активен", default=False)

	def fileLink(self):
		if self.login:
			return format_html('<a href="http://t.me/{}" target="_blank">Написать</a>'.format(self.login))
		else:
			return format_html('У пользователя отсутствует логин')

	fileLink.allow_tags = True
	fileLink.short_description = "Telegram"

	class Meta:
		verbose_name = "Карточку пользователя"
		verbose_name_plural = "Карточки пользователей"

	def __str__(self):
		return '{}.{} {} {}'.format(self.id, self.chat_id, self.login, self.str_name)


@receiver(post_save, sender=Clients)
def refer_client(sender, **kwargs):
	instance = kwargs['instance']
	if(kwargs['update_fields']):
		if('refer' in kwargs['update_fields']):
			client = instance
			text = 'По вашему реферальному коду зарегистрировался пользователь №{}'.format(client.id)


class Sending(CommonInfo):
	clients = models.TextField(verbose_name="chat_ids")
	text = models.TextField(verbose_name="Сообщение")
	buttons = models.TextField(verbose_name="json_buttons")
	token = models.CharField(verbose_name="Токен", max_length=100, default='')
	parse_mode = models.CharField(verbose_name="Кодировка", max_length=100, default='Markdown')
	type_action = models.CharField(verbose_name="Отправка/Редактирование", max_length=100, default='send_task_group')

	obj_task = models.ForeignKey(Tasks, on_delete=models.CASCADE, verbose_name="Задача", blank=True, null=True)

	class Meta:
		verbose_name = "Умная рассылка"
		verbose_name_plural = "Умная рассылка"

	def __str__(self):
		return '{}'.format(self.id)

class DialogControll(CommonInfo):
	client = models.ForeignKey(Clients, on_delete=models.CASCADE,
							   verbose_name="Пользователь")
	data = models.TextField(verbose_name="Доп параметры 1")
	controller = models.TextField(
		verbose_name="Доп параметры 2", blank=True, null=True)
	counter = models.IntegerField(verbose_name="Счётчик", default=0)

	class Meta:
		verbose_name = "Контроллер"
		verbose_name_plural = "Контроллеры"

	def __str__(self):
		return '{}'.format(self.client)
