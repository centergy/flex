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
)
from flex.signal import signal


app_booting = signal('app_booting')
app_booted = app_ready = signal('app_booted')

# app_registering_blueprint = _signals.signal('app-registering-blueprint')
# app_registered_blueprint = _signals.signal('app-registered-blueprint')

app_starting = signal('app_started')
app_started = signal('app_started')

blueprint_registering = signal('blueprint_registering')
blueprint_registered = signal('blueprint_registered')


session_starting = signal('session_starting')
session_started = signal('session_started')
session_ending = signal('session_ending')
session_ended = signal('session_ended')

install = signal('install')



