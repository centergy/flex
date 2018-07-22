from flex.db import db, Manager
from flex.utils.decorators import export
from flex.core.exc import ValidationError
from flex import carbon




@export
class OptionsDbManager(Manager):

	def get_by_key(self, key):
		return self.get(key)
