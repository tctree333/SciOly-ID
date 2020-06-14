# Based on https://redis.io/topics/quickstart
import subprocess
import tarfile
from urllib.request import urlopen
from shutil import copyfileobj

# from https://stackoverflow.com/a/15035466/7941251
with urlopen("http://download.redis.io/redis-stable.tar.gz") as in_stream, open(
    "redis-stable.tar.gz", "wb"
) as out_file:
    copyfileobj(in_stream, out_file)
tar = tarfile.open("redis-stable.tar.gz")
tar.extractall()
subprocess.run("make", cwd="redis-stable")
