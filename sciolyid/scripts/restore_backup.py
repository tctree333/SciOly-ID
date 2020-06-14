import os
import pickle
import sys

import redis

if os.getenv("LOCAL_REDIS") == "true":
    database = redis.Redis(host="localhost", port=6379, db=0)
else:
    database = redis.from_url(os.getenv("REDIS_URL"))
folder = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "backups"


def restore_all():
    print("reading dump")
    with open(f"{folder}/dump.dump", "rb") as f:
        with open(f"{folder}/keys.txt", "r") as k:
            print("restoring")
            for line in k:
                key = line.strip()
                data = pickle.load(f)
                database.restore(key, 0, data, True)
    print("restore finished")


if __name__ == "__main__":
    restore_all()
