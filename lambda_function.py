"""
Generic Slack Inviter API lambda end-point.

Can be used by any slack team.

*WARNING*
Use on server-side. Do not expose your tokens in your client!

Accepts: {
    'team_name': <string>,
    'email': <email>,
    'token': <slack_api_token>  * unless token is in env
}

add *.dist-info to .gitignore
pip install -r requirements.txt --target=.
"""
import json
import os

from urlparse import parse_qs

from flask_lambda import FlaskLambda

import requests

app = FlaskLambda(__name__)


def convert_case(word):
    """Return Camel Case from snake_case."""
    words = [x.capitalize() or '_' for x in word.split('_')]
    return ''.join(words)


def extract_body(event):
    """Return json from the request body."""
    json_input = parse_qs(event['body'])
    for each in json_input.items():
        json_input[each[0]] = each[1][0]
    return json_input


def create_response(key, value):
    """Return generic AWS Lamba proxy response object format."""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({key: value})
    }


def validate_keys(json):
    """Check if json has the right keys, convert array values to non-array, return errors."""
    token = os.environ['token']  # optional token in env is used
    if token:
        json['token'] = token

    keys = ['team_name', 'email', 'token']
    errors = []
    for key in keys:
        if key not in json.keys():
            errors.append('no_{0}'.format(key))
    return errors


@app.route('/', methods=['POST'])
def lambda_handler(event, context):

    # flask-lambda returns just the data on test and returns the event on http request
    data = event
    if 'httpMethod' in event.keys():
        data = extract_body(event)

    # data validation
    errors = validate_keys(data)
    if errors:
        return create_response('error', errors)

    # slack API
    team_name = data.pop('team_name')
    url = "https://{0}.slack.com/api/users.admin.invite".format(team_name)
    r = requests.post(url, data=data)

    if not r.ok:  # did not work
        raise Exception(convert_case('api_error'))

    # it worked but there were errors, raise them as exceptions
    data = r.json()
    if 'ok' not in data.keys():
        exception = type(convert_case(data['error']), (Exception,), {})
        raise exception(data['error'])

    return create_response('result', data)  # it worked

if __name__ == '__main__':
    app.run(debug=True)
