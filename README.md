# comparitive-anirank
Pulls a sample of rankings from an online community and uses those scores to comparitively rank shows within that community.

About
----

comparitive-anirank is a scraping and analyizing program that takes the a sample of users from a selected subreddit, detects if they have a ranking flair on the r/anime subreddit, and uses that flair to compare their rankings of certain anime.

comparitive-anirank utilizes the PRAW API wrapper for accessing Reddits API and will require an individual Reddit instance to be set up if you wish to run it yourself.

Instructions
----

comparitive-anirank requires a Python installation and the following packages:
  * BeautiulSoup 
  * numpy
  * pandas
  * praw
  * selenium
  * time

Instructions for setting up a Python environment on Windows can be found [here](https://docs.python.org/3/using/windows.html)

BeautifulSoup is utilized for parsing the html of both Anilist and MAL, selenium is included to access the dynamic elements of each website.

You must make your own Reddit app instances and update the "cliend-id" and "client-secret" fields in the praw.ini file to use this.
Instructions to do so can be found [here](https://towardsdatascience.com/how-to-use-the-reddit-api-in-python-5e05ddfd1e5c)

There are several user-defined parameters at the top of the code for you to change based on yur own preferences.

* subreddit_name: determines the subreddit you are pulling users from, this is the subreddit you will be comparing scores with. The sample given is for the gundam subreddit, the provided code will compare scores for anime among the gundam community.
* compare_type: determines the type of comparison you want to perform. Type 0 is a direct comparison, this simply takes the scores for each show and averages them. Type 1 is a common comparitive technique which compares the score of each relevant show within each user and creates a show score from each comparitive score containing a certain show. This score is averaged with scores for the same show at the end. Type 2 is a more in depth and more computationally intensive method which I prefer, it holds the comparitive score for each show pairing until the end and then averages each pairing and then each show.
* post_limit: PRAW searches through the comments of top posts to get usernames. This determines how many posts praw will sort through for comments.
* post_comment_limit: Determines how far down the comments praw will search, each 1 is equivalent to a 'see more comments' click. Select None to get all of them.
* user_comment_limit: Determines how many comments back praw will search within a user profile to find an r/anime comment for their flair. Select None to go back 1000, which is the limit of the API.
* mal-ids, anilist_ids: Contains an array of the show IDs you are interested in comparing, provided are the MAL and Anilist IDs for every-ish Gundam show/movie. Switch these out for the shows you're interested in comparing and MAKE SURE the order is the same for both the MAL and Anilist IDs.

Once your parameters are set let the code run, it will be quicker or slower depending on your internet and the API load at any given moment.
At the end you will receive a print out and a .csv and .pk1 file containing the show ID pairs and their sorted rankings, highest being at the top.
