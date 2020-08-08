from typing import List
from firebase_admin import firestore
from twython import Twython, TwythonError

from models import User, Task, Status
from settings import *


class TwitterClient:
    def __init__(self):
        self.twitter = Twython(
            CONSUMER_KEY,
            CONSUMER_SECRET,
            ACCESS_TOKEN,
            ACCESS_TOKEN_SECRET
        )
        super().__init__()

    def delete_tweet(self, user: User, tweet):
        twitter = Twython(
            CONSUMER_KEY,
            CONSUMER_SECRET,
            user.twitter.access_token,
            user.twitter.secret
        )

        return twitter.destroy_status(id=tweet['id_str'])

    def get_unread_tweets(self):
        tweets = self.twitter.get_mentions_timeline(count=10)
            
        return list(filter(lambda t: t['favorited'] == False, tweets))

    def create_favorite(self, tweet):
        return self.twitter.create_favorite(id=tweet['id'])

    def content_format(self, tasks: List[Task], removes: List[Task] = []):
        content = ''
        
        for task, status in removes:
            content += task.name + ' ' + status.name.capitalize() + '\n'

        content += '#TASK334\n'
        content += '\n'.join([f"{i+1}.{task.name}" for i, task in enumerate(tasks)])
        
        return content


    def tweet(self, user: User, content):
        latest_tweet_id = self.get_latest_tweet_id(user)

        twitter = Twython(
            CONSUMER_KEY,
            CONSUMER_SECRET,
            user.twitter.access_token,
            user.twitter.secret
        )
 
        if latest_tweet_id:
            tweet = twitter.update_status(
                status=content,
                in_reply_to_status_id=latest_tweet_id,
                auto_populate_reply_metadata=True
            )
        else:
            tweet = twitter.update_status(status=content)

        return tweet


    def tweet_tasks(self, user: User, tasks: List[Task], removes: List[Task]=[]): 
        content = self.content_format(tasks, removes)
        return self.tweet(user, content)

    def reply(self, tweet, content):
        return self.twitter.update_status(
            status=content,
            in_reply_to_status_id=tweet['id_str'],
            auto_populate_reply_metadata=True
        )


class FireStoreClient:
    def __init__(self):
        self.db = firestore.client()
        super().__init__()

    def add_task(self, user: User, task: Task):
        return self.db.collection('users').document(user.id) \
        .collection('tasks').document().set({
            'name': task.name,
            'status': task.status.value,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })

    def is_registered(self, twitter_id):
        users = self.db.collection('users').where('twitter.id', '==', twitter_id).limit(1).get()
        return True if len(users) > 0 else False

    def done_task(self, user: User, task_id: str):
        return self.db.collection('users').document(user.id) \
            .collection('tasks').document(task_id).set({
                'status': Status.DONE.value,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }, merge=True)


    def left_task(self, user: User, task_id: str):
        return self.db.collection('users').document(user.id) \
            .collection('tasks').document(task_id).set({ \
                'status': Status.LEFT.value,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }, merge=True)

    def devided_task(self, user: User, task_id):
        return self.db.collection('users').document(user.id) \
            .collection('tasks').document(task_id).set({ \
                'status': Status.DEVIDED.value,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }, merge=True)

    def get_user_by_twitter_id(self, twitter_id) -> User:
        users = self.db.collection('users') \
            .where('twitter.id', '==', twitter_id).limit(1).get()
        if len(users):
            user_d = users[0].to_dict()
            user_d['id'] = users[0].id
            return User.from_dict(user_d)
        return None

    def list_task(self, user: User, status: Status = Status.WIP):
        task_docs = self.db.collection('users').document(user.id) \
            .collection('tasks').where('status', '==', status.value) \
            .order_by('createdAt', direction=firestore.Query.ASCENDING).get()

        tasks = []
        for task_doc in task_docs:
            task_d = task_doc.to_dict()
            task_d['id'] = task_doc.id
            tasks.append(Task.from_dict(task_d))

        return tasks

    def update_latest_tweet_id(self, user: User, tweet_id):
        return self.db.collection('users').document(user.id).update({
            'latestTweetId': tweet_id
        })


    def get_latest_tweet_id(self, user: User):
        return user.latest_tweet_id
        # user = self.db.collection('users').document(user.id).get().to_dict()
        # return user['latestTweetId'] if 'latestTweetId' in user else None