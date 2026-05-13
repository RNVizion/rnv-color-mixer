# Internal Developer Notes

This document captures implementation-level integration patterns for
internal utility modules. These notes are for contributors who are
extending or modifying the application's infrastructure — they are not
required reading for end users.

---

## Signal Connection Manager (`utils/signal_manager.py`)

The `SignalConnectionManager` class tracks Qt signal-slot connections so
they can be cleanly disconnected later, preventing memory leaks in
long-running sessions. The `SignalMixin` class provides the same
capability to any `QObject` subclass.

### Basic widget tracking

```python
class ColorMixerApp:
    def __init__(self):
        self.signal_manager = SignalConnectionManager()
    
    def add_color_slot(self):
        slot = ColorSlot()
        self.signal_manager.connect(slot, slot.color_changed, self.on_color_change)
        self.signal_manager.connect(slot, slot.remove_requested, self.remove_slot)
    
    def remove_color_slot(self, slot):
        self.signal_manager.disconnect_widget(slot)
        slot.deleteLater()
```

### Connections with tracking labels

Labels make debugging easier when inspecting active connections:

```python
self.signal_manager.connect(
    slot1, 
    slot1.color_changed, 
    self.on_color_change,
    track_as=f"color_slot_{len(self.slots)}"
)
```

### Application cleanup

Call `disconnect_all()` during the close event to release every tracked
connection before the Qt object tree is torn down:

```python
def closeEvent(self, event):
    logger.debug("Cleaning up signal connections...")
    self.signal_manager.print_stats()
    self.signal_manager.disconnect_all()
    self.signal_manager.verify_cleanup()
    super().closeEvent(event)
```

### Using the SignalMixin

For widgets that own their own connections, inherit from `SignalMixin`
and use `track_connection()` instead of `connect()`:

```python
class ColorSlot(QWidget, SignalMixin):
    def __init__(self):
        super().__init__()
        self.init_signal_tracking()
        
        self.track_connection(
            self.slider,
            self.slider.valueChanged,
            self.on_slider_change,
            label="weight_slider"
        )
    
    def closeEvent(self, event):
        self.cleanup_signals()
        super().closeEvent(event)
```

---

## QPixmap Cache (`utils/pixmap_cache.py`)

The `QPixmapCache` class provides an LRU cache of rendered QPixmaps
keyed by `(image_path, zoom_level, ...)`. The specialized
`ImagePixmapCache` subclass adds automatic invalidation when the source
image changes.

### Wiring the cache into ImageHandler

```python
class ImageHandler:
    def __init__(self):
        super().__init__()
        self.pixmap_cache = QPixmapCache(max_size=15)
        # or use the specialized variant:
        # self.pixmap_cache = ImagePixmapCache(max_size=15)
```

### Simple get-or-create pattern

```python
def get_display_pixmap(self, zoom_level: float) -> QPixmap:
    if not self.image:
        return None
    
    cache_key = (self.image_path, zoom_level, self.image.size)
    
    pixmap = self.pixmap_cache.get_or_create(
        cache_key,
        lambda: self._create_pixmap(zoom_level)
    )
    
    return pixmap
```

### Explicit get/put with hit-rate logging

When profiling, the `get()`/`put()` pair gives you finer control and
exposes the cache statistics:

```python
def get_display_pixmap(self, zoom_level: float) -> QPixmap:
    cache_key = (self.image_path, zoom_level, self.image.size)
    
    # Try cache first
    pixmap = self.pixmap_cache.get(cache_key)
    
    if pixmap:
        logger.success(f"Pixmap cache hit! (zoom: {zoom_level})")
        stats = self.pixmap_cache.get_stats()
        logger.debug(f"  Cache: {stats['size']}/{stats['max_size']}, "
                     f"Hit rate: {stats['hit_rate']:.1f}%")
    else:
        logger.error(f"Cache miss, creating pixmap (zoom: {zoom_level})")
        pixmap = self._create_pixmap(zoom_level)
        self.pixmap_cache.put(cache_key, pixmap)
    
    return pixmap
```

### Clearing the cache when a new image loads

```python
def load_image(self, path: str) -> bool:
    # ... load image ...
    
    # Clear old pixmaps
    cleared = self.pixmap_cache.clear()
    logger.debug(f"Cleared {cleared} cached pixmaps for new image")
    
    return True
```

### Using `ImagePixmapCache` (automatic invalidation)

```python
class ImageHandler:
    def __init__(self):
        self.pixmap_cache = ImagePixmapCache(max_size=15)
    
    def load_image(self, path: str):
        # Automatically clears old image's pixmaps
        self.pixmap_cache.set_current_image(path)
    
    def get_display_pixmap(self, zoom_level: float):
        return self.pixmap_cache.get_for_zoom(
            self.image_path,
            zoom_level,
            self.image.size,
            lambda: self._create_pixmap(zoom_level)
        )
```

### Monitoring cache performance

```python
# After some operations:
self.pixmap_cache.print_stats()
```

Example output:

```
==================================================
QPixmap Cache Statistics:
==================================================
  Cache Size:     8/10
  Cache Hits:     45
  Cache Misses:   8
  Hit Rate:       84.9%
  Evictions:      2
==================================================
```
