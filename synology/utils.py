#coding=utf-8
import json
import random
import string
import time
from urllib.parse import quote


def jsondump(data):
    """Return prettified JSON dump"""
    return json.dumps(data, sort_keys = True, indent = 4)


def jsonprint(data):
    """Prettify JSON dump to stdout"""
    print(jsondump(data))

def generate_key(len: int = 32, lowercase: bool = True, uppercase: bool = True, digits: bool = True) -> str:
    random.seed()
    chars = ''
    if lowercase: chars += string.ascii_lowercase
    if uppercase: chars += string.ascii_uppercase
    if digits: chars += string.digits
    return ''.join([random.choice(chars) for _ in range(len)])