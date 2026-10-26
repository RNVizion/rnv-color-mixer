# Internal Developer Notes

This document covers two of the internal utility modules: the signal
connection manager and the pixmap cache. These notes are for contributors
who are extending or modifying the application's infrastructure — they
are not required reading for end users. The examples are taken from the
application's own code.

---

## Signal Connection Manager (`utils/signal_manager.py`)

The `SignalConnectionManager` class tracks Qt signal-slot connections so
they can be cleanly disconnected later, preventing memory leaks in
long-running sessions. The `SignalMixin` class provides the same
capability to any `QObject` subclass.

### Tracking connections in the main window

`ColorMixerApp` makes one manager in `__init__` and tracks the signals it
connects from the canvas, the screen picker, the Settings & Features panel,
each color slot's remove request, and the application's
`styleHints().colorSchemeChanged`, which the Auto (follow system) theme
listens to. The style hints outlive every window, so a closed window must
let go of that one:

```python
self.signal_manager = SignalConnectionManager()

# In add_color_slot():
slot = ColorSlot(len(self.slots), self.on_slot_change)
self.signal_manager.connect(
    slot,
    slot.remove_requested,
    self.remove_color_slot,
    track_as=f"slot_{len(self.slots)}_remove"
)
```

The optional `track_as` label names the connection in the debug log and in
`list_connections()`. The other signals in the application are connected
directly with `connect()`.

When a slot is removed, `remove_color_slot()` disconnects that slot's
`remove_requested`, `color_changed` and `weight_changed` signals directly
and then calls `slot.deleteLater()`. `disconnect_widget(widget)` is the
manager's call for releasing every tracked connection of one widget.

### Application cleanup

The main window's `closeEvent` releases every tracked connection before
the Qt object tree is torn down:

```python
if hasattr(self, 'signal_manager') and self.signal_manager:
    disconnected = self.signal_manager.disconnect_all()
    logger.debug(f"SignalConnectionManager disconnected {disconnected} signals")
```

For debugging, `print_stats()` writes the connection counts to the log at
debug level, and `verify_cleanup()` returns `False` and logs each
connection still tracked.

### Using the SignalMixin

Widgets that own their own connections inherit from `SignalMixin` and use
`track_connection()` instead of `connect()`. `ColorSlot`, `CanvasView`,
`ScreenColorPicker`, `DebugOverlay` and `DebugOverlayDetailed` do this.
From `ColorSlot`:

```python
class ColorSlot(QWidget, SignalMixin):
    def __init__(self, index: int, on_change_callback: Callable | None = None):
        super().__init__()
        ...
        self.init_signal_tracking()
        ...
        self.track_connection(self.weight_slider, self.weight_slider.valueChanged,
                              self._on_weight_changed, "weight_changed")

    def cleanup(self):
        self.cleanup_signals()
        self.on_change = None
```

`CanvasView.cleanup()` also calls `cleanup_signals()`, and
`ScreenColorPicker` calls it when the picker closes.

---

## QPixmap Cache (`utils/pixmap_cache.py`)

The `QPixmapCache` class is an LRU cache of QPixmaps keyed by a tuple such
as `(image_path, zoom_level, image_size)`, with hit, miss and eviction
counts. The `ImagePixmapCache` subclass adds `set_current_image(path)`,
which clears the cache when the image changes, `get_for_zoom(...)`, and
`invalidate_image(path)`.

### How ImageHandler uses it

`ImageHandler` constructs an `ImagePixmapCache` and clears it, but the
display path does not read from it. What the canvas displays comes from a
single QImage cached for the current zoom level:

```python
# ImageHandler.__init__
self._cached_qimage = None
self._cached_zoom = None
if _pixmap_cache_available:
    self.pixmap_cache = ImagePixmapCache(max_size=15)
else:
    self.pixmap_cache = None

def clear_cache(self) -> None:
    """Clear all image caches (QImage and QPixmap)."""
    self._cached_qimage = None
    self._cached_zoom = None
    if self.pixmap_cache:
        cleared = self.pixmap_cache.clear()

def get_qimage(self) -> 'QImage | None':
    if not self.image:
        return None
    if (self._cached_qimage is not None and
        self._cached_zoom == self.zoom_level):
        return self._cached_qimage
    # ... resize with PIL, convert to an RGB888 QImage ...
    self._cached_qimage = qimage
    self._cached_zoom = self.zoom_level
    return qimage
```

`clear_cache()` runs when an image loads, when the zoom level changes, and
when the image is cleared. `CanvasView.display_image()` calls `get_qimage()`
and shows the result.

### Using the cache

On its own, the cache is used like this:

```python
from utils.pixmap_cache import ImagePixmapCache

cache = ImagePixmapCache(max_size=10)
cache.set_current_image(path)          # clears pixmaps of any other image

pixmap = cache.get_for_zoom(
    path,
    zoom_level,
    (width, height),                   # the original image size
    lambda: make_pixmap(zoom_level)    # called only on a miss
)

# The general form, for any key:
pixmap = cache.get_or_create((path, zoom_level, (width, height)),
                             lambda: make_pixmap(zoom_level))
```

`get()` and `put()` are there for finer control, and `get_stats()` returns
`size`, `max_size`, `hits`, `misses`, `hit_rate` and `evictions`.

### Monitoring cache performance

`print_stats()` writes the statistics to the log at debug level. After two
misses and one hit on a cache of 10:

```
DEBUG    | PixmapCache          | QPixmap Cache Statistics:
DEBUG    | PixmapCache          | ==================================================
DEBUG    | PixmapCache          |   Cache Size:     2/10
DEBUG    | PixmapCache          |   Cache Hits:     1
DEBUG    | PixmapCache          |   Cache Misses:   2
DEBUG    | PixmapCache          |   Hit Rate:       33.3%
DEBUG    | PixmapCache          |   Evictions:      0
DEBUG    | PixmapCache          | ==================================================
```
