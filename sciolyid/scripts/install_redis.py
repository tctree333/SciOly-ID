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
with tarfile.open("redis-stable.tar.gz") as tar:
    
    import os
    
    def is_within_directory(directory, target):
        
        abs_directory = os.path.abspath(directory)
        abs_target = os.path.abspath(target)
    
        prefix = os.path.commonprefix([abs_directory, abs_target])
        
        return prefix == abs_directory
    
    def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
    
        for member in tar.getmembers():
            member_path = os.path.join(path, member.name)
            if not is_within_directory(path, member_path):
                raise Exception("Attempted Path Traversal in Tar File")
    
        tar.extractall(path, members, numeric_owner=numeric_owner) 
        
    
    safe_extract(tar)
subprocess.run("make", cwd="redis-stable")
