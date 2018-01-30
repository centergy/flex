from sqlalchemy_utils.types import PhoneNumberType as BasePhoneNumberType
from flex.conf import config


class PhoneNumberType(BasePhoneNumberType):

	def __init__(self, region=None, max_length=20, *args, **kwargs):
		region = region or config.get('LOCALE_COUNTRY_CODE', 'KE')
		super(PhoneNumberType, self).__init__(region, max_length, *args, **kwargs)


