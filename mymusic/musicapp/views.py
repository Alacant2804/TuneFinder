from django.shortcuts import render
from django.shortcuts import redirect
from .forms import ArtistTrackInputForm
import requests
from decouple import config
import base64
import logging


logger = logging.getLogger(__name__)

SPOTIFY_CLIENT_ID = config('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = config('SPOTIFY_CLIENT_SECRET')


def index(request):
    form = ArtistTrackInputForm()  # Create an instance of the form
    recommended_tracks = None

    try:
        access_token = get_new_access_token()

        if request.method == "POST":
            form = ArtistTrackInputForm(request.POST)

            if form.is_valid():
                artist_name = form.cleaned_data['artist_name']
                track_name = form.cleaned_data['track_name']

                if track_name:  # If a track name is provided
                    track_id = get_spotify_track_id(access_token, track_name, artist_name)

                    if not track_id:
                        return render(request, 'error.html', {"message": "Track not found."})

                    recommended_tracks = get_spotify_recommendations_by_track(access_token, track_id)

                    if not recommended_tracks:
                        return render(request, 'error.html', {"message": "Sorry, we couldn't find any recommendations for that track at the moment."})

                    return render(request, 'recommendation.html', {
                        'track_name': track_name,
                        'recommended_tracks': recommended_tracks
                    })

                else:  # Neither artist nor track provided
                    return render(request, 'error.html', {"message": "Please provide a track."})

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")  # Logging the exception
        return render(request, 'error.html', {"message": "An unexpected error occurred. Please try again later."})

    return render(request, 'index.html', {'form': form})



def get_new_access_token():
    client_id = config('SPOTIFY_CLIENT_ID')
    client_secret = config('SPOTIFY_CLIENT_SECRET')
    
    auth_url = 'https://accounts.spotify.com/api/token'
    
    auth_response = requests.post(
        auth_url, 
        headers={
            'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode()).decode()
        },
        data={'grant_type': 'client_credentials'}
    )
    
    if auth_response.status_code != 200:
        raise Exception("Failed to get access token from Spotify")
    
    return auth_response.json()['access_token']


def get_spotify_track_id(access_token, track_name, artist_name=None):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    search_url = "https://api.spotify.com/v1/search"
    query = track_name
    if artist_name:
        query = f"{artist_name} {track_name}"
    params = {
        "q": query,
        "type": "track",
        "limit": 10 
    }

    search_response = requests.get(search_url, headers=headers, params=params)
    if search_response.status_code != 200:
        raise Exception("Failed to search track")

    track_data = search_response.json()
    if not track_data['tracks']['items']:
        return None

    # Loop through the search results to verify if they match the track and artist name
    for track in track_data['tracks']['items']:
        if track['name'].lower() == track_name.lower():
            for artist in track['artists']:
                if artist['name'].lower() == artist_name.lower():
                    return track['id']
    
    return None  # Return None if no exact matches found.


def get_spotify_recommendations_by_track(access_token, track_id):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    recommendations_url = "https://api.spotify.com/v1/recommendations"
    params = {
        "seed_tracks": track_id,
        "limit": 10  # Number of tracks to fetch
    }

    recommendations_response = requests.get(recommendations_url, headers=headers, params=params)
    if recommendations_response.status_code != 200:
        raise Exception("Failed to get recommendations")

    recommendation_data = recommendations_response.json()
    track_artist_pairs = [(track['name'], track['artists'][0]['name']) for track in recommendation_data['tracks']]
    
    return track_artist_pairs
