class DownloadTestMixin(object):
    _variation_sku = -1

    @property
    def variation_sku(self):
        self._variation_sku += 1
        return self._variation_sku
