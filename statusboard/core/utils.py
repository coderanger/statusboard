import hashlib
import random
import types

from django.conf import settings

from statusboard.utils import json

def hex_random(n):
    byte = lambda: '%02x'%random.randint(0, 255)
    return ''.join(byte() for _ in xrange(n))


def add_new_widget(grid, add_row, add_before):
    new_id = hex_random(4)
    for row in grid:
        for widget in row:
            if widget['id']  == new_id:
                # Duplicate ID, start over
                return add_new_widget(grid, add_row, add_before)
    new_widget = {'id': new_id}
    while add_row >= len(grid):
        grid.append([])
    for i, widget in enumerate(grid[add_row]):
        if widget['id'] == add_before:
            grid[add_row].insert(i, new_widget)
            return new_widget
    grid[add_row].append(new_widget)
    return new_widget


def guess_app(obj):
    if isinstance(obj, types.ModuleType):
        name = obj.__name__
    elif isinstance(obj, basestring):
        name = obj
    else:
        name = obj.__module__
    possibles = []
    for app in settings.INSTALLED_APPS:
        if name.startswith(app):
            possibles.append(app)
    return max(possibles, key=len)


def guess_app_label(obj):
    app = guess_app(obj)
    if app is not None:
        return app.rsplit('.', 1)[-1]


def json_hash(obj):
    return hashlib.sha1(json.dumps(obj)).hexdigest()
