import enum
from dataclasses import dataclass
import datetime as dt

class Status(enum.Enum):
    WIP = 0
    DONE = 1
    LEFT = 2
    DEVIDED = 3

    def __str__(self):
        return self.value

@dataclass
class Twitter:
    access_token: str = None
    secret: str = None

    @staticmethod
    def from_dict(src):
        return Twitter(
            access_token=src['accessToken'],
            secret=src['secret']
        )

@dataclass
class User:
    id: str = None
    twitter: Twitter = None
    latest_tweet_id: str = None

    @staticmethod
    def from_dict(src):
        return User(
            id=src['id'] if 'id' in src else None,
            latest_tweet_id=src['latestTweetId'] if 'latestTweetId' in src else None,
            twitter=Twitter.from_dict(src['twitter'])
        )

@dataclass
class Task:
    id: str = None
    name: str = None
    status: Status = Status.WIP
    created_at: dt.datetime = None
    updated_at: dt.datetime = None

    @staticmethod
    def from_dict(src):
        return Task(
            id=src['id'] if 'id' in src else None,
            name=src['name'],
            status=src['status'],
            created_at=src['createdAt'],
            updated_at=src['updatedAt']
        )
