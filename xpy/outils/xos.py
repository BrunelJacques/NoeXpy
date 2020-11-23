import platform


def ismacintosh():
    if platform.system() == "Darwin":
        return True
    else:
        return False


def iswindows():
    if platform.system() == "Windows":
        return True
    else:
        return False


def islinux():
    if platform.system() == "Linux":
        return True
    else:
        return False
