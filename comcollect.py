"""
Allows you to gauge how a given community comparatively ranks a subset of shows. Provided is how r/Gundam ranks every
Gundam comparatively.
Collects usernames from comments on posts in a given community, searches through their comments to find a comment in
r/anime and checks for a flair linking to either MAL or Anilist. Pulls their profile and checks for their scoring of a
provided set of shows.
The scores for each provided show are compared to each other within each profile through a difference matrix and mapped
to a list with the shows keys. The matching keys from each account (ie. all accounts who scored both x,y; x,z; etc.) are
averaged. Finally the averages of each show starting with a specific id are averaged (ie. xy and xz are averaged but not
yz, yz, zx, or zy). These results are ranked highest to lowest for a comparative score. A direct ranking is also given.
Also provided are methods for 2 other types of comparisons. One averages the comparative score for each show within
itself and then each show score is averaged at the end (ie. Account 1 scores x, y, z and account 2 scores x, z. The
final score for x is the comparative mean of xy, xz from account 1 and xz from account 2). Last is a direct compare
which takes the score of each show and averages it with the score of that show from all other accounts.
"""
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import praw
from prawcore.exceptions import Forbidden
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import time

# ------------ Parameters ------------
# Initializes PRAW with the settings in praw.ini
# YOU MUST MAKE YOUR OWN REDDIT APP INSTANCE TO USE THIS
# It's easy here's a guide https://towardsdatascience.com/how-to-use-the-reddit-api-in-python-5e05ddfd1e5c
# Just follow the steps until you get the client id and secret and copy those into the appropriate field in praw.ini
reddit = praw.Reddit("account")

# Select the community to draw your comments from, this is the community you are making a comparison within
subreddit = reddit.subreddit('gundam')

# The type of comparison you wish to perform. Type 0 is direct score comparison, Type 1 compares scores within an
# account and averages the show scores after. Type 2 compares scores across all accounts and averages the paired
# show scores after. Type 0 is just for basic reference. Type 1 will perform quicker and is a pretty standard form
# of comparison. I prefer Type 2 but it will not do well with very large sample sizes.
compare_type = 0

# A list of the IDs for each show in question. MAL and Anilist often have the same IDs but not always, these IDs are
# for every Gundam currently out that isn't a recap, etc. Probably. If you replace these with other make sure that the
# IDs are in the same order.
mal_ids = [80, 85, 8839, 86, 87, 82, 84, 2695, 81, 17717, 1917, 1916, 4232, 31973, 34391, 23943, 6336, 35224, 37764,
           37765, 10937, 88, 89, 23259, 31454, 96, 90, 2273, 92, 95, 93, 2298, 94, 1215, 1241, 2581, 3927, 6288, 10808,
           17655, 19319, 35982, 24625, 30533, 35567, 37247, 37245, 40192, 40942, 44050, 31251, 33051, 52168, 49828,
           7060, 41063, 49211]
anilist_ids = [80, 85, 8839, 86, 87, 82, 84, 2695, 81, 17717, 1917, 1916, 4232, 21458, 97853, 20707, 6336, 98504,
               101554, 105595, 10937, 88, 89, 20658, 102525, 96, 90, 2273, 92, 95, 93, 2298, 94, 1215, 1241, 2581, 3927,
               6288, 10808, 17655, 19319, 99732, 20739, 21814, 99731, 102622, 101036, 110786, 114233, 126662, 21268,
               21749, 146922, 139274, 7060, 114841, 135645]

# ---------- Parameters End ----------

start_time = time.time()
print('--- time ---')

user_list = []
flair_list = []

# Selects the top x posts in
for submission in subreddit.top(limit=1):
    # Selects how far down the comments section you will go, select None to get all of them
    submission.comments.replace_more(limit=2)
    # Iterates through each comment and its replies, checks if the user is existing, and records the name in a list
    for comment in submission.comments.list():
        if comment.author:
            user_list.append(comment.author.name)
# Removes duplicate accounts in the list
user_list = [*set(user_list)]
print('Number of users found:', len(user_list))

