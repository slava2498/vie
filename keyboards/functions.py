from telebot import types

from bot.texts.functions import font
from bot.keyboards import task as task_keyboard
from bot.keyboards import tags as tags_keyboard

constructor = lambda A, n: [A[i:i+n] for i in range(0, len(A), n)]

def del_send_message(
		telegram_bot, 
		chat_id, 
		text,
		user,
		step_task,
		message_id=0,
		keyboard=[]
	):

	print(151, step_task)
	if(not keyboard):
		keyboard = types.ReplyKeyboardMarkup(True)
		dict_text = {**task_keyboard.dict_text, **tags_keyboard.dict_text}
		keyboard.keyboard = dict_text[step_task]['buttons']
	
	user.set_steper(step_task, message_id)

	if(message_id):
		try:
			telegram_bot.delete_message(chat_id=chat_id, message_id=message_id)
		except Exception as e:
			print(146, e)
	new_message = telegram_bot.send_message(chat_id=chat_id, parse_mode="HTML", text=text, reply_markup=keyboard)

	user.step.message_id = new_message.message_id
	user.step.save(update_fields=['message_id'])

	return new_message.message_id