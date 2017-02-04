import vk
import datetime
import time
from string import ascii_letters,digits
import os
import shutil


APP_ID = 5768415
GROUP_NAME = "podkoren"


api = vk.API(vk.AuthSession(app_id=APP_ID,user_login='',
                            user_password='',
                            scope='offline'))
group_id=api.groups.getById(group_id=GROUP_NAME)[0]['gid']


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
    keys_list = ['attachment', 'from_id', 'online', 'likes', 'marked_as_ads', 'text',
                 'date','post_source', 'reply_count', 'comments', 'post_type', 'reposts',
                 'attachments', 'media', 'to_id', 'id']
    significant_keys = ['text', 'attachments', 'media', 'id']
    server_answer = api.wall.get(owner_id='-'+str(group_id), count=100)
    posts_count, posts = server_answer[0], server_answer[1:]
    offset = 0
    path_to = "посты (от " +\
        ''.join(filter(lambda x: x in ascii_letters + digits, str(datetime.date.today())))+")"
    try:
        os.mkdir(path_to)
    except:
        shutil.rmtree(path_to)
        os.mkdir(path_to)
    try:
        os.mkdir(path_to+'\\в_виде_текстов')
    except:
        shutil.rmtree(path_to+'\\в_виде_текстов')
        os.mkdir(path_to+'\\в_виде_текстов')
    try:
        os.mkdir(path_to+'\\по_папкам')
    except:
        shutil.rmtree(path_to+'\\по_папкам')
        os.mkdir(path_to+'\\по_папкам')
    while offset < posts_count:
        offset += len(posts)
        print('{}/{}'.format(offset, posts_count))
        for post_example in posts:
            # сохраняем в txt
            text = post_example.get('text')
            name = text[:20]
            name = ''.join(
                filter(lambda x:x not in '[|].,!?<>"',name)
            )+'[id'+str(post_example.get('id'))+']'+'.txt'
            with open(path_to+'\\в_виде_текстов'+"\\"+name, 'w',encoding='utf-8') as f:
                f.write(text)
                f.write('\n----------------------------------------')
                f.write('\n..........***К ЗАПИСИ ПРИКРЕПЛЕНЫ***.....')
                attachments = post_example.get('attachments')
                if attachments:
                    for attached in attachments:
                        type_ = attached.get('type')
                        f.write({'photo':'фотокарточка:',
                            'audio':'музыкальное сопровождение:',
                            'link':'ссылка:',
                            'doc':'документ:',
                            'video':'видеопленка:',
                            'poll':'опрос',
                            'album':'альбом'}[type_])

        time.sleep(1)
        server_answer = api.wall.get(owner_id='-' + str(group_id), count=100, offset=offset)
        posts = server_answer[1:]


save_all_posts()