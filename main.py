from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import os
from yandex_music import Client as Yandex, Playlist, Track


def get_spotify_client() -> Spotify:
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = Spotify(client_credentials_manager=client_credentials_manager)

    return sp


def get_yandex_client() -> Yandex:
    client_token = os.getenv('YANDEX_CLIENT_TOKEN')
    client = Yandex(client_token).init()
    return client


def get_spotify_playlist_name(client: Spotify, id: str) -> str:
    playlist = client.playlist(id)
    name = playlist['name']
    return name


def get_spotify_playlist_tracklist(client: Spotify, id: str) -> list[str]:
    playlist = client.playlist_items(id)
    length = playlist['total']
    tracklist = []
    for i in range(0, length, 100):
        playlist = client.playlist_items(id, offset=i)
        items = playlist['items']
        for item in items:
            name = item['track']['name']
            artists = item['track']['artists']
            artists_names = [artist['name'] for artist in artists]
            full_name = f"{name} - {', '.join(artists_names)}"
            tracklist.append(full_name)
    return tracklist


def create_yandex_playlist(client: Yandex, name: str) -> Playlist:
    return client.users_playlists_create(name)


def get_yandex_track(client: Yandex, query: str) -> Track | None:
    search_result = client.search(query)

    if search_result.best is None:
        return None

    type_ = search_result.best.type
    if type_ != 'track':
        return None

    best = search_result.best.result
    return best


def transfer_tracklist_to_playlist(client: Yandex, tracklist: list[str], playlist: Playlist):
    revision = playlist.revision
    total = len(tracklist)
    count = 0
    list_unavailable = []
    count_unavailable = 0

    for name in tracklist:
        track = get_yandex_track(client, name)
        if track is None:
            list_unavailable.append(name)
            count_unavailable += 1
        else:
            client.users_playlists_insert_track(
                kind=playlist.kind,
                track_id=track.track_id.split(':')[0],
                album_id=track.albums[0].id,
                revision=revision
            )
            count += 1
            revision += 1
        print(f"Transferred {count} of {total}, {count_unavailable} unavailable", end='\r')
    print(f"Transferred {count} of {total}" + " " * (len(str(count_unavailable)) + 14), end='\r\n')
    if count_unavailable:
        print(f"{count_unavailable} unavailable:\n{'\n'.join(list_unavailable)}")


if __name__ == '__main__':
    id = input("Enter Spotify playlist id: ")

    spotify_client = get_spotify_client()

    print(f"Starting tracklist export", end='\r')

    playlist_name = get_spotify_playlist_name(spotify_client, id)
    tracklist = get_spotify_playlist_tracklist(spotify_client, id)

    print("Tracklist ready" + " " * 11, end='\r\n')

    yandex_client = get_yandex_client()

    print(f"Starting transfer")

    playlist = create_yandex_playlist(yandex_client, playlist_name)
    transfer_tracklist_to_playlist(yandex_client, tracklist, playlist)

    print("Done")
