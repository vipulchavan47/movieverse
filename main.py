import streamlit as st
import pickle
import pandas as pd
import requests
import random
import concurrent.futures


similarity = pickle.load(open('similarity.pkl', 'rb'))
movie_dict = pickle.load(open('movie_list.pkl', 'rb'))
movies = pd.DataFrame(movie_dict)


api_key = '33c991d576fd12fa87e5d311251fc47c'

# ========== API CALLS ==========

@st.cache_data(show_spinner=False)
def fetch_movie_details(movie_title):
    try:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_title}"
        response = requests.get(search_url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data['results']:
            movie_data = data['results'][0]
            movie_id = movie_data['id']
            poster_path = movie_data.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            release_date = movie_data.get('release_date', 'N/A')
            rating = movie_data.get('vote_average', 'N/A')
            overview = movie_data.get('overview', 'No overview available.')

            director = fetch_director(movie_id)
            trailer_url = fetch_trailer(movie_id)
            imdb_id = fetch_imdb_id(movie_id)
            imdb_link = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else None

            return poster_url, release_date, rating, overview, director, trailer_url, imdb_link

    except (requests.exceptions.RequestException, ValueError):
        pass

    return None, "N/A", "N/A", "No data", "Unknown", None, None


@st.cache_data(show_spinner=False)
def fetch_director(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        for crew in data.get('crew', []):
            if crew['job'] == "Director":
                return crew['name']
    except:
        pass
    return "Unknown"


@st.cache_data(show_spinner=False)
def fetch_trailer(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        for video in data.get('results', []):
            if video['type'] == "Trailer":
                return f"https://www.youtube.com/watch?v={video['key']}"
    except:
        pass
    return None


@st.cache_data(show_spinner=False)
def fetch_imdb_id(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('imdb_id')
    except:
        return None

# ========== RECOMMENDER SYSTEM ==========

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = [movies.iloc[i[0]].title for i in movie_list]

    movie_details = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(fetch_movie_details, recommended_movies)
        for title, details in zip(recommended_movies, results):
            movie_details.append((title, *details))

    return recommended_movies, movie_details


def feeling_lucky():
    return random.choice(movies['title'].values)


# ========== STREAMLIT UI ==========

st.set_page_config(page_title="🎬 Movie Recommender Ultimate", layout="wide")
st.title('🍿 MovieVerse:')

mood = st.sidebar.selectbox("🎯 Select your mood:", ["Adventure", "Happy", "Thrilling", "Romantic", "Random"])
st.sidebar.markdown("✨ Feeling indecisive? Hit 'Feeling Lucky'!")

selected_movie_name = st.selectbox(
    "🎥 Choose a movie to get recommendations:",
    movies['title'].values
)

if st.sidebar.button("Feeling Lucky"):
    selected_movie_name = feeling_lucky()
    st.sidebar.success(f"🎉 You're watching: {selected_movie_name}")

if st.button('🚀 Recommend'):
    with st.spinner("Fetching recommendations..."):
        recommendations, movie_details = recommend(selected_movie_name)

    st.subheader("✨ Your Top 5 Recommended Movies:")
    if movie_details:
        cols = st.columns(5)
        for idx, (movie, poster_url, date, rating, overview, director, trailer_url, imdb_link) in enumerate(movie_details):
            with cols[idx]:
                if poster_url:
                    st.image(poster_url, caption=f"📅 {date} | ⭐ {rating}")
                st.markdown(f"🎬 {movie}")
                st.caption(f"🎥 Directed by: {director}")
                st.write(f"📖 {overview}")

                if trailer_url:
                    st.markdown(
                        f'<a href="{trailer_url}" target="_blank"><button style="background-color:#FF4B4B; color:white; padding:5px 10px; border-radius:5px; border:none; cursor:pointer;">🎬 Watch Trailer</button></a>',
                        unsafe_allow_html=True,
                    )

                if imdb_link:
                    st.markdown(
                        f'<a href="{imdb_link}" target="_blank"><button style="background-color:#f5c518; color:black; padding:5px 10px; border-radius:5px; border:none; cursor:pointer;">🍿 View on IMDB</button></a>',
                        unsafe_allow_html=True,
                    )
    else:
        st.warning("No recommendations found. Try another movie!")

st.markdown(
    "<hr style='border:1px solid #f0f0f0'><p style='text-align:center;'>🔥 Pick Your Mood — We'll Find the Movie.</p>",
    unsafe_allow_html=True
)
