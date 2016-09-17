SKU = -1


class DownloadTestMixin(object):

    @property
    def sku(self):
        global SKU
        SKU += 1
        return SKU
