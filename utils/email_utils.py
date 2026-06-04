from django.conf import settings
from functools import lru_cache
import os

@lru_cache(maxsize=1)
def load_blocked_domains():
    print('yha bhi hu1')
    path = os.path.join(settings.BASE_DIR, "domains.txt")
    print(path)
    domains = set()

    with open(path, "r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            domain = line.strip().lower()
            if domain and not domain.startswith("#"):
                domains.add(domain)

    return domains


def is_blocked_domain(email):
    print('yha bhi hu2')
    if not email or "@" not in email:
        return False

    domain = email.split("@")[-1].lower()
    return domain in load_blocked_domains()