# Iterates through each user in the list and reads their comments
for user in user_list:
    try:
        # Select how many comments back to read, None for all of them
        for comment in reddit.redditor(user).comments.new(limit=10):
            if comment.subreddit == 'Anime':
                if comment.author_flair_text is not None:
                    if "anilist" in comment.author_flair_text or 'myanimelist' in comment.author_flair_text:
                        # Restructures the flair because there are several ways that it is displayed
                        flair = comment.author_flair_text.split(':')[-1:][0]
                        if '//' in flair:
                            flair = flair.split('//')[-1:][0]
                        flair = 'https://' + flair
                        # Selects only the completed section for a more fair comparison
                        if 'anilist' in flair:
                            flair = flair + '/animelist/Completed'
                        if 'myanimelist' in flair:
                            flair.replace('profile', 'animelist')
                            flair = flair + '?status=2'
                        flair_list.append(flair)
                        break
    except Forbidden:
        print("403 error on user", user, ": suspended")
print('Users with usable flairs:', len(flair_list))

# Creates a tuple of each ID pair for easier comparison later
new_ids = list(map(lambda x, y: [x, y], mal_ids, anilist_ids))

# Initializes the various dataframes needed for processing
df = pd.DataFrame(columns=['Title', 'ID', 'Score'])
score_df = pd.DataFrame(columns=['ID', 'Score'])
out_df = pd.DataFrame(columns=['ID', 'Score'])
final_df = pd.DataFrame(columns=['ID', 'Score'])

