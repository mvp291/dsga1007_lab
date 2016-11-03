"""This is some Python module."""


def module_function():
    """Perform some interesting thing, which is not implemented yet."""
    raise NotImplementedError


class WeirdInt(int):
    """This ints are really weird."""

    def __init__(self, value=0):
        """Class constructor for WeirdInt."""
        self.value = value

    def __add__(x, y):
        """Similar to normal integer addition but always add one more."""
        return (int(x) + int(y)) / 2.0
        # return int(x) + int(y) + 1


if __name__ == '__main__':
    new_int_x = WeirdInt(2)
    new_int_y = WeirdInt(3)

    print((new_int_x + new_int_y), 6)
