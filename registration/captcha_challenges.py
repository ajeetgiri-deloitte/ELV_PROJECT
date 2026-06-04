import random
import string

def complex_symbol_challenge():
    # Include letters, digits, and selected symbols
    # chars = string.ascii_letters + string.digits + "!@#$%&*?"
    chars = string.ascii_letters + string.digits 
    challenge = ''.join(random.choices(chars, k=6))
    return challenge, challenge
