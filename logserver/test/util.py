import string
import random


def ascii_string(length=32):
    """Return a random string of ascii characters."""
    return ''.join(random.sample(string.ascii_letters, length))
