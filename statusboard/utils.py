import random
import sys

def hex_random(n):
    byte = lambda: '%02x'%random.randint(0, 255)
    return ''.join(byte() for _ in xrange(n))

def add_new_widget(grid, add_row, add_before):
    new_id = hex_random(4)
    for row in grid:
        for widget in row:
            if widget['id']  == new_id:
                # Duplicate ID, start over
                return add_new_widget(grid, add_row, add_after)
    new_widget = {'id': new_id}
    while add_row >= len(grid):
        grid.append([])
    for i, widget in enumerate(grid[add_row]):
        if widget['id'] == add_before:
            grid[add_row].insert(i, new_widget)
            return new_widget
    grid[add_row].append(new_widget)
    return new_widget

# Taken from Django with permission from/by the original author.
def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                              "package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]
