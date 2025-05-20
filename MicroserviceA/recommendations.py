import zmq
import json
import pandas as pd

# Load preprocessed movie data
print("Loading preprocessed movie data...")
movie_data = pd.read_csv('processed_movie_data.csv')
print(f"Loaded {len(movie_data)} movies into memory.")

# Initialize ZeroMQ context and sockets
context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind("tcp://*:5555")

sender = context.socket(zmq.PUSH)
sender.connect("tcp://localhost:5556")

print("Microservice A is running and waiting for requests...")

def get_recommendations(history, genres):
    # Filter out movies that the user has already seen
    filtered_data = movie_data[~movie_data['primaryTitle'].isin(history)]

    # Further filter by genres if specified
    if genres:
        genre_query = '|'.join(genres)
        filtered_data = filtered_data[filtered_data['genres'].str.contains(genre_query, na=False)]

    # Compute the "popularity score" as the product of rating and number of votes
    filtered_data['popularity_score'] = filtered_data['averageRating'] * filtered_data['numVotes']

    # Sort by the new score in descending order
    filtered_data.sort_values(by='popularity_score', ascending=False, inplace=True)

    # Select the top 10 recommendations
    recommendations = filtered_data.head(10)
    
    # Create response format
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

while True:
    try:
        # Receive the request
        message = receiver.recv_json()
        print(f"Received request: {message}")
        user_id = message.get("user_id")
        history = message.get("history", [])
        genres = message.get("preferred_genres", [])

        if not history and not genres:
            # Completely empty data: return popular recommendations
            response = {
                "user_id": user_id,
                "recommendations": get_recommendations([], [])
            }
        else:
            # Personalized recommendations based on history and genre
            response = {
                "user_id": user_id,
                "recommendations": get_recommendations(history, genres)
            }

            
        # Send the response back
        sender.send_json(response)
        print(f"Sent response: {response}")

    except Exception as e:
        print(f"Error: {e}")
        error_response = {"error": "Invalid Request"}
        sender.send_json(error_response)
    except KeyboardInterrupt:
        print("Exited by user.")
        break
