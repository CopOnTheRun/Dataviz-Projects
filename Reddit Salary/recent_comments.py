from typing import Any
from praw import Reddit
import datetime as dt
from reddit_salary import get_config


def get_recent_users(subreddit, num = 100):
    """Grabs num most recent users from a subreddit and returns their username and flair as a dict."""
    users = {}

    for submission in subreddit.new(limit = None):
        print(submission.title)
        submission.comments.replace_more(limit=None)

        flair = submission.author_flair_text
        users[submission.author] = flair if flair else ""

        for comment in submission.comments.list():
            if len(users) >= num:
                return users
            #deleted users won't show up as author
            if author := comment.author:
                flair = comment.author_flair_text
                users[comment.author] = flair if flair else ""
                print(author,users[author])
                print(len(users))

    return users


def write_users_to_file(users,filename):
    """Given a dict of users and a filename, write user infor to the file as a csv."""
    with open(filename,"w") as f:
        print("author,flair,verified,comment karma,link karma,duration",file=f)
        for author,flair in users.items():
            try:
                verified = author.has_verified_email
                comment_karma = author.comment_karma
                link_karma = author.link_karma
                duration = (dt.datetime.now() - dt.datetime.utcfromtimestamp(author.created_utc)).days
                print(author,flair,verified,comment_karma,link_karma,duration,sep=",",file=f)
                print(author,flair,verified,comment_karma,link_karma,duration,sep=",")
            #don't feel like doing anything fancy with the exceptions
            except Exception as e:
                print(e)


def main():

    config_dict = get_config("config.ini")
    reddit = Reddit(**config_dict)
    subreddit = reddit.subreddit("rva")
    users = get_recent_users(subreddit, 500)
    file_string = f"New_Comments_{subreddit}.csv"
    write_users_to_file(users,file_string)


if __name__ == "__main__":
    main()
