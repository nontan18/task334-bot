import time
import firebase_admin
from error import *
from models import *
from settings import *
from replyer import Replyer, handle_command, handle_error

class Task334Bot(Replyer):

    @handle_command(commands=['add', '追加'])
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

    @handle_command(commands=['done', '削除'])
    def handle_done_tweet(self, args, user: User, tweet):
        try:
            indexes = list(map(lambda i: int(i) - 1, args[2:]))
        except ValueError:
            raise CommandArgumentsError()

        tasks = self.list_task(user) 

        if len(tasks) - 1 < max(indexes) or 0 > min(indexes):
            raise IndexIsOutOfTasksRangeError()
 
        done_tasks = [tasks.pop(index) for index in sorted(indexes, reverse=True)]

        for task in done_tasks:
            self.done_task(user, task.id)

        tweet = self.tweet_tasks(user, tasks, [(task, Status.DONE) for task in done_tasks])
        self.update_latest_tweet_id(user, tweet['id_str'])


    @handle_command(commands=['left', '放置'])
    def handle_left_tweet(self, args, user: User, tweet):
        try:
            indexes = list(map(lambda i: int(i)-1, args[2:]))
        except ValueError:
            raise CommandArgumentsError()

        tasks = self.list_task(user)
        print('tasks:', tasks)
        
        if len(tasks) - 1 < max(indexes) or 0 > min(indexes):
            raise IndexIsOutOfTasksRangeError()

        left_tasks = [tasks.pop(index) for index in sorted(indexes, reverse=True)]

        for task in left_tasks:
            self.left_task(user, task.id)

        tweet = self.tweet_tasks(user, tasks, [(task, Status.LEFT) for task in left_tasks])
        self.update_latest_tweet_id(user, tweet['id_str'])


    @handle_command(commands=['devide', '分割'])
    def handle_devide_tweet(self, args, user: User, tweet):
        index = int(args[2]) - 1        
        tasks = self.list_task(user)

        if len(tasks) - 1 < index:
            raise IndexIsOutOfTasksRangeError()

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


    @handle_error(CommandArgumentsError)
    def handle_commands_arguments_error(self, user, tweet):
        self.reply(tweet, 'コマンド引数に問題があります')
        self.create_favorite(tweet)


    @handle_error(ExceedMaximumTweetLengthError)
    def handle_exceed_maximum_tweet_length_error(self, user, tweet):
        self.reply(tweet, 'タスクの量が140文字を超えます。早くタスクを処理してください。')
        self.create_favorite(tweet)


    @handle_error(IndexIsOutOfTasksRangeError)
    def handle_index_is_out_of_tasks_range_error(self, user, tweet):
        self.reply(tweet, 'タスク番号が選択範囲を超えています。正しいタスク番号を指定して下さい。')
        self.create_favorite(tweet)


    @handle_error(NotRegisteredUserError)
    def handle_not_registered_user_error(self, user, tweet):
        self.reply(tweet, 'TASK334を利用するためには、こちらからTwitter連携を行う必要があります。')
        self.create_favorite(tweet)

    @handle_error(NoCommandError)
    def handle_no_command_error(self, user, tweet):
        self.reply(tweet, 'TASK334を利用するためにはコマンドを入力して下さい。')
        self.create_favorite(tweet)

    @handle_error(CommandNotFoundError)
    def handle_command_not_found_error(self, user, tweet):
        self.reply(tweet, '無効なコマンドです。現在、使用可能なコマンドは「追加(add)」、「完了(done)」、「放置(left)」、「分割(devide)」の４つです。')
        self.create_favorite(tweet)

    def handle_unexpected_error(self, user, tweet):
        self.reply(tweet, 'ご不便をおかけしてすみません。予期されないエラーが発生しました。管理者(@nontangent)が至急処理に当たります。')
        self.create_favorite(tweet)



def onetimerun(data, context):
    bot = Task334Bot()

    for _ in range(4):
        bot.handle_tweets()
        time.sleep(15)

def main():
    bot = Task334Bot()
    bot.run()


if __name__ == '__main__':
    main()
    # print(ReplyHandler.handling_commands)

