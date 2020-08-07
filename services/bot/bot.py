import time
import firebase_admin
from firebase_admin import firestore
from twython import Twython, TwythonError
from error import *
from models import *
from settings import *
from typing import List

firebase_admin.initialize_app(CERTIFICATE)

class ReplyHandler:
    def __init__(self):
        self.twitter = Twython(
            CONSUMER_KEY,
            CONSUMER_SECRET,
            ACCESS_TOKEN,
            ACCESS_TOKEN_SECRET
        )

        self.db = firestore.client()

    def run(self):
        while True:
            try:
                self.handle_tweets()

            except Exception as e:
                print('Error:', e)

            time.sleep(INTERVAL)

    def handle_tweets(self):
        tweets = self.get_unread_tweets()

        for tweet in reversed(tweets):
            print(tweet['text'])
            self.handle_tweet(tweet)

    def get_unread_tweets(self):
        tweets = self.twitter.get_mentions_timeline(count=10)
            
        return list(filter(lambda t: t['favorited'] == False, tweets))

    def create_favorite(self, tweet):
        return self.twitter.create_favorite(id=tweet['id'])

    def is_registered(self, twitter_id):
        users = self.db.collection('users').where('twitter.id', '==', twitter_id).limit(1).get()
        return True if len(users) > 0 else False

    def handle_tweet(self, tweet):
        args = list(filter(lambda x: x != '', tweet['text'].replace('　', ' ').split(' ')))
        replyer_id = tweet['user']['id_str']
        user = self.get_user_by_twitter_id(replyer_id)

        if len(args) < 2:
            return

        if not user:
            return

        command = args[1].upper()
        try:
            if command in ('ADD', '追加'):
                self.handle_add_tweet(args, user, tweet)
                self.delete_tweet(user, tweet)

            elif command in ('DONE', '完了'):
                self.handle_done_tweet(args, user, tweet)
                self.delete_tweet(user, tweet)

            elif command in ('LEFT', '放置'):
                self.handle_left_tweet(args, user, tweet)
                self.delete_tweet(user, tweet)

            elif command in ('DEVIDE', '分割'):
                self.handle_devide_tweet(args, user, tweet)
                self.delete_tweet(user, tweet)

            else:
                self.handle_exception_tweet(args, user, tweet)
                self.create_favorite(tweet)

        except CommandArgumentsError:
            self.reply(tweet, 'コマンド引数に問題があります')
            self.create_favorite(tweet)

        except ExceedMaximumTweetLengthError:
            self.reply(tweet, 'タスクの量が140文字を超えます。早くタスクを処理してください。')
            self.create_favorite(tweet)

        except Exception as e:
            raise(e)


    def handle_add_tweet(self, args, user: User, tweet): 
        additional_tasks = [Task(id=None, name=name, status=Status.WIP) 
            for name in args[2:]]
        tasks = self.list_task(user) + additional_tasks

        content = self.content_format(tasks)
        # 140文字制限
        if len(content) > 140:
            raise ExceedMaximumTweetLengthError()


        for task in additional_tasks:
            self.add_task(user, task)

        tweet = self.tweet(user, content)

        content = self.content_format(tasks)

        self.update_latest_tweet_id(user, tweet['id_str'])


    def handle_done_tweet(self, args, user: User, tweet):
        try:
            indexes = list(map(lambda i: int(i) - 1, args[2:]))
        except ValueError:
            raise CommandArgumentsError()

        tasks = self.list_task(user) 

        if len(tasks) < max(indexes) or 0 > min(indexes):
            return
 
        done_tasks = [tasks.pop(index) for index in sorted(indexes, reverse=True)]

        for task in done_tasks:
            self.done_task(user, task.id)

        tweet = self.tweet_tasks(user, tasks, [(task, Status.DONE) for task in done_tasks])
        self.update_latest_tweet_id(user, tweet['id_str'])


    def handle_left_tweet(self, args, user: User, tweet):
        try:
            indexes = list(map(lambda i: int(i)-1, args[2:]))
        except ValueError:
            raise CommandArgumentsError()

        tasks = self.list_task(user)
        print('tasks:', tasks)
        
        if len(tasks) < max(indexes) or 0 > min(indexes):
            return

        left_tasks = [tasks.pop(index) for index in sorted(indexes, reverse=True)]

        for task in left_tasks:
            self.left_task(user, task.id)

        tweet = self.tweet_tasks(user, tasks, [(task, Status.LEFT) for task in left_tasks])
        self.update_latest_tweet_id(user, tweet['id_str'])


    def handle_devide_tweet(self, args, user: User, tweet):
        index = int(args[2]) - 1        
        tasks = self.list_task(user)

        if len(tasks) < index:
            return

        additional_tasks = [Task(id=None, name=name, status=Status.WIP) 
            for name in args[3:]]

        tasks += additional_tasks

        for task in additional_tasks:
            self.add_task(user, task)

        devided_task = tasks.pop(index)
        devided_task.status = Status.DEVIDED
        self.devided_task(user, devided_task.id)
        
        content = self.content_format(tasks, [(devided_task, Status.DEVIDED)])
        tweet = self.tweet(user, content)

        self.update_latest_tweet_id(user, tweet['id_str'])


    def handle_exception_tweet(self, args, user: User, tweet):
        pass


    def add_task(self, user: User, task: Task):
        return self.db.collection('users').document(user.id) \
        .collection('tasks').document().set({
            'name': task.name,
            'status': task.status.value,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })


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


    def delete_tweet(self, user: User, tweet):
        twitter = Twython(
            CONSUMER_KEY,
            CONSUMER_SECRET,
            user.twitter.access_token,
            user.twitter.secret
        )

        return twitter.destroy_status(id=tweet['id_str'])

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


    def update_latest_tweet_id(self, user: User, tweet_id):
        return self.db.collection('users').document(user.id).update({
            'latestTweetId': tweet_id
        })


    def get_latest_tweet_id(self, user: User):
        return user.latest_tweet_id
        # user = self.db.collection('users').document(user.id).get().to_dict()
        # return user['latestTweetId'] if 'latestTweetId' in user else None

def onetimerun(data, context):
    replyer = ReplyHandler()

    for _ in range(4):
        replyer.handle_tweets()
        time.sleep(15)

def main():
    replyer = ReplyHandler()
    replyer.run()


if __name__ == '__main__':
    main()

