import requests


class DeezerAuthRejected(Exception):
    pass


class DeezerUnexpectedResponse(Exception):
    pass


class DeezerResponseError(Exception):
    def __init__(self, type_, message, code):
        super(DeezerResponseError, self).__init__()
        self.type = type_
        self.message = message
        self.code = code

    def __str__(self):
        return f'{self.type}: {self.message} ({self.message})'


def request(url, params, method='get'):
    response = requests.request(method, url, params=params)
    response.raise_for_status()
    json = response.json()

    if isinstance(json, bool):
        if not json:
            raise DeezerUnexpectedResponse(
                f'`{json}` response for url: `{url}` with params `{params}`'
            )
        return json

    error = json.get('error')
    if error:
        raise DeezerResponseError(
            type_=error.get('type'),
            message=error.get('message'),
            code=error.get('code'),
        )

    return json['data'] if 'data' in json else json
