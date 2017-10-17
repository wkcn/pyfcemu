import hashlib

def hashFile(path):
    return hashlib.md5(path.encode("utf-8")), None
