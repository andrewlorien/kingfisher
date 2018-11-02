from ocdskingfisher.base import Source


class MoldovaMTenderSource(Source):
    """
    Paged JSON:
        https://public.api.mepps.openprocurement.net/api/0/tenders
        https://public.api.mepps.openprocurement.net/api/0/plans
        https://public.api.mepps.openprocurement.net/api/0/contracts
    """

    url = 'https://public.api.mepps.openprocurement.net/api/'
    source_id = 'moldova_mtender'

    def gather_all_download_urls(self):
        return []