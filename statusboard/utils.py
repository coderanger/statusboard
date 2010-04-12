import random

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

