import requests
import random
import os
from environs import Env
from pathlib import Path


def upload_number_random_comic():
    """Загружает номер случайного комикса."""
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    random_comic_number = random.randint(1, response.json()['num'])
    return random_comic_number


def download_comic(url, comic_path):
    """Скачивает и сохраняет комикс."""
    response = requests.get(url)
    response.raise_for_status()
    comic_image = requests.get(response.json()['img'])
    with open(comic_path, 'wb') as file:
        file.write(comic_image.content)


def upload_comments_comic(url):
    """Загружает комментарии к комиксу."""
    response = requests.get(url)
    response.raise_for_status()
    comic = response.json()
    return comic['alt']


def get_address_upload_photo(parameters):
    """Получает адрес для загрузки фото."""
    response = requests.get(
        f'https://api.vk.com/method/photos.getWallUploadServer', params=parameters)
    response.raise_for_status()
    return response.json()['response']['upload_url']


def send_comic_server(comic_path):
    """Отправляет комикс на сервер Вконтакте.

    Возвращает ответ от него в виде json формата."""
    path_ = Path.cwd().joinpath(comic_path)

    with open(path_, 'rb') as file:
        files = {
            'photo': file
        }
        url = get_address_upload_photo(parameters)
        response = requests.post(url, files=files)
        response.raise_for_status()
    return response.json()


def save_comic_in_group_album(parameters):
    """Сохраняет комикс в альбоме группы Вконтакте.

    Возвращает json с информацией о загруженном комиксе.
    """
    url = f'https://api.vk.com/method/photos.saveWallPhoto'
    parameters |= send_comic_server(comic_path=comic_path)
    saving_comic_group_album = requests.post(url, params=parameters)
    saving_comic_group_album.raise_for_status()
    return saving_comic_group_album.json()


def publish_post_in_group(comic_number, parameters):
    """Публикует пост на стену в группу Вконтакте."""
    media_id = save_comic_in_group_album(parameters)['response'][0]['id']
    url = f'https://api.vk.com/method/wall.post'
    parameters |= {
        'owner_id': -env.int('VK_GROUP_ID'),
        'from_group': 1,
        'attachments': f'{"photo"}{env.int("VK_OWNER_ID")}_{media_id}',
        'message': upload_comments_comic(url=f'https://xkcd.com/{comic_number}/info.0.json')
    }
    requests.post(url, params=parameters).raise_for_status()


if __name__ == '__main__':
    env = Env()
    env.read_env()

    parameters = {
        'group_id': env('VK_GROUP_ID'),
        'access_token': env('VK_ACCESS_TOKEN'),
        'v': env('VK_API_VERSION'),
    }

    comic_number = upload_number_random_comic()

    comic_url = f'https://xkcd.com/{comic_number}/info.0.json'
    comic_path = f'comic_{comic_number}.png'

    download_comic(url=comic_url, comic_path=comic_path)
    publish_post_in_group(comic_number=comic_number, parameters=parameters)

    os.remove(comic_path)
