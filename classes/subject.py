# -*- coding: utf-8 -*-
import datetime
from bot.models import *
from django.utils import timezone
from django.core.paginator import Paginator
from telebot import types

class SubjectClass:

	subjects = ''
	keyboard = ''
	clientfilter = ''
	count_list = 6
	COUNT_ROW = 2

	def __init__(self):
		self.subjects = Subject.objects.filter()

	def subject_paginator(self, data, page):
		self.subjects = Paginator(data, self.count_list)
		self.subjects = self.subjects.page(int(page))

	def generate_buttons(self, client, data, subject_id, page, parent_id, type_button, back=False, paginator=True):
		if(not back):
			self.subject_paginator(data, int(page))
		else:
			self.subjects = Paginator(data, self.count_list)
			self.sub = self.subjects.page(1)
			for x in self.subjects.page_range:
				for y in self.subjects.page(x).object_list:
					if(int(subject_id) == y.id):
						self.sub = self.subjects.page(x)
						page = x
						break

			self.subjects = self.sub
			print(self.subjects)
			print(self.subjects.object_list)

		buttons = []
		for x in self.subjects.object_list:
			print(x)
			self.get_filter(client)
			postfix = ''
			if(type_button == 'SUBJECT100'):
				postfix = '✅'

			buttons.append({'text': x.name + postfix, 'callback_data': '{}_{}_{}_{}'.format(type_button, x.id, str(page), str(parent_id))})

		print(buttons)
		self.keyboard = types.InlineKeyboardMarkup(True)
		f = lambda A, n: [A[i:i+n] for i in range(0, len(A), n)]
		self.keyboard.keyboard = f(buttons, self.COUNT_ROW)

		if(paginator):
			buttons_paginator = []
			if(self.subjects.has_previous()):
				buttons_paginator.append({'text': '◀️', 'callback_data': '{}PAGE_{}_{}_{}'.format(
					type_button,
					str(subject_id),
					self.subjects.previous_page_number(),
					parent_id)
				})

			buttons_paginator.append({'text': 'Назад', 'callback_data': '{}BACK_{}_{}_{}'.format(type_button, str(subject_id), str(page), str(parent_id))})
			if(self.subjects.has_next()):
				buttons_paginator.append({'text': '▶️', 'callback_data': '{}PAGE_{}_{}_{}'.format(
					type_button,
					str(subject_id),
					self.subjects.next_page_number(),
					parent_id)
				})
	
			self.keyboard.keyboard.append(buttons_paginator)