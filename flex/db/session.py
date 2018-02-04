from sqlalchemy.orm.session import Session as SessionBase
from .query import Query
from .utils import _get_app_state


class Session(SessionBase):

	def __init__(self, db, **options):
		#: The application that this session belongs to.
		self.app = app = db.get_app()
		options = db.make_session_options(db.get_config(app), options)
		bind = options.pop('bind', None) or db.engine
		SessionBase.__init__(self, bind=bind, **options)

	def get_bind(self, mapper=None, clause=None):
		# mapper is None if someone tries to just get a connection
		if mapper is not None:
			info = getattr(mapper.mapped_table, 'info', {})
			bind_key = info.get('bind_key')
			if bind_key is not None:
				state = _get_app_state(self.app)
				return state.db.get_engine(self.app, bind=bind_key)
		return SessionBase.get_bind(self, mapper, clause)

	# def save(self, *models, commit=True):
	# 	# raise Exception("Re implement this.")
	# 	self.add_all(models)
	# 	if not self.autocommit and commit:
	# 		self.commit()

	# def delete(self, *models, commit=False):
	# 	for model in models:
	# 		super(Session, self).delete(model)

	# 	if not self.autocommit and commit:
	# 		self.commit()

