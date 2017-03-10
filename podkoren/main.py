import vk
import datetime
import time
from string import ascii_letters,digits
import os
import shutil
import re


APP_ID = 5768415
GROUP_NAME = "podkoren"


api = vk.API(vk.AuthSession(app_id=APP_ID,user_login='',
                            user_password='',
                            scope='offline'))
group_id=api.groups.getById(group_id=GROUP_NAME)[0]['gid']


# находит все тэги
# возвращает их отдельно и отдельно возвращает исходный текст
# уже БЕЗ ТЕГОВ
def extract_tags(txt):
    tags = re.findall(r'#\w+', txt)
    for tag in tags: txt = txt.replace(tag, '')
    return tags, txt

def extract_name(txt):
    name = re.split(r'[.!?]', txt, maxsplit=1)[0]
    if not name: #TODO
        name = 'ну_так_ну_тип_пойдет'
    return name, txt


# для работы исключительно с параграфом
class Paragraph:
    def __init__(self, tags, name, txt):
        self.tags = tags
        self.text = txt
        self.name = name
        self.images = [] # путь к изображению и описание
        self.other_attachments = [None]

    def __str__(self):
        result = '<big_text>'
        result += '<h1>' + self.name + '</h1>'
        for tag in self.tags:
            result += '<tag>{}</tag>'.format(tag)
        result += ('<br>' if self.tags else '') + '</br>' + self.text
        if self.images:
            result += '<table>'
            for image in self.images:
                result += "<tr> <img src='{}'></img> <p class='description'> {} </p> </tr>".format(image[0], image[1])
            result += '</table>'
        return result + '</big_text> <br>'


# для работы искючительно с телом документа
class Body:
    """
        Итак, предполагаемый функционал
        1. Возможность добавить абзац текста +
        2. Возможность добавить картинку (с подписью или без) к последнему добавленному параграфу +
        3. Возможность добавить инфу о том, что к абзацу что-то прикреплено +
        4. Преставить всё тело в текстовом виде +
    """
    def __init__(self):
        # структура массива paragraphs
        self.paragraphs = []

    def add_paragraph(self, txt):
        tags, txt = extract_tags(txt) # выделяем тэги, если есть
        name, txt = extract_name(txt)
        self.paragraphs.append(Paragraph(tags, name, txt))

    def add_picture(self, img, img_text):
        self.paragraphs[-1].images.append([img, img_text])

    def add_attachment(self, text):
        self.paragraphs[-1].other_attachments.append(text)

    def __str__(self):
        return '<body>' + ''.join(str(p) for p in self.paragraphs) + '</body>'

# для работы с html полностью
class Html:
    """
        Функции, которые реализованы в этом классе
        1. Добавление таблицы стилей
        2. Сохранение этого вот всего в текстовый файл
    """
    def __init__(self, name='все посты.html'):
        self.meta = """
        <!DOCTYPE html>
        <meta charset="utf-8">
        """
        self.name = name
        self.body = Body()
        self.style = None

    def add_stylesheet(self, path='./stylesheet.css'):
        self.style = path

    def __str__(self):
        self.headers = """
           	    <head>
             		<title>{}</title>
             		<link rel='stylesheet' href='{}'>
        	    </head>
                """.format(self.name, self.style)
        return self.meta +'<html>' + self.headers + str(self.body) + '</html>'

    def write_down(self, path=None):
        if path:
            f = open(path+'/'+self.name, 'w', encoding='utf-8')
        else:
            f = open(self.name, 'w', encoding='utf-8')
        f.write(str(self))
        f.close()

# сохраняем всех пользователей
def save_all_users(api=api,group_id=group_id):
    users_list = open("users_list"+
                  ''.join(filter(lambda x:x in ascii_letters+digits, str(datetime.datetime.today())))
                  +".txt","w")
    offset = 0
    server_answer = api.groups.getMembers(group_id=group_id)
    members_count, users_bunch = server_answer['count'], server_answer['users']
    while offset < members_count:
        offset += len(users_bunch)
        print("{}/{}".format(offset, members_count))
        users_list.write('\n'.join(map(str,users_bunch))+'\n')
        time.sleep(1)
        server_answer = api.groups.getMembers(group_id=group_id,offset=offset)
        users_bunch = server_answer['users']
    users_list.close()


# сохраняем все посты
def save_all_posts(api=api, group_id=group_id):

    # все возможные ключи ответа
    keys_list = ['attachment', 'from_id', 'online', 'likes', 'marked_as_ads', 'text',
                 'date','post_source', 'reply_count', 'comments', 'post_type', 'reposts',
                 'attachments', 'media', 'to_id', 'id']

    # те из этих ключей, которые мы обрабатываем
    significant_keys = ['text', 'attachments', 'media', 'id']

    # запрос на первые сто записей
    server_answer = api.wall.get(owner_id='-'+str(group_id), count=100)
    posts_count, posts = server_answer[0], server_answer[1:]
    offset = 0

    # формируем нашу аштиэмэльку
    mainHtml = Html()
    mainHtml.add_stylesheet()

    # в процессе используем mainHtml.body.add_paragraph()
    # mainHtml.body.add_picture()
    # mainHtml.body.add_attachment()


    while offset < posts_count:
        offset += len(posts)
        print('{}/{}'.format(offset, posts_count))
        for post_example in posts[:100]: # для удобства отладки рассматриваем только первые десять постов
             # сохраняем в txt
            text = post_example.get('text')
            mainHtml.body.add_paragraph(text)
            attachments = post_example.get('attachments')
            if attachments:
                for attached in attachments:
                    type_ = attached.get('type')
                    if type_ == 'audio':
                        mainHtml.body.add_attachment('музыкальное сопровождение: {} - {}'.format(attached['audio']['artist'],
                                                             attached['audio']['title']))
                    elif type_ == 'photo':
                        mainHtml.body.add_picture(attached['photo']['src_big'], attached['photo']['text'])
                    # elif type_ == 'photo':
                    #         f.write('фотокарточка')
                    #     elif type_ == 'link':
                    #         f.write('ccылка:' + attached['link']['title'] + ':' +
                    #                 attached['link']['url'])
                    #     elif type_ == 'doc':
                    #         f.write('документ:' + attached['doc']['title'])
                    #     elif type_ == 'video':
                    #         f.write('видеопленка:' + attached['video']['title'])
                    #     elif type_ == 'poll':
                    #         f.write('опрос:' + attached['poll']['question'])
                    #     elif type_ == 'album':
                    #         f.write('альбом "' + attached['album']['title'] + '": ' + attached['album']['description'])
        break
        time.sleep(1)
        server_answer = api.wall.get(owner_id='-' + str(group_id), count=100, offset=offset)
        posts = server_answer[1:]
    mainHtml.write_down()

save_all_posts()