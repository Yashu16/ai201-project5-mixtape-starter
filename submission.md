**Notes**
1. *feed_service file*: It has two functions. Both of them search for users and their friends. Returns Value_Error if user is not found, and returns [] if user has no friends. Also, imports user, song and Listening event from models file.
- First function identifies the music user's friends are listening right now and their recent ones, with a time limit of last 24hrs. And it only returns their most recent song. 
- Second function identifies the music listened by the user's friends and returns all songs regardless of how old the date says they are, upto a certain limit.  

2. *notification_service file*: This one has five functions. 
- First one is basic create_notification, which adds and commits said notification to database. 
- Next, it's add_to_playlist, it imports playlist from models file and those playlist songs from playlist_service file. Once it made sure the user, songs and playlist exist in the db, it adds the song to playlist if said song doesn't already exist. And, it notifies the user who shared the song, however, if the user themselves adds it, they don't get a notification. 
- Third one is rate_song, which first checks if score is 1-5, and if said user and song exist in db. If the user has already rated the song before, it will overwrite it in db. Otherwise, the song gets a rating. Then returns the rating without triggering any notification. This is a **bug**.
- Fourth one is get_notification, which fetches a user's notification list. But if user only want unread ones, it returns only them based on said parameter value being true. It returns these notification in the order from most recent to old. 
- Last is mark_as_read, which dismisses a notification if user marks it as true. It does by looking at notification ID, and flipping read flag to True, and saves it in db. If there's no notification, it returns ValueError. 

3. *playlist_service file*: There are Four functions in this file. 
- First function - create_playlist - identifies if a user exists in db and then builds a new playlist (imported from models file), and by default it assumes collaboration with friends is true.
- Second Function - get_playlist_songs - returns songs in the order they were added in a playlist. It first confirms the playlist exist, and queries playlist_entries table to get songs in order. However, it says [songs[:-1]] in return statement, which means the last song is never returned. This is a **bug**. 
- Third function - get_playlist - returns the metadata of the playlist without songs. 
- Fourth function - get_user_playlists - returns all playlists created by an user.
4. *search_service file*: This one has two functions. 
- search_songs - it finds songs by title or artist. 
- get_song - fetches one song by ID. If said song is not in db, it returns ValueError. 
5. *streak_service file*: It has three functions. 
- record_listening_event - once it confirms the user exist in db, it creates a new listening event row with current timestamp. calls it's second function to update streak. 
- update_listening_streak - updates streak based on certain rules given in docstring. 
- get_streak - returns the streak after checking the user exists in db. 

**Data flow**
Let's see how data flows when a user rates a song. 
- First the client sends an API POST request when they rate it. The API request will have user_id and score they give. 
- Next, rate function from routes/songs gets called, which will parse JSON body from previous API into python dict, and will return 400 error if user_id or the score is missing. Otherwise, calls rate_song from notification_service file. 
- The score gets converted from string to int.
- rate_song function first checks if a score already exists in the database, and if it does, it overwrites them. 
- rate_song function will call try/except ValueError - if try works, it returns the Rating object without triggering any notification, otherwise, returns a 400 response with error.
- The Rating class in models.py file uses UniqueConstraint in the table to guarantee there's only one rating per song. It converts id, user_id, song_id, score and rated_at into a dictionary.
- That rating.to_dict is returned by the route and then to the client gets a JSON body.  

**pattern noticed** - Services raise ValueError for "expected" failures, and routes translate that into HTTP status codes. 
