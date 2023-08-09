import re
import datetime as dt
import pandas as pd

from praw import Reddit, models
from configparser import ConfigParser

def get_config(filename: str) -> dict[str,str]:
    """Gets the configuration for praw from the config file passed. Returns config as a dict."""
    config: ConfigParser = ConfigParser()
    config.read(filename)

    config_dict: dict[str,str] = {}

    config_dict["client_id"] = config.get('reddit', 'client_id')
    config_dict["client_secret"] = config.get('reddit', 'client_secret')
    config_dict["user_agent"] = config.get('reddit', 'user_agent')

    return config_dict

def scraping_reddit(reddit: Reddit, url: str) -> list[list[str|float|None]]:
    """Creates and returns a list of list of reddit users, in a certain thread. Extracts salary if detected"""
    submission: models.Submission = reddit.submission(url=url)
    submission.comments.replace_more(limit=None)

    lol: list[list[str|float|None]] = [["Author","Verified","Comment Karma","Link Karma","Flair","Years on Reddit","Comment Score","Salary","Comment"]]
    for comment in submission.comments:
        author = comment.author
        if author:
            try:
                #this block is very slow
                verified = author.has_verified_email
                comment_karma = author.comment_karma
                link_karma = author.link_karma
                flair = comment.author_flair_text if comment.author_flair_text else ""
                duration = (dt.datetime.now() - dt.datetime.utcfromtimestamp(author.created_utc)).days
                years = float(duration)/365
                score = comment.score
                text = comment.body
                salary = extract_salary(text)
                lol.append([author,verified,comment_karma,link_karma,flair,years,score,salary,text])
            #some comments have accounts that get suspended which results in a Redditor instance with no attributes except the name. Despite the docs saying there's an "is_suspended" attribute.
            except AttributeError as e:
                print(e)
    return lol

def extract_salary(comment: str) -> float | None:
    """A function the tries its darn best to extract salary from a comment. Returns the found salary as a float, or returns None if it doesn't detect a salary."""
    # I am so sorry
    salary_regex = r'(?:(?<!\S)|-)~?\$?(?:(?:\d{1,3}(?:,\d{3}){1,2})(?!,)|(?!401[kK])\d{1,3}(?:\.\d)?[Kk])\b'
    hourly_regex = r'(?<!\S)\$?(\d{2}(?:\.\d{2})?)(?![kK,%])\b'
    print(comment)

    #default is to match salary if found, and then fallback to hourly
    if match := re.findall(salary_regex, comment):
        print("Salary found")
        return max(salary_to_number(m) for m in match)
    elif match := re.findall(hourly_regex, comment):
        print("Hourly found")
        hourly = max(salary_to_number(m) for m in match)
        return hourly*40*50 #convert to annual 40hr/wk, 50 work wk/yr
    else:
        print("No salary information found")
        return None

def salary_to_number(salary: str) -> float:
    """Converts a salary string to a float"""
    salary = salary.casefold().lstrip(" $~-").replace(",","")
    if "k" in salary:
        salary = float(salary.rstrip("k"))*1000
    return float(salary)

def main() -> None:
    """Runs program, and saves data as a csv."""
    config_dict = get_config("config.ini")

    url = "https://www.reddit.com/r/rva/comments/11lvneq/rva_salary_transparency_thread/"
    reddit: Reddit = Reddit(**config_dict)

    comment_list = scraping_reddit(reddit,url)

    df = pd.DataFrame(comment_list[1:],columns=comment_list[0])
    df.to_csv("Reddit Salary.csv")

if __name__ == "__main__":
    main()
