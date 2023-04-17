import requests
import pygame
import os

link = 'https://geocode-maps.yandex.ru/1.x'
data = {'geocode': input().replace(' ', '+'),
        'apikey': '40d1649f-0493-4b70-98ba-98533de7710b',
        'format': 'json'}
coords = ','.join(requests.get(link, params=data).json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject'][
    'Point']['pos'].split())

search_api_server = "https://search-maps.yandex.ru/v1/"
search_params = {
    "apikey": 'dda3ddba-c9ea-4ead-9010-f43fbc15c6e3',
    "text": "музыкальный магазин",
    "lang": "ru_RU",
    "ll": coords,
    "type": "biz"}

response = requests.get(search_api_server, params=search_params).json()

organization = response["features"][0]
org_name = organization["properties"]["CompanyMetaData"]["name"]
org_address = organization["properties"]["CompanyMetaData"]["address"]

point = organization["geometry"]["coordinates"]
org_point = "{0},{1}".format(point[0], point[1])
delta = "0.02"

# Собираем параметры для запроса к StaticMapsAPI:
map_params = {
    "ll": coords,
    "spn": ",".join([delta, delta]),
    "l": "map",
    "pt": "{0},org".format(org_point)
}

map_api_server = "http://static-maps.yandex.ru/1.x/"
response = requests.get(map_api_server, params=map_params)

map_file = "map.png"
with open(map_file, "wb") as file:
    file.write(response.content)

pygame.init()
screen = pygame.display.set_mode((600, 450))
# Рисуем картинку, загружаемую из только что созданного файла.
screen.blit(pygame.image.load(map_file), (0, 0))
# Переключаем экран и ждем закрытия окна.
pygame.display.flip()
while pygame.event.wait().type != pygame.QUIT:
    pass
pygame.quit()

# Удаляем за собой файл с изображением.
os.remove(map_file)