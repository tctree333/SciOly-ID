import os
import pickle

import redis

if os.getenv("LOCAL_REDIS") == "true":
    database = redis.Redis(host='localhost', port=6379, db=0)
else:
    database = redis.from_url(os.getenv("REDIS_URL"))

def restore_all():
    print("reading dump")
    with open("backups/dump.dump", 'rb') as f:
        with open("backups/keys.txt", 'r') as k:
            print("restoring")
            for line in k:
                key = line.strip()
                data = pickle.load(f)
                database.restore(key, 0, data, True)
    print("restore finished")

if __name__ == "__main__":
    restore_all()
