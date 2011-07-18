from __future__ import absolute_import
import types
import warnings

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet
from django.http import HttpResponse

# Find a JSON module to use
try: #pragma: no cover
    import json
except ImportError: #pragma: no cover
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

def maybe_call(x):
    if callable(x):
        return x()
    return x


class JSONEncoder(DjangoJSONEncoder):
    """Custom encoder to allow arbitrary model classes."""

    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return maybe_call(obj.to_dict)
        elif hasattr(obj, 'to_list'):
            return maybe_call(obj.to_list)
        elif isinstance(obj, (QuerySet, types.GeneratorType)):
            return list(obj)
        return super(JSONEncoder, self).default(obj)


load = json.load
loads = json.loads
dump = lambda obj: json.dump(obj, cls=JSONEncoder)
dumps = lambda obj: json.dumps(obj, cls=JSONEncoder)


class JSONResponse(HttpResponse):
    """JSON response wrapper."""
    def __init__(self, obj={}, *args, **kwargs):
        kwargs.setdefault('mimetype', 'application/json')
        if not isinstance(obj, dict):
            # Returning anything other than an object literal is a possible
            # security issue. http://flask.pocoo.org/docs/security/#json-security
            msg = 'Only dicts should be used with JSONResponse for security reasons.'
            if settings.DEBUG:
                raise ValueError(msg)
            else:
                warnings.warn(msg)
        super(JSONResponse, self).__init__(dumps(obj), *args, **kwargs)
