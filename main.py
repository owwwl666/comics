import requests
from pathlib import Path

folder = 'Files'
Path(folder).mkdir(parents=True, exist_ok=True)


def downloads_file(url, folder, file_name, **kwargs):
    """Скачивание и сохранение файла"""
    response = requests.get(url, params=kwargs)
    response.raise_for_status()
    with open(Path(folder).joinpath(file_name), 'wb') as file:
        file.write(response.content)


def returns_information_comic(url):
    """Возвращет информацию о комиксе в json формате."""
    response = requests.get(url)
    response.raise_for_status()
    comic = response.json()
    return comic


downloads_file(
    url='https://imgs.xkcd.com/comics/python.png',
    folder=folder,
    file_name='python.png'
)

print(returns_information_comic(url='https://xkcd.com/353/info.0.json'))
