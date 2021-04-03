import time


class ActivePanel:
    def __init__(self, mid, user, types, instance):
        """ActivePanel class

        Args:
            mid (int): The active panel's message ID
            user (int): Active panel users
            types (set): All types this active panel's instance inherits from
            instance (common.BasicPanel): This active panel's instance
        """
        self.instance = instance
        self.types = types
        self.timestamp = time.time()
        self.user = user
        self.id = mid

    def is_type(self, string):
        """Check if this active panel is of a certain type

        Args:
            string (str): Type

        Returns:
            bool: True if 'string' is one of its types
        """
        return string in self.types
