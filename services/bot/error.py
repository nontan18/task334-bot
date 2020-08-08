class CommandArgumentsError(Exception):
    pass

class ExceedMaximumTweetLengthError(Exception):
    pass

class IndexIsOutOfTasksRangeError(Exception):
    pass

class NotRegisteredUserError(Exception):
    pass

class CommandNotFoundError(Exception):
    pass

class NoCommandError(Exception):
    pass    