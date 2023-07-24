import string
import random


def generate_code():
    code = ''.join(random.choice(string.digits) for _ in range(4))
    return code
