
class PageIsNotLoaded(Exception):
    pass


class ItemIsNotAvailable(Exception):
    pass


class ItemHasSizes(Exception):
    def __init__(self, sizes_list):
        self.sizes_list = sizes_list
        super().__init__(sizes_list)
