try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import os
from fastapi.openapi.models import Response
import praw
from praw.reddit import Subreddit
from praw.exceptions import RedditAPIException
from sqlalchemy import true
from starlette import responses
from datetime import datetime, timedelta
import json

from sql_app import crud, models, schemas


class Server:
    def __init__(self):
        self.conf = self.get_config()
        self.reddit = self.load_reddit_instans()
        self.cashTime = {"days": 1}

    def get_config(self):
        config = ConfigParser.ConfigParser()
        config.read([os.path.expanduser(".config/reddit/config.cfg")])

        conf = dict(config.items("reddit"))
        print(f"client_id: {conf.get('client_id')}")
        print(f"client_secret: {conf.get('client_secret')}")
        print(f"user_agent: {conf.get('user_agent')}")
        return conf

    def load_reddit_instans(self):
        conf = self.conf
        reddit = praw.Reddit(
            client_id=conf.get("client_id"),
            client_secret=conf.get("client_secret"),
            redirect_uri="http://localhost:8080/",
            user_agent=conf.get("user_agent"),
        )
        return reddit

    def get_link_to_auth(self):
        # print()
        return self.reddit.auth.url(
            [
                "*",
                # "read",
                # "identity",
                # "subscribe",
                # "vote",
                # "save",
                # "privatemessages",
                # "edit",
                # "history",
            ],
            "reddit-farm",
            "permanent",
        )

    def get_user_data(self, code):
        print("code:", code)
        conf = self.conf
        reddit = praw.Reddit(
            client_id=conf.get("client_id"),
            client_secret=conf.get("client_secret"),
            redirect_uri="http://localhost:8000/",
            user_agent=conf.get("user_agent"),
        )
        print("before refresh_token")
        reddit.validate_on_submit = True
        refresh_token = reddit.auth.authorize(code)
        print("refresh_token", refresh_token)
        username = reddit.user.me()
        print("username", username)
        return {"refresh_token": refresh_token, "username": username.name}

    def get_user_posts(self, refresh_token):
        print("refresh_token", refresh_token)
        reddit = praw.Reddit(
            client_id=self.conf.get("client_id"),
            client_secret=self.conf.get("client_secret"),
            refresh_token=refresh_token,
            user_agent=self.conf.get("user_agent"),
        )
        user = reddit.user.me()
        redditor = reddit.redditor(user.name)
        print("redditor", redditor)
        submissions = redditor.submissions.new(limit=100)
        posts = []
        for submission in submissions:
            posts.append(
                {
                    "title": submission.title,
                    "score": submission.score,
                    "subreddit": str(submission.subreddit),
                    "selftext": str(submission.selftext),
                    "url": submission.url,
                }
            )
        return posts

    def get_users_subsreddits(self, refresh_token):
        reddit = praw.Reddit(
            client_id=self.conf.get("client_id"),
            client_secret=self.conf.get("client_secret"),
            refresh_token=refresh_token,
            user_agent=self.conf.get("user_agent"),
        )
        print("read_only: " + str(reddit.read_only))
        print("active account: " + str(reddit.user.me()))
        print("scopes: ", reddit.auth.scopes())
        subredditsRaw = reddit.user.subreddits(limit=None)

        print(subredditsRaw)
        subreddits = []
        for subreddit in subredditsRaw:
            print("subredditsRaw item:", str(subreddit))
            sub = str(subreddit)
            if sub.find("u_") != 0:
                print("add item.")
                subreddits.append(str(subreddit))
        return subreddits

    def get_subsreddit_info(self, refresh_token, name):
        reddit = praw.Reddit(
            client_id=self.conf.get("client_id"),
            client_secret=self.conf.get("client_secret"),
            refresh_token=refresh_token,
            user_agent=self.conf.get("user_agent"),
        )
        print("subreddit name: ", name)
        subreddit = reddit.subreddit(name)
        print("subreddit: ", subreddit)
        rules = subreddit.rules
        print("subreddit.rules: ", rules)
        newRules = []
        for rule in rules:
            print("rule", rule)
            newRules.append(
                {"name": rule.short_name, "description": rule.description, }
            )

        flairs = reddit.post(
            "r/" + name + "/api/flairselector/", data={"is_newlink": True}
        )["choices"]

        response = {
            "flairs": flairs,
            "rules": newRules,
        }
        return response

    # def get_subsreddits_info(self, refresh_token, subsList, cashed=False):
    #     reddit = praw.Reddit(
    #         client_id=self.conf.get("client_id"),
    #         client_secret=self.conf.get("client_secret"),
    #         refresh_token=refresh_token,
    #         user_agent=self.conf.get("user_agent"),
    #     )
    #     print(subsList)
    #     subreddits = []
    #     for sub in subsList:
    #         print("subreddit", sub)
    #         subreddit = reddit.subreddit(sub)
    #         newRules = []
    #         for rule in subreddit.rules:
    #             # print("rule", rule)
    #             newRules.append(
    #                 {"name": rule.short_name, "description": rule.description,}
    #             )
    #         flairs = reddit.post(
    #             "r/" + sub + "/api/flairselector/", data={"is_newlink": True}
    #         )["choices"]
    #         newItem = {
    #             "name": sub,
    #             "flairs": flairs,
    #             "rules": newRules,
    #         }
    #         subreddits.append(newItem)
    #     return subreddits

    def get_subsreddits_info(self, db, refresh_token, subsList):
        reddit = praw.Reddit(
            client_id=self.conf.get("client_id"),
            client_secret=self.conf.get("client_secret"),
            refresh_token=refresh_token,
            user_agent=self.conf.get("user_agent"),
        )
        subreddits = []
        for sub in subsList:
            print("subreddit", sub)
            subreddit = reddit.subreddit(sub)
            rules = crud.get_rules_by_subreddit(db, sub)

            print("rules DB: ", rules)
            if rules == None:
                try:
                    newRules = []
                    for rule in subreddit.rules:
                        newRules.append(
                            {"name": rule.short_name,
                                "description": rule.description, }
                        )
                    rules = crud.create_subreddit_rules(
                        db, {"subreddit": sub, "content": newRules}
                    )
                except RedditAPIException as exception:
                    print(exception)
                    rules = crud.get_rules_by_subreddit(db, sub)
            elif not rules.updated_at > datetime.now() - timedelta(**self.cashTime):
                try:
                    print("update rules")
                    newRules = []
                    for rule in subreddit.rules:
                        newRules.append(
                            {"name": rule.short_name,
                                "description": rule.description, }
                        )
                    crud.update_subreddit_rules(db, sub, newRules)
                    rules = crud.get_rules_by_subreddit(db, sub)
                except RedditAPIException as exception:
                    print(exception)
                    rules = crud.get_rules_by_subreddit(db, sub)

            flairs = crud.get_flairs_by_subreddit(db, sub)
            print("flairs DB: ", flairs)
            if flairs == None:
                try:
                    newFlairs = reddit.post(
                        "r/" + sub + "/api/flairselector/", data={"is_newlink": True}
                    )["choices"]
                    flairs = crud.create_subreddit_flairs(
                        db, {"subreddit": sub, "content": newFlairs}
                    )
                except RedditAPIException as exception:
                    print(exception)
                    flairs = crud.get_flairs_by_subreddit(db, sub)
            elif not flairs.updated_at > datetime.now() - timedelta(**self.cashTime):
                print("update flairs")
                try:
                    newFlairs = reddit.post(
                        "r/" + sub + "/api/flairselector/", data={"is_newlink": True}
                    )["choices"]
                    crud.update_subreddit_flairs(db, sub, newFlairs)
                    flairs = crud.get_flairs_by_subreddit(db, sub)
                except RedditAPIException as exception:
                    print(exception)
                    flairs = crud.get_flairs_by_subreddit(db, sub)
                except Exception as e:
                    flairs = crud.get_flairs_by_subreddit(db, sub)

            newItem = {
                "subreddit": sub,
                "flairs": flairs.content,
                "rules": rules.content,
            }
            subreddits.append(newItem)
        return subreddits

    def create_user_post(self, db, user_data, post):
        reddit = praw.Reddit(
            client_id=self.conf.get("client_id"),
            client_secret=self.conf.get("client_secret"),
            refresh_token=user_data.refresh_token,
            user_agent=self.conf.get("user_agent"),
        )
        print('post id', post.id)
        subreddit = reddit.subreddit(post.subreddit)
        try:
            if(post.type == 'url'):
                print('post url')
                posted = subreddit.submit(
                    post.title, url=post.content, nsfw=post.nsfw, spoiler=post.spoiler, flair_id=post.flair)
            if(post.type == 'text'):
                print('post text')
                posted = subreddit.submit(
                    post.title, selftext=post.content, nsfw=post.nsfw, spoiler=post.spoiler, flair_id=post.flair)
                # post = crud.get_post_by_id(db, post_id)
                # if (post.status != enum):
            print('posted', posted)
            print('permalink', posted.permalink)
            # crud.add_log(db, schemas.LogBase(method='create_user_post',
            #                                  content=json.dumps(
            #                                      {'post_id': post.id, 'url': posted.permalink, 'createad': true, }),
            #                                  owner_id=user_data.id))
            return crud.publish_user_post(db, post.id, user_data, posted.permalink)
        except RedditAPIException as exception:
            for e in exception.items:
                print(e.error_type)
                if e.field == "ratelimit":
                    if wait == True:
                        msg = e.message.lower()
                        index = msg.find("minute")
                        minutes = int(msg[index - 2]) + \
                            1 if index != -1 else 1
                        print("\n\nRatelimit reached. Waiting " +
                              str(minutes)+" minutes before retrying.")
                        # time.sleep(minutes*60)
                        # return 5
                        return e
                    else:
                        print("Error posting submission -- "+str(e))
                        return e
            return exception
        except Exception as e:
            print("Error posting submission -- "+str(e))
            return e


if __name__ == "__main__":
    server = Server()
    server.get_link_to_auth()
