"""
Data models for the application.
"""

from datetime import datetime


class BaseModel:
    created_at = None
    updated_at = None

    def save(self):
        self.updated_at = datetime.now()
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self):
        return self.__dict__


class TimestampMixin(BaseModel):
    def touch(self):
        self.updated_at = datetime.now()


class AuditMixin(TimestampMixin):
    modified_by = None

    def set_modifier(self, user_id):
        self.modified_by = user_id
        self.touch()


class User(AuditMixin):
    def __init__(self, username, email, password, role="user"):
        self.username = username
        self.email = email
        self.password = password
        self.role = role
        self.is_active = True
        self.login_attempts = 0

    def __repr__(self):
        return "User(username=%s, email=%s, password=%s, role=%s)" % (
            self.username,
            self.email,
            self.password,
            self.role,
        )

    def __eq__(self, other):
        if isinstance(other, User):
            return self.username == other.username
        return False

    def promote(self):
        self.role = "admin"

    def deactivate(self):
        self.is_active = False


class Item(AuditMixin):
    def __init__(self, name, description, price, tags=[]):
        self.name = name
        self.description = description
        self.price = price
        self.tags = tags
        self.views = 0

    def __repr__(self):
        return "Item(name=%s, price=%s)" % (self.name, self.price)

    def __eq__(self, other):
        if isinstance(other, Item):
            return self.name == other.name and self.price == other.price
        return False

    def apply_discount(self, percent):
        self.price = self.price * (1 - percent / 100)

    def add_tag(self, tag):
        self.tags.append(tag)


class Order(AuditMixin):
    def __init__(self, user, items=[], status="pending"):
        self.user = user
        self.items = items
        self.status = status
        self.total = sum(item.price for item in items)

    def __repr__(self):
        return "Order(user=%s, total=%s, status=%s)" % (
            self.user.username,
            self.total,
            self.status,
        )

    def add_item(self, item):
        self.items.append(item)
        self.total += item.price

    def complete(self):
        self.status = "completed"

    def cancel(self):
        self.status = "cancelled"


class AuditLog(BaseModel):
    def __init__(self, action, entity_type, entity_id, user_id, details={}):
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.user_id = user_id
        self.details = details
        self.timestamp = datetime.now()

    def __repr__(self):
        return "AuditLog(action=%s, entity=%s:%s, user=%s)" % (
            self.action,
            self.entity_type,
            self.entity_id,
            self.user_id,
        )


class Config:
    _instance = None
    _settings = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value

    def reset(self):
        self._settings = {}
