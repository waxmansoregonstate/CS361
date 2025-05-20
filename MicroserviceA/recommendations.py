import zmq
import json
import pandas as pd

print("Loading preprocessed movie data...")
movie_data = pd.read_csv('processed_movie_data.csv')
print(f"Loaded {len(movie_data)} movies into memory.")

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind("tcp://*:5555")

sender = context.socket(zmq.PUSH)
sender.connect("tcp://localhost:5556")

print("Microservice A is running and waiting for requests...")

def get_recommendations(history, genres):
    filtered_data = movie_data[~movie_data['primaryTitle'].isin(history)]

    if genres:
        genre_query = '|'.join(genres)
        filtered_data = filtered_data[filtered_data['genres'].str.contains(genre_query, na=False)]

    filtered_data['popularity_score'] = filtered_data['averageRating']**3 * filtered_data['numVotes']

    filtered_data.sort_values(by='popularity_score', ascending=False, inplace=True)

    recommendations = filtered_data.head(10)
    
    response = [
        {
            "title": row['primaryTitle'],
            "score": row['averageRating'],
            "votes": row['numVotes'],
            "popularity_score": row['popularity_score'],
            "year": row['startYear'],
            "genres": row['genres']
        }
        for _, row in recommendations.iterrows()
    ]

    return response

poller = zmq.Poller()
poller.register(receiver, zmq.POLLIN)

while True:
    try:
        # Poll for incoming messages for 1000ms (1 second)
        events = dict(poller.poll(1000))
        
        # Check if the receiver has data ready
        if receiver in events:
            message = receiver.recv_json()
            print(f"Received request: {message}")
            
            user_id = message.get("user_id")
            history = message.get("history", [])
            genres = message.get("preferred_genres", [])

            if not history and not genres:
                response = {
                    "user_id": user_id,
                    "recommendations": get_recommendations([], [])
                }
            else:
                response = {
                    "user_id": user_id,
                    "recommendations": get_recommendations(history, genres)
                }

            sender.send_json(response)

    except KeyboardInterrupt:
        print("\nExiting microservice...")
        break
    except Exception as e:
        print(f"Error: {e}")
        error_response = {"error": "Invalid Request"}
        sender.send_json(error_response)

