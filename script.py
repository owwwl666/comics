import requests
import random
import os
from environs import Env


def download_all_comics():
    """Скачивает все комиксы."""
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


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


def get_uploading_photo_address(group_id, access_token, api_version):
    """Получает адрес для загрузки фото."""
    params = {
        'group_id': group_id,
        'access_token': access_token,
        'v': api_version
    }
    response = requests.get(
        f'https://api.vk.com/method/photos.getWallUploadServer', params=params)
    response.raise_for_status()
    return response.json()['response']['upload_url']


def send_server_comic(url, comic_path):
    """Отправляет комикс на сервер Вконтакте.

    Возвращает ответ от него в виде json формата."""
    with open(comic_path, 'rb') as file:
        files = {'photo': file}
        response = requests.post(url, files=files)
    response.raise_for_status()
    params = response.json()
    return params['server'], params['photo'], params['hash']


def save_in_album_comic(server_params, group_id, access_token, api_version):
    """Сохраняет комикс в альбоме группы Вконтакте.

    Возвращает json с информацией о загруженном комиксе.
    """
    server, photo, hash = server_params
    params = {
        'group_id': group_id,
        'access_token': access_token,
        'v': api_version,
        'server': server,
        'photo': photo,
        'hash': hash
    }
    sending_comic = requests.post(
        f'https://api.vk.com/method/photos.saveWallPhoto', params=params)
    sending_comic.raise_for_status()
    return sending_comic.json()


def publish_in_group_post(comic_comments, group_id, access_token, api_version):
    """Публикует пост на стену в группу Вконтакте."""
    download_url = get_uploading_photo_address(group_id, access_token, api_version)
    sending_to_server = send_server_comic(download_url, comic_path)
    save_to_album = save_in_album_comic(sending_to_server, group_id, access_token, api_version)

    media_id = save_to_album['response'][0]['id']
    owner_id = save_to_album['response'][0]['owner_id']

    params = {
        'group_id': group_id,
        'access_token': access_token,
        'v': api_version,
        'owner_id': -group_id,
        'from_group': 1,
        'attachments': f'{"photo"}{owner_id}_{media_id}',
        'message': comic_comments
    }

    publishing_post = requests.post(
        f'https://api.vk.com/method/wall.post', params=params)
    publishing_post.raise_for_status()


if __name__ == '__main__':
    env = Env()
    env.read_env()

    group_id = env.int('VK_GROUP_ID')
    access_token = env.str('VK_ACCESS_TOKEN')
    api_version = env('VK_API_VERSION')

    comic_number = random.randint(1, download_all_comics()['num'])

    comic_path = f'comic_{comic_number}.png'

    comic_img, comic_comments = download_comic()

    with open(comic_path, 'wb') as file:
        file.write(comic_img.content)

    publish_in_group_post(comic_comments, group_id, access_token, api_version)

    os.remove(comic_path)
