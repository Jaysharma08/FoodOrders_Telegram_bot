orders = []

def get_next_token():
    try:
        with open("token.txt", "r") as f:
            token = int(f.read().strip())
    except:
        token = 0

    token += 1

    with open("token.txt", "w") as f:
        f.write(str(token))

    return token
