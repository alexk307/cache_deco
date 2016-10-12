class SimpleObject(object):

    def __init__(self, string, number):
        self.string = string
        self.number = number

    def __eq__(self, other):
        return self.string == other.string and self.number == other.number
