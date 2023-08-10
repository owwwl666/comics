import requests
import random
import os
from environs import Env


def upload_random_comic_number():
    """Загружает номер случайного комикса."""
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    random_comic_number = random.randint(1, response.json()['num'])
    return random_comic_number


def download_comic():
    """Скачивает комикс.

    Возвращает картинку комикса и комментарии к нему.
    """
    url = f'https://xkcd.com/{comic_number}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    comic = response.json()

    comic_img = requests.get(comic['img'])
    comic_img.raise_for_status()
    comic_comments = comic['alt']

    return comic_img, comic_comments


def get_uploading_photo_address(parameters):
    """Получает адрес для загрузки фото."""
    response = requests.get(
        f'https://api.vk.com/method/photos.getWallUploadServer', params=parameters)
    response.raise_for_status()
    return response.json()['response']['upload_url']


def send_server_comic(url, comic_path):
    """Отправляет комикс на сервер Вконтакте.

    Возвращает ответ от него в виде json формата."""
    with open(comic_path, 'rb') as file:
        files = {'photo': file}
        response = requests.post(url, files=files)
    response.raise_for_status()
    return response.json()


def save_in_group_album_comic(server_params, parameters):
    """Сохраняет комикс в альбоме группы Вконтакте.

    Возвращает json с информацией о загруженном комиксе.
    """
    parameters |= server_params
    sending_comic = requests.post(
        f'https://api.vk.com/method/photos.saveWallPhoto', params=parameters)
    sending_comic.raise_for_status()
    return sending_comic.json()


def publish_in_group_post(comic_comments, parameters):
    """Публикует пост на стену в группу Вконтакте."""
    download_url = get_uploading_photo_address(parameters)
    sending_to_server = send_server_comic(download_url, comic_path)
    save_to_album = save_in_group_album_comic(sending_to_server, parameters)

    media_id = save_to_album['response'][0]['id']
    owner_id = save_to_album['response'][0]['owner_id']

    parameters |= {
        'owner_id': -env.int('VK_GROUP_ID'),
        'from_group': 1,
        'attachments': f'{"photo"}{owner_id}_{media_id}',
        'message': comic_comments
    }

    publishing_post = requests.post(
        f'https://api.vk.com/method/wall.post', params=parameters)
    publishing_post.raise_for_status()


if __name__ == '__main__':
    env = Env()
    env.read_env()

    parameters = {
        'group_id': env('VK_GROUP_ID'),
        'access_token': env('VK_ACCESS_TOKEN'),
        'v': env('VK_API_VERSION'),
    }

    comic_number = upload_random_comic_number()

    comic_path = f'comic_{comic_number}.png'

    comic_img, comic_comments = download_comic()

    with open(comic_path, 'wb') as file:
        file.write(comic_img.content)

    publish_in_group_post(comic_comments, parameters)

    os.remove(comic_path)
