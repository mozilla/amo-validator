

def is_ctrl_char(x, y=None):
    "Returns whether X is an ASCII control character"
    if y is None:
        y = ord(x)
    return 0 <= y <= 31 and y not in (9, 10, 13)  # TAB, LF, CR


def is_standard_ascii(x):
    "Returns whether X is a standard, non-control ASCII character"
    y = ord(x)
    return not (is_ctrl_char(x, y) or y > 126)


def filter_ascii(text):
    if isinstance(text, list):
        return [filter_ascii(x) for x in text]
    return "".join((x if is_standard_ascii(x) else "?") for x in text)

