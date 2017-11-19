"""See: https://github.com/evansd/whitenoise/issues/96"""

from whitenoise.storage import CompressedManifestStaticFilesStorage


class WhitenoiseErrorSquashingStorage(CompressedManifestStaticFilesStorage):

    def url(self, name, **kwargs):
        try:
            return super(WhitenoiseErrorSquashingStorage, self).url(name, **kwargs)
        except ValueError:
            return name