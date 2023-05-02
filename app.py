import spotipy, openai, json
import argparse
from dotenv import dotenv_values

config = dotenv_values(".env")
openai.api_key = config["OPEN_API_KEY"]

def get_playlist(prompt, count=8):
    example_json = """[
    {"song": "Everybody Hurts", "artist": "R.E.M."},
    {"song": "Hurt", "artist": "Johnny Cash"},
    {"song": "Nothing Compares 2 U", "artist": "Sinead O'Connor"},
    {"song": "Yesterday", "artist": "The Beatles"},
    {"song": "All Too Well", "artist": "Taylor Swift"},
    {"song": "Someone Like You", "artist": "Adele"},
    {"song": "My Heart Will Go On", "artist": "Celine Dion"},
    {"song": "Tears in Heaven", "artist": "Eric Clapton"},
    {"song": "The Sound of Silence", "artist": "Simon & Garfunkel"},
    {"song": "Goodbye My Lover", "artist": "James Blunt"}
    ]"""

    # Prompt
    messages = [
        {"role": "system", "content": """
        You are a helpful playlist generating assistant. You should
        generate a list of songs and their artists according to a text prompt
        You should only return a JSON array, where each element follows this format:
        {"song": <song_title>, "artist": <artist_name>}
        """},
        {"role":"user", "content":"Generate a playlist of 10 songs based on this prompt: super super sad songs"},
        {"role":"assistant", "content": example_json},
        {"role":"user", "content":f"Generate a playlist of {count} songs based on this prompt: {prompt}"}

    ]
    
    # Model
    reply = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = messages,
        max_tokens = 400
    )
    
    playlist = json.loads(reply["choices"][0]["message"]["content"])
    
    return playlist


def login_spotify():
    spot = spotipy.Spotify(
        auth_manager = spotipy.SpotifyOAuth(
            client_id = config["SPOTIFY_CLIENT_ID"],
            client_secret =config["SPOTIFY_CLIENT_SECRET"],
            redirect_uri = "http://localhost:9999",
            scope="playlist-modify-private"
        )
    )

    return spot
    



def main():
    # Argument Parser
    parser = argparse.ArgumentParser(description="Simple CL song utility")
    parser.add_argument("-p", type=str, default="GPT Playlist", help="Prompt to describe playlist")
    parser.add_argument("-n", type=int, default=8, help="Number of songs to add to playlist")
    parser.add_argument("-t", type=str, default="GPT Playlist", help="Title of Spotify Playlist")

    args = parser.parse_args()

    if args.n not in range(1,50):
        raise ValueError("Error: n should be between 0 and 50")


    # Login into Spotify
    spot = login_spotify()

    user = spot.current_user()
    assert user is not None

    # Generate playlist
    gen_playlist = get_playlist(args.p, args.n)

    track_id = []

    # Append each song ID to the track arr
    for item in gen_playlist:
        artist, song = item["artist"], item["song"]
        query = f"{song} {artist}"
        search_results = spot.search(q=query, type="track", limit=5)
        tracks = search_results["tracks"]["items"][0]["id"]
        track_id.append(tracks)


    # Create a new playlist with generated tracks
    playlist = spot.user_playlist_create(
        user["id"],
        public = False,
        name = args.t
    )

    # Add playlist to Spotify
    spot.user_playlist_add_tracks(user["id"], playlist["id"], track_id)

    print("\n")
    print(f"Created playlist: {playlist['name']}")
    print(playlist["external_urls"]["spotify"])


if __name__ == "__main__":
    main()