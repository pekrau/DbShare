"DbShare web app."

import flask

import dbshare
import dbshare.about
import dbshare.config
import dbshare.db
import dbshare.dbs
import dbshare.chart
import dbshare.query
import dbshare.schema
import dbshare.site
import dbshare.system
import dbshare.table
import dbshare.user
import dbshare.view

import dbshare.api.root
import dbshare.api.db
import dbshare.api.dbs
import dbshare.api.schema
import dbshare.api.table
import dbshare.api.user
import dbshare.api.users
import dbshare.api.view
import dbshare.api.chart
from dbshare import constants
from dbshare import utils


app = flask.Flask(__name__)

# Add URL map converters.
app.url_map.converters['name'] = utils.NameConverter
app.url_map.converters['nameext'] = utils.NameExtConverter

# Add template filters.
app.add_template_filter(utils.informative)
app.add_template_filter(utils.size_none)
app.add_template_filter(utils.none_as_literal_null)
app.add_template_filter(utils.none_as_empty_string)
app.add_template_filter(utils.do_markdown, name='markdown')
app.add_template_filter(utils.access)
app.add_template_filter(utils.mode)

# Get the configuration.
dbshare.config.init(app)

# Initialize the subsystems.
dbshare.system.init(app)
dbshare.chart.init(app)
utils.mail.init_app(app)

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context of Jinja2 templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token,
                utils=utils,
                enumerate=enumerate,
                len=len,
                range=range,
                round=round)

@app.before_first_request
def set_schema_base_url():
    "Must be done after URL routes have been defined."
    dbshare.schema.set_base_url(utils.url_for('api_schema.schema'))

@app.before_request
def prepare():
    """Actions performed before every access.
    - Connect to the system database (read-only).
    - Get the current user.
    """
    flask.g.cnx = dbshare.system.get_cnx()
    flask.g.current_user = dbshare.user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user.get('role') == constants.ADMIN
    flask.g.timer = utils.Timer()

app.after_request(dbshare.system.log_access)

@app.route('/')
def home():
    "Home page; display the list of public databases."
    if utils.accept_json():
        return flask.redirect(flask.url_for('api.root'))
    return flask.render_template('home.html',
                                 dbs=dbshare.dbs.get_dbs(public=True))

# Set up the URL map.
app.register_blueprint(dbshare.db.blueprint, url_prefix='/db')
app.register_blueprint(dbshare.dbs.blueprint, url_prefix='/dbs')
app.register_blueprint(dbshare.table.blueprint, url_prefix='/table')
app.register_blueprint(dbshare.query.blueprint, url_prefix='/query')
app.register_blueprint(dbshare.view.blueprint, url_prefix='/view')
app.register_blueprint(dbshare.chart.blueprint, url_prefix='/chart')
app.register_blueprint(dbshare.user.blueprint, url_prefix='/user')
app.register_blueprint(dbshare.about.blueprint, url_prefix='/about')
app.register_blueprint(dbshare.site.blueprint, url_prefix='/site')

app.register_blueprint(dbshare.api.root.blueprint, url_prefix='/api')
app.register_blueprint(dbshare.api.db.blueprint, url_prefix='/api/db')
app.register_blueprint(dbshare.api.dbs.blueprint, url_prefix='/api/dbs')
app.register_blueprint(dbshare.api.table.blueprint, url_prefix='/api/table')
app.register_blueprint(dbshare.api.view.blueprint, url_prefix='/api/view')
app.register_blueprint(dbshare.api.chart.blueprint, url_prefix='/api/chart')
app.register_blueprint(dbshare.api.user.blueprint, url_prefix='/api/user')
app.register_blueprint(dbshare.api.users.blueprint, url_prefix='/api/users')
app.register_blueprint(dbshare.api.schema.blueprint, url_prefix='/api/schema')


# This code is used only during development.
if __name__ == '__main__':
    app.run()
