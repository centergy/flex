from flask.signals import (
	template_rendered,
	before_render_template,
	request_started,
	request_finished,
	request_tearing_down,
	got_request_exception,
	appcontext_tearing_down,
	appcontext_pushed,
	appcontext_popped,
	message_flashed,
	Namespace
)



_signals = Namespace()

app_booting = _signals.signal('app-booting')
app_booted = app_ready = _signals.signal('app-booted')

# app_registering_blueprint = _signals.signal('app-registering-blueprint')
# app_registered_blueprint = _signals.signal('app-registered-blueprint')

app_starting = _signals.signal('app-started')
app_started = _signals.signal('app-started')

blueprint_registering = _signals.signal('blueprint-registering')
blueprint_registered = _signals.signal('blueprint-registered')


session_starting = _signals.signal('session-starting')
session_started = _signals.signal('session-started')
session_ending = _signals.signal('session-ending')
session_ended = _signals.signal('session-ended')


