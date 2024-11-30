class Event:
    name = None

    def __init__(self, data):
        self.data = data
        self.topic = self.name
        # key is used as message key
        self.key = data["id"]

    def __str__(self):
        return f"{self.name}: {self.data}"


class UserCreated(Event):
    name = "UserCreated"


class UserUpdated(Event):
    name = "UserUpdated"


class UserDeleted(Event):
    name = "UserDeleted"


class PasswordResetRequested(Event):
    name = "PasswordResetRequested"


class EmailVerificationRequested(Event):
    name = "EmailVerificationRequested"


class MobileVerificationRequested(Event):
    name = "MobileVerificationRequested"


class VerificationCreated(Event):
    name = "VerificationCreated"


class VerificationAssigned(Event):
    name = "VerificationAssigned"


class VerificationInspected(Event):
    name = "VerificationInspected"
