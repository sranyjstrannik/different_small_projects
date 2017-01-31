# сперва надо понять, как работает описание в xml
# потом написать функцию, которая парсит это описание в формат, пригодный для заливки в группу
# потом написать функцию, которая заливает все вк +

# ---* АЛГОРИТМ *---
# открываем xml-файл +
# парсим его на товары +
# парсим все существующие в группе вк товары +
# пробигаемся по всем товарам из xml, если их нет вк, добавляем +
# те товары, которые есть вк, но которых нет в xml, удаляем +


import vk
import json
from PIL import Image
import PIL
import requests
from io import BytesIO
import time

APP_ID = 5768415 # my_own_tricks


def get_settings():
    # ищет в папке со скриптом файл
    # settings.json со следующей структурой:
    # login: login
    # password: password
    # group_id: group_id
    with open("settings.json",'r') as f:
        settings = json.load(f)
    return settings


def find_and_parse_xml():
    """
        ищет в папке со скриптом находящиеся там xml-файлы
        берет из них последний по времени,самый свежий
        парсит его товары
        возвращает эти товары в качестве массива
    """
    import os
    xml_for_work =sorted([entry for entry in os.scandir() if entry.name.endswith('.xml')],key=lambda x:os.path.getmtime(x.path))[-1]
    xml_path = xml_for_work.path
    # открываем xml file
    from bs4 import BeautifulSoup
    t = open(xml_path,mode='r',encoding='utf-8').read()
    soup = BeautifulSoup(t,'xml')
    # выдираем все категории, быть может, потом пригодится
    ctgs = {int(tag['id']):tag.text for tag in soup.findAll('category')}
    # выдираем все товары
    offers = soup.findAll('offer')
    all_categories = set()
    result = []
    for offer in offers:
        t = {
            'name': offer.find('name'),
            'description': offer.description,
            'category_id': 1,
            'price': offer.price,
            'photo_url': offer.picture
        }
        for key,value in t.items():
            if type(value) not in [type(1),type('1')]:
                t[key] = value.text
        t['name'] = t['name'][:100]

        all_categories.add(offer.categoryId.text)
        result.append(t)
    # print([ctgs[int(c)] for c in all_categories])
    # print(len(result))
    return result

def parse_all_uploaded_items(group_id,api_client):
    """
        все существующие товары из группы group_id
        сохраняем в массив
    """
    offset = 0
    all_items = []
    while True:
        next_piece = api_client.market.get(
            owner_id = -int(group_id),
            count = 200,
            offset = offset
        )
        time.sleep(0.5)
        if len(next_piece):
            all_items += next_piece[1:]
        offset = len(all_items)
        if len(next_piece) < 190:
            break
    for item in all_items:
        item['need_delete'] = True
    return all_items


def upload_item(d, settings, api_client=None):
    """"
        d имеет структуру {
        owner_id: -id-группы / либо id владельца
        name: Пальто Victoria&apos;s Secret 155-460
        description: Состав: шерсть с подкладкой из полиэстера.
        Размеры: 12 (48-50 российский).
        Цвета: черный.
        category_id: (1:"Женская одежда", 4:"Обувь и сумки",5:"Аксессуары и украшения")
        price:
        main_photo_id: получается через отдельную процедуру
    """
    if not api_client:
        api_client = vk.API(vk.AuthSession(APP_ID, settings['login'], settings['password'],scope="market,photos"))

    if 'main_photo_id' not in d:
        # загружаем фото
        if 'photo_url' not in d:
            link = "http://www.pink-girl.ru/img/small/239425.jpg"
        else: link = d['photo_url']
        response = requests.get(link)
        img = Image.open(BytesIO(response.content))
        height, width = img.height, img.width
        side = min(height,width)
        if side < 400:
            coeff = 400/side
            img = img.resize((int(height*coeff)+1, int(width*coeff)+1), PIL.Image.BILINEAR)
            height, width = int(height*coeff)+1, int(width*coeff)+1
            side = min(height,width)
        img.save('someImg.jpg')
        if height > width:
            crop_x = height//2 - side//2
            crop_y = 0
        else:
            crop_x = 0
            crop_y = width//2 - side//2
        crop_x, crop_y = crop_y, crop_x
        upload_url = api_client.photos.getMarketUploadServer(
            group_id=settings["group_id"],
            main_photo=1,
            crop_x=crop_x,
            crop_y=crop_y,
            crop_width=side)['upload_url']
        # Передайте файл на адрес upload_url, полученный в предыдущем пункте,
        # сформировав POST-запрос с полем file.
        # Это поле должно содержать изображение в формате multipart/form-data.
        r = requests.post(upload_url,files={'photo': open('someImg.jpg','rb')})
        # После успешной загрузки сервер возвращает в ответе JSON-объект
        #  с полями server, photo, hash, crop_data, crop_hash:
        photo_dict = json.loads(r.text)
        # Чтобы сохранить фотографию, вызовите метод photos.saveMarketPhoto
        #  с параметрами server, photo, crop_data, crop_hash, полученными на предыдущем этапе.
        #  Если фотография не основная, поля crop_data и crop_hash передавать не нужно.
        r  = api_client.photos.saveMarketPhoto(
            group_id=settings['group_id'],
            server=photo_dict['server'],
            photo=photo_dict['photo'],
            crop_data=photo_dict['crop_data'],
            crop_hash=photo_dict['crop_hash'],
            hash=photo_dict['hash']
        )
        d['main_photo_id'] = r[0]['pid']
    api_client.market.add(**d)


settings = get_settings()
for key,value in settings.items():
    print(key,value)
r = find_and_parse_xml() # получили список всех товаров из xml
api_client = vk.API(vk.AuthSession(APP_ID, settings['login'], settings['password'],scope="market,photos"))
existing_items = parse_all_uploaded_items(settings['group_id'],api_client)
t1 = time.time()
# пробегаемся по всем товарам
new_uploaded = 0
for index,item in enumerate(r):
    item['owner_id'] = str(-int(settings['group_id']))
    # проверяем, есть ли такой товар в магазине
    flag = False # флаг, указывающий, есть ли такой товар в магазине
    for ex_item in existing_items:
        if ex_item['title'] == item['name']:
            flag = True
            ex_item['need_delete'] = False
            break
    if flag: continue # если такой товар уже есть
    try:
        upload_item(item, settings,api_client=api_client)
        new_uploaded += 1
        time.sleep(0.5)
    except Exception as e:
        print('upload exception', index)
        #print(e)
print('total time:',time.time()-t1)
print('uploaded_items:',new_uploaded)

# удаляем все элементы магазина, которых нет в xml
t1 = time.time()
cnt = 0
for item in existing_items:
    cnt += 1
    if item['need_delete']:
        flag = True
        while flag:
            try:
                api_client.market.delete(
                    owner_id = -int(settings['group_id']),
                    item_id = item['id']
                )
                flag = False
                print(cnt)
            except requests.exceptions.Timeout:
                print('hmmmm, timeout')
                time.sleep(0.5)
                continue
        time.sleep(0.3)
print("deletion time:", time.time()-t1)



