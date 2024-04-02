class Md5sum:

    def __init__(self,filename):
        from hashlib import md5
        from mmap import mmap, ACCESS_READ
        
        with open(filename) as file, mmap(file.fileno(), 0, access=ACCESS_READ) as file:
            self.sum = md5(file).hexdigest()
