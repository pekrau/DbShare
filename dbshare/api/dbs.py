"Database lists API endpoints."

import http.client

import flask
import flask_cors

import dbshare.dbs
import dbshare.user
from dbshare import utils


blueprint = flask.Blueprint("api_dbs", __name__)

flask_cors.CORS(blueprint, methods=["GET"])


@blueprint.route("/public")
def public():
    "Return the list of public databases."
    result = {
        "title": "Public databases",
        "databases": get_json(dbshare.dbs.get_dbs(public=True)),
    }
    return flask.jsonify(utils.get_json(**result))


@blueprint.route("/all")
@utils.admin_required
def all():
    "Return the list of all databases."
    dbs = dbshare.dbs.get_dbs()
    result = {
        "title": "All databases",
        "total_size": sum([db["size"] for db in dbs]),
        "databases": get_json(dbs),
    }
    return flask.jsonify(utils.get_json(**result))


@blueprint.route("/owner/<name:username>")
@utils.login_required
def owner(username):
    "Return the list of databases owned by the given user."
    if not dbshare.dbs.has_access(username):
        return flask.abort(http.client.UNAUTHORIZED)
    dbs = dbshare.dbs.get_dbs(owner=username)
    result = {
        "title": f"Databases owned by {username}",
        "user": dbshare.api.user.get_json(username),
        "total_size": sum([db["size"] for db in dbs]),
        "databases": get_json(dbs),
        "actions": [
            {
                "title": "Create a new empty database.",
                "href": utils.url_for_unq("api_db.database", dbname="{dbname}"),
                "variables": {"dbname": {"title": "Name of the database."}},
                "method": "PUT",
            }
        ]
    }
    return flask.jsonify(utils.get_json(**result))


def get_json(dbs):
    "Return JSON for the databases."
    result = []
    for db in dbs:
        result.append(
            {
                "name": db["name"],
                "href": utils.url_for("api_db.database", dbname=db["name"]),
                "title": db.get("title"),
                "description": db.get("description"),
                "owner": dbshare.api.user.get_json(db["owner"]),
                "public": db["public"],
                "readonly": db["readonly"],
                "size": db["size"],
                "modified": db["modified"],
                "created": db["created"],
                "hashes": db["hashes"],
            }
        )
    return result
