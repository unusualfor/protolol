# encoding=latin-1

from pprint import pprint
import random
import sys
import telepot
from telepot.delegate import per_chat_id, create_open, pave_event_space, per_inline_from_id
from telepot.namedtuple import InputTextMessageContent, InlineQueryResultArticle


def select_jokes(keyword):
    jokes = []
    file = open("jokes.txt")
    for joke in file:
        jokes.append(joke)
    if keyword == "random" or keyword == "joke":
        return jokes
    else:
        proto_jokes = []
        for joke in jokes:
            if keyword.lower() in joke.lower():
                proto_jokes.append(joke)
        return proto_jokes


def decide_joke(keyword):
    joke_list = select_jokes(keyword)
    num_jokes = sum(1 for joke in joke_list)
    if num_jokes < 1:
        return "No jokes related to keyword: " + keyword
    return random.choice(joke_list)


class MyChatHandler(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(MyChatHandler, self).__init__(*args, **kwargs)

    @staticmethod
    def on_chat_message(update):
        pprint(update)
        content_type, chat_type, chat_id = telepot.glance(update)

        if content_type == 'text':

            sentence = update['text']
            if update['chat']['type'] == 'group':
                receiver = update['chat']['title']
            elif update['chat']['type'] == 'private':
                receiver = 'private chat'
            sender = ""
            if update['from']['first_name']:
                sender += update['from']['first_name']
            if 'last_name' in update['from']:
                sender += " " + update['from']['last_name']

            if sentence[:1] == '/':
                print('Got command: %s' % sentence)

                if sentence == "/start":
                    bot.sendMessage(chat_id, "Are you interested in a geeky joke?")

            elif sentence[:3] == '*#*':
                print('Got my same reply, I am not doing anything')

            else:
                sent = decide_joke(sentence.lower())
                if DEBUG:
                    report_msg = "Sending: \"" + str(sent).replace("\n","") + "\"\nTo chat: " + str(receiver) + "\nTriggered by: " + str(sender) + "\nRequired content: " + sentence
                    bot.sendMessage(debug_chat_id, report_msg)
                bot.sendMessage(chat_id, sent)


class InlineHandler(telepot.helper.InlineUserHandler, telepot.helper.AnswererMixin):
    def __init__(self, *args, **kwargs):
        super(InlineHandler, self).__init__(*args, **kwargs)

    def on_inline_query(self, msg):
        def compute():
            if query_string == "":
                return []
            articles = []
            keyword = query_string.lower()
            joke_list = select_jokes(keyword)

            i = 0
            for joke in joke_list:
                str_id = keyword + str(i)
                articles.append(InlineQueryResultArticle(id=str_id, title=joke,
                                                         input_message_content=InputTextMessageContent(
                                                             message_text=joke)))
                i = i + 1

            return articles

        query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
        print('Inline Query:', query_id, from_id, query_string)

        self.answerer.answer(msg, compute)

    def on_chosen_inline_result(self, msg):
        pprint(msg)
        result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
        print(self.id, ':', 'Chosen Inline Result:', result_id, from_id, query_string)

        if DEBUG:
            first_name = msg['from']['first_name']
            report_msg = "Inline query from " + first_name + " (" + str(from_id) + "), choice " + result_id
            bot.sendMessage(13113271, report_msg)


# MAIN #

DEBUG = False
TOKEN = None
if len(sys.argv) < 2:
    print("Usage: python protolol.py TOKEN [DEBUG debug_chat_id]")
    exit(0)
elif len(sys.argv) == 4:
    if str(sys.argv[2]).lower() == "debug":
        debug_chat_id = sys.argv[3]
        print("DEBUG mode on, sending debug info to chat_id " + debug_chat_id)
        DEBUG = True
else:
    DEBUG = False

TOKEN = sys.argv[1]
bot = telepot.DelegatorBot(TOKEN, [
    pave_event_space()(per_chat_id(), create_open, MyChatHandler, timeout=10),
    pave_event_space()(per_inline_from_id(), create_open, InlineHandler, timeout=10),
])
bot.message_loop(run_forever='Listening ...')
answerer = telepot.helper.Answerer(bot)

# END MAIN #
