def md5sum(filename):
    from hashlib import md5
    from mmap import mmap, ACCESS_READ
    
    with open(filename) as file, mmap(file.fileno(), 0, access=ACCESS_READ) as file:
        return md5(file).hexdigest()