# Iterates through each flair in the list to pull the relevant scores from either website
for i in flair_list:
    # Loading each page, both Anilist and MAL (sometimes) utilize dynamic webpages, this opens the webpage and scrolls
    # to the bottom to ensure that all of the scoring data is read
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)
    driver.get(i)
    time.sleep(3)
    previous_height = driver.execute_script('return document.body.scrollHeight')
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        if 'anilist' in i:
            time.sleep(.15)
        if 'myanimelist' in i:
            time.sleep(2)
        new_height = driver.execute_script('return document.body.scrollHeight')
        if new_height == previous_height:
            break
        previous_height = new_height
    # Protocol for Anilist
    if 'anilist' in i:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = soup.select('.entry.row')
        for result in results:
            title = result.select_one('.title').get_text(strip=True)
            link_ref = result.select_one('a', href=True)
            link_ref = int(str(link_ref).split('/')[2])
            # Maps the ID into the combined ID tuple
            link_ref = [item for item in new_ids if link_ref in item]
            if link_ref:
                link_ref = link_ref[0]
            else:
                continue
            score = float(result.select_one('.score').get_text(strip=True))
            if score:
                # Adds all relevant scores to a df
                if link_ref in new_ids:
                    concat_df = pd.DataFrame({'Title': [title], 'ID': [link_ref], 'Score': [score]})
                    df = pd.concat([df, concat_df], ignore_index=True)
    # Protocol for MAL
    if 'myanimelist' in i:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # Type 1 MAL profile, because MAL insists on personalized user profiles with differing tags.
        if soup.select('.list-block'):
            results = soup.select('.list-item')
            for result in results:
                title_link = result.select_one('.data.title.clearfix').select_one('.link.sort')
                title = str(title_link).split('>', 1)[1].split('<')[0]
                link_ref = int(str(title_link).split('/')[2])
                # Maps the ID into the combined ID tuple
                link_ref = [item for item in new_ids if link_ref in item]
                if link_ref:
                    link_ref = link_ref[0]
                else:
                    continue
                # Filters out completed shows with no score
                try:
                    score = float(result.select_one('.score-label').get_text(strip=True))
                except ValueError:
                    continue
                # Adds all relevant scores to a df
                if link_ref in new_ids:
                    concat_df = pd.DataFrame({'Title': [title], 'ID': [link_ref], 'Score': [score]})
                    df = pd.concat([df, concat_df], ignore_index=True)
        # Type 2 MAL profile. These are the main two I came across, there's probably others that aren't included now
        else:
            results = soup.select('table')
            for result in results:
                if result.select_one('.animetitle') is not None and result.select_one('.List_LightBox') is not None \
                        and result.select_one('.score-label') is not None:
                    title = result.select_one('.animetitle').get_text(strip=True)
                    link_ref = result.select_one('.List_LightBox')
                    link_ref = int(str(link_ref).split("&", 1)[0].split('=')[3])
                    # Maps the ID into the combined ID tuple
                    link_ref = [item for item in new_ids if link_ref in item]
                    if link_ref:
                        link_ref = link_ref[0]
                    else:
                        continue
                    # Filters out completed shows with no score
                    try:
                        score = float(result.select_one('.score-label').get_text(strip=True))
                    except ValueError:
                        continue
                    # Adds all relevant scores to a df
                    if link_ref in new_ids:
                        concat_df = pd.DataFrame({'Title': [title], 'ID': [link_ref[0]], 'Score': [score]})
                        df = pd.concat([df, concat_df], ignore_index=True)

    # Puts the scores for each ID into a difference matrix to measure their comparative scores against each other
    A = np.array(df.Score)
    B = np.array(df.Score)
    diff = np.subtract.outer(A, B)

    # Positional Iterators
    ocount = 0
    dcount = 0

    # Iterates though the matrix and populates score_df with the double ID and score difference
    for i in diff:
        for j in i:
            if df.ID[ocount] == df.ID[dcount]:
                ocount += 1
                continue
            concat_df = pd.DataFrame({'ID': [[df.ID[ocount]] + [df.ID[dcount]]], 'Score': j})
            score_df = pd.concat([score_df, concat_df], ignore_index=True)
            ocount += 1
        ocount = 0
        dcount += 1

    sub_list = []
    # Type 0 compare:
    # Direct compare, averages the score of each show. Here only concat score_df to a df outside the loops for later
    # processing.
    if compare_type == 0:
        for i in df.index:
            df.ID[i] = tuple(df.ID[i])
        out_df = pd.concat([out_df, df], ignore_index=True)
        df = df.iloc[0:0]
        score_df = score_df.iloc[0:0]

    # Type 1 compare:
    # Iterates through the earlier dataframe, comparing each ID tuple with the double ones from score_df, averages
    # the values in each profile.
    if compare_type == 1:
        for i in df.index:
            for j in score_df.index:
                # Subtractive compare
                if df.ID[i][0] in score_df.ID[j][1]:
                    sub_list.append([tuple(df.ID[i]), score_df.Score[j]])
        sub_df = pd.DataFrame(data=sub_list, columns=['ID', 'Score'])
        concat_df = sub_df.groupby(['ID'], as_index=False).mean()
        final_df = pd.concat([final_df, concat_df], ignore_index=True)
        df = df.iloc[0:0]
        score_df = score_df.iloc[0:0]

    # Type 2 compare:
    # Iterates through the earlier dataframe, comparing each ID tuple with the double ones from score_df, averages
    # the values across each show. Here only concat score_df to a df outside the loops for later processing.
    if compare_type == 2:
        out_df = pd.concat([out_df, score_df], ignore_index=True)
        df = df.iloc[0:0]
        score_df = score_df.iloc[0:0]

# Continuation of Type 0 compare, does the averaging by show here.
if compare_type == 0:
    final_df = out_df.drop(['Title'], axis=1).groupby(['ID'], as_index=False).mean()

# Continuation of Type 2 compare, does the averaging by show here.
sub_list = []
if compare_type == 2:
    for i in enumerate(new_ids):
        for j in out_df.index:
            if i[1] == out_df.ID[j][1]:
                sub_list.append([tuple(i[1]), out_df.Score[j]])
    sub_df = pd.DataFrame(data=sub_list, columns=['ID', 'Score'])
    concat_df = sub_df.groupby(['ID'], as_index=False).mean()
    final_df = pd.concat([final_df, concat_df], ignore_index=True)

# Averages the results of each profile and outputs the final result.
final_df = final_df.groupby(['ID'], as_index=False).mean()
final_df = final_df.sort_values('Score', ignore_index=True, ascending=False)
print(final_df)
# Saves results as csv and pk1 for future reference
final_df.to_csv('results.csv', index=False)
final_df.to_pickle('results.pk1', index=False)
print('--- %s seconds ---' % (time.time() - start_time))
