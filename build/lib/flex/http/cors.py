from flask_cors import CORS
from flex.conf import config

cors = CORS(origins=config.CORS_ORIGINS, supports_credentials=True)