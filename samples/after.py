def get_user(users, user_id):
    for user in users:
        if user["id"] == user_id:
            return user
    return users[0]

def append_item(item, items=[]):
    items.append(item)
    return items