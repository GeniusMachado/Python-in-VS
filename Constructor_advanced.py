import json

class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    @classmethod
    def from_json(cls, json_data):
        # Alternative constructor for JSON input
        data = json.loads(json_data)
        return cls(data['name'], data['age'])

# Standard usage
user1 = User("Alice", 30)

# Alternative usage
user2 = User.from_json('{"name": "Bob", "age": 25}')
