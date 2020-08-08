import time
from models import User, Task, Status
from types import MethodType, FunctionType, LambdaType
from settings import *
from clients import TwitterClient, FireStoreClient

def handle_command(commands=[]):
    def decorate(func):
        setattr(func, '__commands', commands)
        return func
    return decorate


def handle_error(error):
    def decorate(func):
        setattr(func, '__error', error)
        return func
    return decorate


class ReplyerMeta(type):
    def __new__(cls, name, bases, attr):
        def is_excutable(v):
            return isinstance(v, (MethodType, FunctionType, LambdaType))

        handling_commands = attr.get('handling_commands', [])
        handling_errors = attr.get('handling_errors', [])

        for k, v in attr.items():
            if not is_excutable(v):
                continue
                        
            commands = getattr(v, '__commands', None)
            if commands:
                handling_commands.append((getattr(v, '__commands'), v))

            error = getattr(v, '__error', None)
            if error:
                handling_errors.append((getattr(v, '__error'), v))

        klass = type.__new__(cls, name, bases, attr)
        klass.handling_commands = handling_commands
        klass.handling_errors = handling_errors
        return klass


class Replyer(
    TwitterClient,
    FireStoreClient,
    metaclass=ReplyerMeta
):
    handling_commands = []

    def __init__(self):
        super().__init__()

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

    def handle_tweet(self, tweet):
        args = list(filter(lambda x: x != '', tweet['text'].replace('　', ' ').split(' ')))
        replyer_id = tweet['user']['id_str']
        user = self.get_user_by_twitter_id(replyer_id)

        if len(args) < 2:
            return

        try:
            if not user:
                raise NotRegisteredUserError()

            command = args[1].lower()

            for commands, func in self.handling_commands:
                if command in commands:
                    func(self, args, user, tweet)
                    self.delete_tweet(user, tweet)
                    return
            
            self.handle_exception_tweet(args, user, tweet)
            self.create_favorite(tweet)
            return

        except Exception as e:
            for error, func in self.handling_errors:
                if type(e) == error:
                    func(self, user, tweet)
                    return
            raise(e)

            # TODO: エラーにハマった場合に動けなくなるのをどうにかする。


    def handle_exception_tweet(self, args, user: User, tweet):
        pass


