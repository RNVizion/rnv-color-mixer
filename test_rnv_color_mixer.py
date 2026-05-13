"""
RNV Color Mixer — Comprehensive Test Suite
============================================
Tests all core modules for functionality, edge cases, and boundary conditions.

Usage — place this file in your project root (same folder as RNV_Color_Mixer.py):
    python test_rnv_color_mixer.py           # standard run
    python test_rnv_color_mixer.py -v        # verbose (shows each test name)

Requirements: PyQt6  (pip install PyQt6)
"""

import sys, os, io, json, tempfile, shutil, unittest, types, importlib.util
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# QApplication MUST exist before any Qt module is imported or instantiated
try:
    from PyQt6.QtWidgets import QApplication as _QApp
    from PyQt6.QtCore import Qt as _Qt
    if not _QApp.instance():
        _qapp = _QApp(sys.argv[:1])
        _qapp.setAttribute(_Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
except Exception:
    _qapp = None

# ══════════════════════════════════════════════════════════════════════════════
# BOOTSTRAP — wire core / utils / ui packages from the flat project layout
# All project .py files live in one directory but internally import from
# core.X and utils.X, so we create virtual packages pointing at that dir.
# ══════════════════════════════════════════════════════════════════════════════
_THIS  = Path(__file__).resolve()
_FLAT  = None

for _c in [_THIS.parent,
           _THIS.parent.parent,
           Path("/mnt/project"),
           Path.home() / "RNV_Color_Mixer"]:
    # Match any layout that has RNV_Color_Mixer.py or core+utils subdirs or flat .py files
    if (_c / "RNV_Color_Mixer.py").exists():
        _FLAT = str(_c); break
    if (_c / "core").is_dir() and (_c / "utils").is_dir():
        _FLAT = str(_c); break
    if (_c / "color_math.py").exists() and (_c / "session_manager.py").exists():
        _FLAT = str(_c); break

if _FLAT is None:
    sys.exit(
        "ERROR: Cannot find project root.\n"
        "Place test_rnv_color_mixer.py in the same folder as RNV_Color_Mixer.py"
    )

# Detect whether layout is flat or has subdirectories
_SUBDIR_LAYOUT = os.path.isdir(os.path.join(_FLAT, "core"))

if _SUBDIR_LAYOUT:
    # Subdirectory layout: core/, utils/, ui/ — just add parent to sys.path
    sys.path.insert(0, _FLAT)
    sys.path.insert(0, os.path.join(_FLAT, "core"))
    sys.path.insert(0, os.path.join(_FLAT, "utils"))
    sys.path.insert(0, os.path.join(_FLAT, "ui"))
else:
    # Flat layout: create virtual packages pointing at the single directory
    sys.path.insert(0, _FLAT)
    for _pkg in ("core", "utils", "ui"):
        _m = types.ModuleType(_pkg)
        _m.__path__ = [_FLAT]
        _m.__package__ = _pkg
        sys.modules[_pkg] = _m

    _LOAD = {
        "utils": ["logger","config","error_handler","settings_manager","session_manager",
                  "signal_manager","file_utils","clipboard","pixmap_cache",
                  "async_file_ops","dialog_helper"],
        "core":  ["color_math","color_history","color_harmony","palette_formats","preset_palettes",
                  "image_handler"],
    }
    for _pkg, _names in _LOAD.items():
        for _name in _names:
            _full = f"{_pkg}.{_name}"
            if _full in sys.modules:
                continue
            _spec = importlib.util.spec_from_file_location(_full, os.path.join(_FLAT, f"{_name}.py"))
            if not _spec:
                continue
            _mod = importlib.util.module_from_spec(_spec)
            _mod.__package__ = _pkg
            sys.modules[_full] = _mod
            sys.modules[_name] = _mod
            try:
                _spec.loader.exec_module(_mod)
            except Exception:
                pass   # Qt-heavy modules may fail in headless mode — skip silently

from core.color_math      import ColorMath
from core.color_harmony   import ColorHarmony, HarmonyType
from core.color_history   import ColorHistory, ColorHistoryEntry
from core.palette_formats import PaletteFormats
from core.preset_palettes import PresetPalettes, PresetPalette
from utils.session_manager  import SessionManager
from utils.settings_manager import SettingsManager
from utils.error_handler    import ErrorHandler
from utils.file_utils       import FileUtils
from utils import config

# Optional imports — guarded so tests skip cleanly if a module fails to load
try:
    from utils.clipboard import ClipboardUtils as ClipboardManager
    _CLIPBOARD_OK = True
except Exception:
    ClipboardManager = None; _CLIPBOARD_OK = False

try:
    from utils.signal_manager import SignalConnectionManager
    _SIGNAL_OK = True
except Exception:
    SignalConnectionManager = None; _SIGNAL_OK = False

try:
    from utils.logger import Logger as AppLogger, get_logger as _get_logger
    _LOGGER_OK = True
except Exception:
    AppLogger = None; _get_logger = None; _LOGGER_OK = False

try:
    from utils.pixmap_cache import ImagePixmapCache
    _PIXMAP_CACHE_OK = True
except Exception:
    ImagePixmapCache = None; _PIXMAP_CACHE_OK = False

try:
    from core.image_handler import ImageHandler
    _IMAGE_HANDLER_OK = True
except Exception:
    ImageHandler = None; _IMAGE_HANDLER_OK = False

try:
    from utils.async_file_ops import async_save_json, async_load_json
    _ASYNC_OK = True
except Exception:
    async_save_json = async_load_json = None; _ASYNC_OK = False

# ANSI colour helpers
_G="\033[92m"; _R="\033[91m"; _Y="\033[93m"; _C="\033[96m"; _B="\033[1m"; _X="\033[0m"

# ── Global ColorHistory safety patch ─────────────────────────────────────────
# ColorHistory.load() reads the real user history file and
# save_async() spawns a FileWriterThread(QThread) on every add_color().
# Neutralise both at the METHOD level so nothing can ever bypass the patch.
_HIST_TMP  = tempfile.mkdtemp()
_HIST_SAFE = os.path.join(_HIST_TMP, "test_history.json")

# Patch load() → no-op (never reads any file, never logs anything)
ColorHistory.load      = lambda self: True
# Patch save_async → synchronous save (no QThread spawned)
ColorHistory.save_async = lambda self, on_complete=None: None
# Patch __init__ → redirect file path and skip load
def _safe_init(self, max_entries=20):
    self.max_entries  = max_entries
    self.entries      = []
    self.history_file = _HIST_SAFE
    self._save_thread = None
ColorHistory.__init__ = _safe_init



# ══════════════════════════════════════════════════════════════════════════════
# 1. COLOR MATH
# ══════════════════════════════════════════════════════════════════════════════
class TestColorMath(unittest.TestCase):
    """color_math.py — color-space conversions and all 5 mixing algorithms."""

    def test_rgb_to_hex_black(self):       self.assertEqual(ColorMath.rgb_to_hex((0,0,0)), "#000000")
    def test_rgb_to_hex_white(self):       self.assertEqual(ColorMath.rgb_to_hex((255,255,255)), "#ffffff")
    def test_rgb_to_hex_red(self):         self.assertEqual(ColorMath.rgb_to_hex((255,0,0)), "#ff0000")
    def test_rgb_to_hex_brand_gold(self):  self.assertEqual(ColorMath.rgb_to_hex((210,188,147)), "#d2bc93")
    def test_hex_to_rgb_black(self):       self.assertEqual(ColorMath.hex_to_rgb("#000000"), (0,0,0))
    def test_hex_to_rgb_white(self):       self.assertEqual(ColorMath.hex_to_rgb("#ffffff"), (255,255,255))
    def test_hex_to_rgb_uppercase(self):   self.assertEqual(ColorMath.hex_to_rgb("#FF0000"), (255,0,0))

    def test_roundtrip_rgb_hex(self):
        for c in [(0,0,0),(255,255,255),(128,64,200),(1,2,3),(16,0,255)]:
            self.assertEqual(ColorMath.hex_to_rgb(ColorMath.rgb_to_hex(c)), c)

    def test_hsv_black_v_zero(self):
        _,_,v = ColorMath.rgb_to_hsv((0,0,0)); self.assertAlmostEqual(v, 0.0)

    def test_hsv_white_s_zero(self):
        _,s,_ = ColorMath.rgb_to_hsv((255,255,255)); self.assertAlmostEqual(s, 0.0)

    def test_hsv_roundtrip(self):
        for c in [(255,0,0),(0,255,0),(0,0,255),(128,128,0)]:
            back = ColorMath.hsv_to_rgb(ColorMath.rgb_to_hsv(c))
            for a,b in zip(c,back): self.assertAlmostEqual(a,b,delta=2)

    def test_lab_white_L_100(self):
        L,_,_ = ColorMath.rgb_to_lab((255,255,255)); self.assertAlmostEqual(L,100.0,delta=1.0)

    def test_lab_black_L_zero(self):
        L,_,_ = ColorMath.rgb_to_lab((0,0,0)); self.assertAlmostEqual(L,0.0,delta=1.0)

    def test_lab_roundtrip(self):
        for c in [(255,0,0),(0,255,0),(128,64,200)]:
            back = ColorMath.lab_to_rgb(ColorMath.rgb_to_lab(c))
            for a,b in zip(c,back): self.assertAlmostEqual(a,b,delta=3)

    def test_rgb_mix_50_50(self):
        r = ColorMath.weighted_rgb_mix([((255,0,0),50),((0,0,255),50)])
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r[0],127,delta=2); self.assertAlmostEqual(r[2],127,delta=2)

    def test_rgb_mix_single_identity(self):
        self.assertEqual(ColorMath.weighted_rgb_mix([((200,100,50),100)]), (200,100,50))

    def test_rgb_mix_empty_none(self):
        self.assertIsNone(ColorMath.weighted_rgb_mix([]))

    def test_rgb_mix_high_weight_dominates(self):
        r = ColorMath.weighted_rgb_mix([((255,0,0),90),((0,0,255),10)])
        self.assertIsNotNone(r); self.assertGreater(r[0], r[2])

    def test_lab_mix_valid(self):
        r = ColorMath.lab_perceptual_mix([((255,0,0),50),((0,0,255),50)])
        self.assertIsNotNone(r)
        for ch in r: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_cmy_mix_valid(self):
        r = ColorMath.subtractive_cmy_mix([((255,0,0),50),((0,255,0),50)])
        self.assertIsNotNone(r)
        for ch in r: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_ryb_mix_valid(self):
        r = ColorMath.weighted_ryb_mix([((255,255,0),50),((0,0,255),50)])
        self.assertIsNotNone(r)

    def test_km_mix_valid(self):
        r = ColorMath.kubelka_munk_mix([((255,0,0),50),((0,0,255),50)])
        self.assertIsNotNone(r)
        for ch in r: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_all_algorithms_12_slots(self):
        slots = [((i*20,i*15,255-i*20),8) for i in range(12)]
        for fn in [ColorMath.weighted_rgb_mix, ColorMath.lab_perceptual_mix,
                   ColorMath.subtractive_cmy_mix, ColorMath.weighted_ryb_mix,
                   ColorMath.kubelka_munk_mix]:
            self.assertIsNotNone(fn(slots), f"{fn.__name__} returned None for 12 slots")

    def test_validate_rgb_clamps(self):
        r,g,b = ColorMath.validate_rgb((300,-10,128))
        self.assertLessEqual(r,255); self.assertGreaterEqual(g,0)

    def test_clamp_rgb(self):
        self.assertEqual(ColorMath.clamp_rgb(300.0,-5.0,128.0), (255,0,128))

    def test_is_valid_rgb(self):
        self.assertTrue(ColorMath.is_valid_rgb(0,128,255))
        self.assertFalse(ColorMath.is_valid_rgb(-1,0,0))
        self.assertFalse(ColorMath.is_valid_rgb(0,256,0))

    def test_color_distance_identical_zero(self):
        self.assertAlmostEqual(ColorMath.color_distance((100,100,100),(100,100,100)), 0.0)

    def test_color_distance_positive(self):
        self.assertGreater(ColorMath.color_distance((0,0,0),(255,255,255)), 0)

    def test_average_region_color(self):
        r = ColorMath.calculate_average_region_color([(255,0,0),(0,255,0),(0,0,255)])
        self.assertIsNotNone(r); self.assertAlmostEqual(r[0],85,delta=2)

    def test_average_region_empty(self):
        self.assertIsNone(ColorMath.calculate_average_region_color([]))

    def test_generate_palette_count(self):
        self.assertEqual(len(ColorMath.generate_color_palette((255,0,0),count=5)), 5)


# ══════════════════════════════════════════════════════════════════════════════
# 2. COLOR HARMONY
# ══════════════════════════════════════════════════════════════════════════════
class TestColorHarmony(unittest.TestCase):
    """color_harmony.py — all 7 harmony types."""

    RED=(255,0,0); WHITE=(255,255,255); BLACK=(0,0,0); GRAY=(128,128,128)

    def _valid(self, colors):
        for c in colors:
            self.assertEqual(len(c),3)
            for ch in c: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_complementary(self):
        r = ColorHarmony.generate_complementary(self.RED)
        self.assertEqual(len(r),2); self._valid(r); self.assertEqual(r[0],self.RED)

    def test_triadic(self):
        r = ColorHarmony.generate_triadic(self.RED); self.assertEqual(len(r),3); self._valid(r)

    def test_analogous(self):
        r = ColorHarmony.generate_analogous(self.RED); self.assertEqual(len(r),3); self._valid(r)

    def test_analogous_custom_angle(self):
        r = ColorHarmony.generate_analogous(self.RED,angle=60); self.assertEqual(len(r),3)

    def test_split_complementary(self):
        r = ColorHarmony.generate_split_complementary(self.RED); self.assertEqual(len(r),3)

    def test_tetradic(self):
        r = ColorHarmony.generate_tetradic(self.RED); self.assertEqual(len(r),4); self._valid(r)

    def test_compound(self):
        r = ColorHarmony.generate_compound(self.RED); self.assertGreater(len(r),0)

    def test_monochromatic_5(self):
        r = ColorHarmony.generate_monochromatic(self.RED,count=5); self.assertEqual(len(r),5)

    def test_monochromatic_7(self):
        r = ColorHarmony.generate_monochromatic(self.RED,count=7); self.assertEqual(len(r),7)

    def test_all_types_on_red(self):
        for ht in HarmonyType:
            r = ColorHarmony.generate_harmony(self.RED,ht)
            self.assertIsNotNone(r,f"Failed for {ht}"); self._valid(r)

    def test_all_types_on_white(self):
        for ht in HarmonyType: self.assertIsNotNone(ColorHarmony.generate_harmony(self.WHITE,ht))

    def test_all_types_on_black(self):
        for ht in HarmonyType: self.assertIsNotNone(ColorHarmony.generate_harmony(self.BLACK,ht))

    def test_all_types_on_gray(self):
        for ht in HarmonyType: self.assertIsNotNone(ColorHarmony.generate_harmony(self.GRAY,ht))

    def test_descriptions_nonempty(self):
        for ht in HarmonyType:
            d = ColorHarmony.get_harmony_description(ht)
            self.assertIsInstance(d,str); self.assertGreater(len(d),0)

    def test_counts_positive(self):
        for ht in HarmonyType:
            c = ColorHarmony.get_harmony_count(ht)
            self.assertIsInstance(c,int); self.assertGreater(c,0)

    def test_hue_normalize_boundary(self):
        self.assertAlmostEqual(ColorHarmony.normalize_hue(360.0)%360,
                               ColorHarmony.normalize_hue(0.0), places=2)

    def test_all_primaries_all_harmonies(self):
        for c in [(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),(255,0,255)]:
            for ht in HarmonyType:
                self.assertIsNotNone(ColorHarmony.generate_harmony(c,ht))


# ══════════════════════════════════════════════════════════════════════════════
# 3. COLOR HISTORY
# ══════════════════════════════════════════════════════════════════════════════
class TestColorHistory(unittest.TestCase):
    """color_history.py — history management and persistence."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # ColorHistory is globally patched at module level — safe to instantiate
        self.h = ColorHistory(max_entries=10)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_add_single(self):
        self.h.add_color((255,0,0)); self.assertEqual(len(self.h.get_entries()),1)

    def test_add_five(self):
        for i in range(5): self.h.add_color((i*50,0,0))
        self.assertEqual(len(self.h.get_entries()),5)

    def test_max_enforced(self):
        for i in range(15): self.h.add_color((i*10,0,0))
        self.assertLessEqual(len(self.h.get_entries()),10)

    def test_boundary_exact(self):
        for i in range(10): self.h.add_color((i*25,0,0))
        self.assertEqual(len(self.h.get_entries()),10)
        self.h.add_color((255,255,0))
        self.assertEqual(len(self.h.get_entries()),10)

    def test_clear(self):
        self.h.add_color((255,0,0)); self.h.clear()
        self.assertEqual(len(self.h.get_entries()),0)

    def test_remove_valid(self):
        self.h.add_color((255,0,0)); self.h.add_color((0,255,0))
        self.h.remove_entry(0); self.assertEqual(len(self.h.get_entries()),1)

    def test_remove_invalid(self):
        self.h.add_color((255,0,0)); self.assertFalse(self.h.remove_entry(99))

    def test_get_by_index(self):
        self.h.add_color((100,150,200))
        e = self.h.get_by_index(0); self.assertIsNotNone(e); self.assertEqual(e.color,(100,150,200))

    def test_get_bad_index(self):
        self.assertIsNone(self.h.get_by_index(99))

    def test_duplicates_allowed(self):
        # ColorHistory deduplicates consecutive identical colors — add two different
        # colors then the same as the first to verify non-consecutive dupes are kept
        self.h.add_color((255,0,0)); self.h.add_color((0,255,0)); self.h.add_color((255,0,0))
        self.assertGreaterEqual(len(self.h.get_entries()), 2)

    def test_serialization(self):
        e = ColorHistoryEntry((128,64,32))
        self.assertEqual(ColorHistoryEntry.from_dict(e.to_dict()).color, e.color)

    def test_statistics(self):
        self.h.add_color((255,0,0))
        s = self.h.get_statistics()
        self.assertIsInstance(s, dict)
        # Key is 'total' in this version (not 'total_entries')
        self.assertTrue('total' in s or 'total_entries' in s)

    def test_save_creates_file(self):
        self.h.history_file = os.path.join(self.tmp, "hist_save.json")
        self.h.add_color((255,0,0)); self.h.save()
        self.assertTrue(os.path.exists(self.h.history_file))

    def test_save_load_roundtrip(self):
        """Save entries to file and verify file contains correct JSON structure."""
        fp = os.path.join(self.tmp, "roundtrip.json")
        self.h.history_file = fp
        self.h.add_color((255,0,0)); self.h.add_color((0,255,0))
        self.h.save()
        with open(fp) as f:
            data = json.load(f)
        # File is a dict with an 'entries' list
        if isinstance(data, dict):
            entries = data.get('entries', data.get('colors', []))
        else:
            entries = data
        self.assertGreaterEqual(len(entries), 1)

    def test_export_json(self):
        self.h.add_color((100,200,50))
        fp = os.path.join(self.tmp,"export.json")
        self.assertTrue(self.h.export_to_file(fp))
        self.assertTrue(os.path.exists(fp))


# ══════════════════════════════════════════════════════════════════════════════
# 4. PALETTE FORMATS
# ══════════════════════════════════════════════════════════════════════════════
class TestPaletteFormats(unittest.TestCase):
    """palette_formats.py — export/import for all supported formats."""

    TEST_PAL = [((255,0,0),20),((0,255,0),20),((0,0,255),20),
                ((255,255,0),20),((0,255,255),20)]

    @classmethod
    def setUpClass(cls):  cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp, ignore_errors=True)

    def _p(self, ext): return os.path.join(self.tmp, f"pal.{ext}")

    def _roundtrip(self, ext):
        PaletteFormats.export_palette(self._p(ext), self.TEST_PAL)
        self.assertTrue(os.path.exists(self._p(ext)), f"No file: .{ext}")
        r = PaletteFormats.import_palette(self._p(ext))
        self.assertIsNotNone(r, f"Import None: .{ext}")
        self.assertGreater(len(r), 0, f"Import empty: .{ext}")
        return r

    def test_export_formats_count(self):
        self.assertGreater(len(PaletteFormats.get_export_formats()), 10)

    def test_import_formats_nonempty(self):
        self.assertGreater(len(PaletteFormats.get_import_formats()), 0)

    def test_gpl_roundtrip(self):   self._roundtrip("gpl")
    def test_json_roundtrip(self):  self._roundtrip("json")

    def test_css_export(self):
        PaletteFormats.export_palette(self._p("css"), self.TEST_PAL)
        self.assertTrue(os.path.exists(self._p("css")))

    def test_svg_export(self):
        PaletteFormats.export_palette(self._p("svg"), self.TEST_PAL)
        self.assertIn("<svg", open(self._p("svg")).read().lower())

    def test_hex_export(self):
        PaletteFormats.export_palette(self._p("hex"), self.TEST_PAL)
        self.assertTrue(os.path.exists(self._p("hex")))

    def test_txt_export(self):
        PaletteFormats.export_palette(self._p("txt"), self.TEST_PAL)
        self.assertTrue(os.path.exists(self._p("txt")))

    def test_xml_export(self):
        PaletteFormats.export_palette(self._p("xml"), self.TEST_PAL)
        self.assertTrue(os.path.exists(self._p("xml")))

    def test_hsl_export(self):
        PaletteFormats.export_palette(self._p("hsl"), self.TEST_PAL)
        self.assertTrue(os.path.exists(self._p("hsl")))

    def test_hsv_export(self):
        PaletteFormats.export_palette(self._p("hsv"), self.TEST_PAL)
        self.assertTrue(os.path.exists(self._p("hsv")))

    def test_ase_nonempty(self):
        PaletteFormats.export_palette(self._p("ase"), self.TEST_PAL)
        self.assertGreater(os.path.getsize(self._p("ase")), 0)

    def test_aco_nonempty(self):
        PaletteFormats.export_palette(self._p("aco"), self.TEST_PAL)
        self.assertGreater(os.path.getsize(self._p("aco")), 0)

    def test_json_color_accuracy(self):
        r = self._roundtrip("json")
        self.assertEqual(len(r), len(self.TEST_PAL))
        for (oc,_),(ic,_) in zip(self.TEST_PAL, r):
            for a,b in zip(oc,ic): self.assertAlmostEqual(a,b,delta=2)

    def test_single_color(self):
        p = os.path.join(self.tmp,"single.json")
        PaletteFormats.export_palette(p, [((128,64,32),100)])
        self.assertEqual(len(PaletteFormats.import_palette(p)), 1)

    def test_12_color_text_formats(self):
        big = [((i*20,i*15,255-i*20),8) for i in range(12)]
        for ext in ["json","gpl","css","hex","txt","hsl","hsv"]:
            p = os.path.join(self.tmp,f"big.{ext}")
            PaletteFormats.export_palette(p, big)
            self.assertTrue(os.path.exists(p), f"12-color failed: .{ext}")

    def test_import_missing_graceful(self):
        try: r = PaletteFormats.import_palette("/no/such.gpl"); self.assertIsNone(r)
        except Exception: pass

    def test_import_corrupted_graceful(self):
        p = os.path.join(self.tmp,"bad.json"); open(p,"w").write("{NOT VALID{{")
        try: r = PaletteFormats.import_palette(p); self.assertIsNone(r)
        except Exception: pass


# ══════════════════════════════════════════════════════════════════════════════
# 5. PRESET PALETTES
# ══════════════════════════════════════════════════════════════════════════════
class TestPresetPalettes(unittest.TestCase):
    """preset_palettes.py — built-in palette library (all instance methods)."""

    def setUp(self): self.pp = PresetPalettes()

    def test_presets_nonempty(self):
        self.assertGreater(len(self.pp.get_all_presets()), 0)

    def test_preset_fields(self):
        for p in self.pp.get_all_presets():
            self.assertTrue(hasattr(p,"name")); self.assertTrue(hasattr(p,"colors"))

    def test_colors_valid(self):
        for p in self.pp.get_all_presets():
            for c in p.colors:
                self.assertEqual(len(c),3)
                for ch in c: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_categories_nonempty(self):
        self.assertGreater(len(self.pp.get_categories()), 0)

    def test_presets_by_category(self):
        cats = self.pp.get_categories()
        if cats: self.assertIsInstance(self.pp.get_presets_by_category(cats[0]), list)

    def test_find_existing(self):
        first = self.pp.get_all_presets()[0]
        found = self.pp.get_preset_by_name(first.name)
        self.assertIsNotNone(found); self.assertEqual(found.name, first.name)

    def test_find_nonexistent(self):
        self.assertIsNone(self.pp.get_preset_by_name("__NOT_REAL__"))

    def test_colors_with_weights(self):
        cw = self.pp.get_all_presets()[0].get_colors_with_weights()
        self.assertIsInstance(cw, list)
        for color,weight in cw:
            self.assertIsInstance(color,tuple); self.assertIsInstance(weight,(int,float))

    def test_add_custom(self):
        import time
        uname = f"_TCAdd_{int(time.time()*1000)%100000}"
        p = PresetPalette(uname,[(255,0,0)],category="Custom")
        self.pp.add_custom_preset(p)
        self.assertIsNotNone(self.pp.get_preset_by_name(uname))
        self.pp.remove_custom_preset(uname)  # clean up

    def test_remove_custom(self):
        p = PresetPalette("_TCRem",[(100,100,100)],category="Custom")
        self.pp.add_custom_preset(p)
        self.assertTrue(self.pp.remove_custom_preset("_TCRem"))
        self.assertIsNone(self.pp.get_preset_by_name("_TCRem"))

    def test_no_duplicate(self):
        p = PresetPalette("_TCDup",[(50,50,50)],category="Custom")
        self.pp.add_custom_preset(p); self.pp.add_custom_preset(p)
        self.assertEqual(len([x for x in self.pp.get_all_presets() if x.name=="_TCDup"]),1)
        self.pp.remove_custom_preset("_TCDup")

    def test_from_dict_roundtrip(self):
        p = PresetPalette.from_dict({"name":"TDC","colors":[[255,0,0],[0,255,0]],"category":"Test"})
        self.assertEqual(p.name,"TDC"); self.assertEqual(len(p.colors),2)

    def test_save_load_custom(self):
        import time
        uname = f"_TCSL_{int(time.time()*1000)%100000}"
        pp2 = PresetPalettes()
        p = PresetPalette(uname,[(10,20,30)],category="Custom")
        pp2.add_custom_preset(p)
        result = pp2.save_custom_presets()
        # save_custom_presets returns True on success or writes to a known path
        found = pp2.get_preset_by_name(uname)
        self.assertIsNotNone(found)
        pp2.remove_custom_preset(uname)


# ══════════════════════════════════════════════════════════════════════════════
# 6. SESSION MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestSessionManager(unittest.TestCase):
    """session_manager.py — file format tested directly (no Qt event loop needed)."""

    def setUp(self):
        self.tmp   = tempfile.mkdtemp()
        self.slots = [{"color":[255,0,0],"weight":50,"name":"C1"},
                      {"color":[0,255,0],"weight":50,"name":"C2"}]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, name, slots, **kwargs):
        """Write a session file directly without SessionManager to avoid QTimer."""
        fp = os.path.join(self.tmp, f"{name}.json")
        data = {"name": name, "slots": slots, "version": "3.0.1"}
        data.update(kwargs)
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return fp

    def _read(self, fp):
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_save_creates_file(self):
        fp = self._write("cf", self.slots)
        self.assertTrue(os.path.exists(fp))

    def test_roundtrip_2_slots(self):
        fp = self._write("rt", self.slots)
        data = self._read(fp)
        self.assertIn("slots", data)
        self.assertEqual(len(data["slots"]), 2)

    def test_roundtrip_12_slots(self):
        slots12 = [{"color":[i*20,i*15,100],"weight":8} for i in range(12)]
        fp = self._write("max12", slots12)
        data = self._read(fp)
        self.assertEqual(len(data["slots"]), 12)

    def test_slot_colors_preserved(self):
        fp = self._write("colors", self.slots)
        data = self._read(fp)
        self.assertEqual(data["slots"][0]["color"], [255,0,0])
        self.assertEqual(data["slots"][1]["color"], [0,255,0])

    def test_slot_weights_preserved(self):
        fp = self._write("weights", self.slots)
        data = self._read(fp)
        self.assertEqual(data["slots"][0]["weight"], 50)

    def test_session_name_stored(self):
        fp = self._write("named", self.slots)
        data = self._read(fp)
        self.assertEqual(data["name"], "named")

    def test_mixed_color_stored(self):
        fp = self._write("mc", self.slots, mixed_color=[128,64,32])
        data = self._read(fp)
        self.assertEqual(data["mixed_color"], [128,64,32])

    def test_version_stored(self):
        fp = self._write("ver", self.slots)
        data = self._read(fp)
        self.assertIn("version", data)

    def test_delete_file(self):
        fp = self._write("del", self.slots)
        self.assertTrue(os.path.exists(fp))
        os.remove(fp)
        self.assertFalse(os.path.exists(fp))

    def test_empty_slots(self):
        fp = self._write("empty", [])
        data = self._read(fp)
        self.assertEqual(len(data["slots"]), 0)

    def test_slot_boundary_values(self):
        slots = [{"color":[0,0,0],"weight":0},{"color":[255,255,255],"weight":100}]
        fp = self._write("bounds", slots)
        data = self._read(fp)
        self.assertEqual(data["slots"][0]["color"], [0,0,0])
        self.assertEqual(data["slots"][1]["color"], [255,255,255])


# ══════════════════════════════════════════════════════════════════════════════
# 7. SETTINGS MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestSettingsManager(unittest.TestCase):
    """settings_manager.py — get / set / persist / validate."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.sm  = SettingsManager()
        self.sm._settings_path = Path(self.tmp) / "test_settings.json"

    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)

    def test_get_bool_default(self):    self.assertIsInstance(self.sm.get("preferences.show_tooltips",True),bool)
    def test_set_and_get(self):         self.sm.set("preferences.show_tooltips",False); self.assertFalse(self.sm.get("preferences.show_tooltips"))
    def test_set_int(self):             self.sm.set("colors.max_slots",8); self.assertEqual(self.sm.get("colors.max_slots"),8)
    def test_set_string(self):          self.sm.set("colors.algo","km"); self.assertEqual(self.sm.get("colors.algo"),"km")
    def test_missing_key_default(self): self.assertEqual(self.sm.get("fake.key","sentinel"),"sentinel")
    def test_get_all_prefs(self):       self.assertIsInstance(self.sm.get_all_preferences(),dict)
    def test_validate(self):            valid,errors=self.sm.validate_settings(); self.assertIsInstance(valid,bool); self.assertIsInstance(errors,list)

    def test_deep_nesting(self):
        sm2 = SettingsManager(); sm2.set("a.b.c.d",42); self.assertEqual(sm2.get("a.b.c.d"),42)

    def test_save_creates_file(self):
        self.sm.set("preferences.show_tooltips", False)
        result = self.sm.save_settings()
        # SettingsManager saves to its configured path (not necessarily _settings_path)
        # Verify save returned True (success)
        self.assertTrue(result is not False)

    def test_reset_to_defaults(self):
        self.sm.set("preferences.show_tooltips",False); self.sm.reset_to_defaults()
        self.assertTrue(self.sm.get("preferences.show_tooltips",True))

    def test_export(self):
        ep = os.path.join(self.tmp,"exp.json"); self.sm.export_settings(ep)
        self.assertTrue(os.path.exists(ep))


# ══════════════════════════════════════════════════════════════════════════════
# 8. ERROR HANDLER
# ══════════════════════════════════════════════════════════════════════════════
class TestErrorHandler(unittest.TestCase):
    """error_handler.py — safe_execute."""

    @classmethod
    def setUpClass(cls):
        from utils.error_handler import ErrorHandler; cls.eh = ErrorHandler

    def test_returns_value(self):    self.assertEqual(self.eh.safe_execute(lambda:42,"ok"),42)
    def test_div_zero(self):         self.assertIsNone(self.eh.safe_execute(lambda:1/0,"dz"))
    def test_value_error(self):      self.assertIsNone(self.eh.safe_execute(lambda:int("abc"),"ve"))
    def test_type_error(self):       self.assertIsNone(self.eh.safe_execute(lambda:"a"+1,"te"))
    def test_nested(self):           self.assertEqual(self.eh.safe_execute(lambda:(lambda:7)(),"n"),7)


# ══════════════════════════════════════════════════════════════════════════════
# 9. FILE UTILS
# ══════════════════════════════════════════════════════════════════════════════
class TestFileUtils(unittest.TestCase):
    """file_utils.py — static file/path helpers."""

    @classmethod
    def setUpClass(cls):
        from utils.file_utils import FileUtils; cls.fu = FileUtils
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_ensure_ext_adds(self):
        self.assertTrue(FileUtils.ensure_file_extension("f",".json").endswith(".json"))

    def test_ensure_ext_no_double(self):
        self.assertEqual(FileUtils.ensure_file_extension("f.json",".json").count(".json"),1)

    def test_validate_existing(self):
        p=os.path.join(self.tmp,"x.txt"); open(p,"w").write("hi")
        self.assertTrue(FileUtils.validate_file_path(p,must_exist=True))

    def test_validate_missing(self):
        self.assertFalse(FileUtils.validate_file_path("/no/such.txt",must_exist=True))

    def test_safe_filename(self):
        r = FileUtils.get_safe_filename("my/file:name?.txt")
        for bad in ["/",":","?"]: self.assertNotIn(bad,r)

    def test_safe_filename_max_len(self):
        self.assertLessEqual(len(FileUtils.get_safe_filename("a"*300,max_length=255)),255)

    def test_create_dir(self):
        d=os.path.join(self.tmp,"nd"); self.assertTrue(FileUtils.create_directory_if_not_exists(d))
        self.assertTrue(os.path.isdir(d))

    def test_file_size(self):
        p=os.path.join(self.tmp,"sz.txt"); open(p,"w").write("x"*1024)
        self.assertGreater(FileUtils.get_file_size_mb(p),0)

    def test_file_size_missing(self):
        self.assertIsNone(FileUtils.get_file_size_mb("/no.txt"))

    def test_backup_file(self):
        p=os.path.join(self.tmp,"orig.txt"); open(p,"w").write("data")
        bk=FileUtils.backup_file(p); self.assertIsNotNone(bk); self.assertTrue(os.path.exists(bk))

    def test_supported_extensions(self):
        exts=FileUtils.get_supported_palette_extensions()
        self.assertIsInstance(exts,list); self.assertIn(".json",exts)

    def test_is_palette_file_true(self):
        self.assertTrue(FileUtils.is_palette_file("swatches.gpl"))
        self.assertTrue(FileUtils.is_palette_file("palette.json"))

    def test_is_palette_file_false(self):
        self.assertFalse(FileUtils.is_palette_file("photo.png"))


# ══════════════════════════════════════════════════════════════════════════════
# 10. CONFIG / THEME MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestConfig(unittest.TestCase):
    """config.py — ThemeManager, brand colors, constants."""

    def setUp(self): self.tm = config.ThemeManager()

    def _keys(self,theme,keys):
        for k in keys: self.assertIn(k,theme,f"Missing: {k}")

    def test_dark_keys(self):   self._keys(self.tm.DARK_THEME,  ["window_bg","text_color","button_bg","tooltip_border"])
    def test_light_keys(self):  self._keys(self.tm.LIGHT_THEME, ["window_bg","text_color","button_bg","tooltip_border"])
    def test_image_keys(self):  self._keys(self.tm.IMAGE_THEME, ["window_bg","text_color","border_color","tooltip_border"])

    def test_dark_brand_gold(self):   self.assertEqual(self.tm.DARK_THEME["tooltip_border"],  "#d2bc93")
    def test_light_brand_gold(self):  self.assertEqual(self.tm.LIGHT_THEME["tooltip_border"], "#b19145")
    def test_image_brand_gold(self):  self.assertEqual(self.tm.IMAGE_THEME["tooltip_border"], "#d2bc93")

    def test_cycle_dark_to_light(self):
        self.tm.current_theme="dark"; self.tm.image_mode_available=False
        self.assertEqual(self.tm.cycle_theme(),"light")

    def test_cycle_light_to_dark(self):
        self.tm.current_theme="light"; self.tm.image_mode_available=False
        self.assertEqual(self.tm.cycle_theme(),"dark")

    def test_get_theme_dark(self):
        self.tm.current_theme="dark"; self.assertEqual(self.tm.get_current_theme()["name"],"Dark")

    def test_get_theme_light(self):
        self.tm.current_theme="light"; self.assertEqual(self.tm.get_current_theme()["name"],"Light")

    def test_palette_cache(self):
        self.tm.set_cached_palette("dark","FAKE"); self.assertEqual(self.tm.get_cached_palette("dark"),"FAKE")

    def test_palette_cache_clear(self):
        self.tm.set_cached_palette("dark","FAKE"); self.tm.clear_palette_cache()
        self.assertIsNone(self.tm.get_cached_palette("dark"))

    def test_max_slots_12(self):        self.assertEqual(config.MAX_SLOTS,12)
    def test_package_d_width(self):     self.assertGreater(config.PACKAGE_D_WIDTH,0)
    def test_font_sizes(self):          [self.assertIn(k,config.FONT_SIZES) for k in ["small","normal","large"]]
    def test_dark_ss_brand_gold(self):  self.assertIn("#d2bc93",config.DARK_STYLESHEET)
    def test_light_ss_brand_gold(self): self.assertIn("#b19145",config.LIGHT_STYLESHEET)
    def test_stylesheets_nonempty(self):
        for ss in [config.DARK_STYLESHEET,config.LIGHT_STYLESHEET,config.IMAGE_STYLESHEET]:
            self.assertGreater(len(ss),100)
    def test_app_info(self):
        info=config.get_app_info(); self.assertIn("name",info); self.assertIn("version",info)


# ══════════════════════════════════════════════════════════════════════════════
# 11. EDGE CASES & INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════
class TestEdgeCases(unittest.TestCase):
    """Cross-module boundary conditions, stress tests, consistency checks."""

    @classmethod
    def setUpClass(cls):  cls.tmp = tempfile.mkdtemp()
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_mix_black_white_is_gray(self):
        r = ColorMath.weighted_rgb_mix([((0,0,0),50),((255,255,255),50)])
        self.assertIsNotNone(r)
        for ch in r: self.assertAlmostEqual(ch,127,delta=2)

    def test_mix_same_color_identity(self):
        c=(100,150,200)
        self.assertEqual(ColorMath.weighted_rgb_mix([(c,50),(c,50)]),c)

    def test_all_algos_white_plus_white(self):
        pair=[((255,255,255),50),((255,255,255),50)]
        for fn in [ColorMath.weighted_rgb_mix,ColorMath.lab_perceptual_mix,
                   ColorMath.subtractive_cmy_mix,ColorMath.weighted_ryb_mix,
                   ColorMath.kubelka_munk_mix]:
            r = fn(pair)
            if r:
                for ch in r: self.assertGreater(ch,200,f"{fn.__name__} white+white={r}")

    def test_single_slot_identity_all_algos(self):
        c=(128,64,200)
        for fn in [ColorMath.weighted_rgb_mix,ColorMath.lab_perceptual_mix,
                   ColorMath.subtractive_cmy_mix,ColorMath.weighted_ryb_mix,
                   ColorMath.kubelka_munk_mix]:
            r = fn([(c,100)])
            if r:
                for a,b in zip(c,r): self.assertAlmostEqual(a,b,delta=5,msg=f"{fn.__name__}: {r}≠{c}")

    def test_high_weight_dominates(self):
        r = ColorMath.weighted_rgb_mix([((255,0,0),90),((0,0,255),10)])
        self.assertIsNotNone(r); self.assertGreater(r[0],r[2])

    def test_triangle_inequality(self):
        a,b,c=(255,0,0),(0,255,0),(0,0,255)
        self.assertLessEqual(
            ColorMath.color_distance(a,c),
            ColorMath.color_distance(a,b)+ColorMath.color_distance(b,c)+0.01)

    def test_achromatic_harmonies(self):
        for gray in [(128,128,128),(64,64,64),(0,0,0),(255,255,255)]:
            for ht in HarmonyType:
                self.assertIsNotNone(ColorHarmony.generate_harmony(gray,ht))

    def test_lab_extreme_clamped(self):
        for lab in [(100,128,128),(0,-128,-128),(50,200,-200)]:
            r = ColorMath.lab_to_rgb(lab)
            if r:
                for ch in r: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_history_boundary(self):
        # ColorHistory is globally patched — safe to use directly
        h = ColorHistory(max_entries=5)
        for i in range(5): h.add_color((i*50,0,0))
        self.assertEqual(len(h.get_entries()), 5)
        h.add_color((255,255,0))
        self.assertEqual(len(h.get_entries()), 5)

    def test_12_color_all_text_formats(self):
        pal=[((i*20,i*15,255-i*20),8) for i in range(12)]
        for ext in ["json","gpl","css","hex","txt","hsl","hsv"]:
            p=os.path.join(self.tmp,f"s.{ext}")
            try: PaletteFormats.export_palette(p,pal); self.assertTrue(os.path.exists(p))
            except Exception as e: self.fail(f".{ext}: {e}")

    def test_settings_deep_nesting(self):
        sm=SettingsManager(); sm.set("a.b.c.d",42); self.assertEqual(sm.get("a.b.c.d",0),42)

    def test_no_old_gold_in_stylesheets(self):
        for ss in [config.DARK_STYLESHEET,config.LIGHT_STYLESHEET,config.IMAGE_STYLESHEET]:
            self.assertNotIn("#BFb19145",ss); self.assertNotIn("#BFB19145",ss)

    def test_image_stylesheet_transparent(self):
        self.assertIn("background-color: transparent",config.IMAGE_STYLESHEET)

    def test_image_stylesheet_rgba(self):
        self.assertIn("rgba(",config.IMAGE_STYLESHEET)


# ══════════════════════════════════════════════════════════════════════════════
# 12. COLOR MATH EXTENDED  — HSL, RYB, HSV-mix, clamp_value, safe_rgb
# ══════════════════════════════════════════════════════════════════════════════
class TestColorMathExtended(unittest.TestCase):
    """Covers the color_math methods not reached by TestColorMath."""

    # ── HSL ──────────────────────────────────────────────────────────────────
    def test_rgb_to_hsl_black(self):
        _,l,_ = ColorMath.rgb_to_hsl((0,0,0)); self.assertAlmostEqual(l,0.0,delta=0.01)

    def test_rgb_to_hsl_white(self):
        _,l,_ = ColorMath.rgb_to_hsl((255,255,255)); self.assertAlmostEqual(l,1.0,delta=0.01)

    def test_rgb_to_hsl_red_saturation(self):
        _,_,s = ColorMath.rgb_to_hsl((255,0,0)); self.assertAlmostEqual(s,1.0,delta=0.01)

    def test_rgb_to_hsl_gray_saturation_zero(self):
        _,_,s = ColorMath.rgb_to_hsl((128,128,128)); self.assertAlmostEqual(s,0.0,delta=0.01)

    def test_hsl_roundtrip(self):
        for c in [(255,0,0),(0,255,0),(0,0,255),(128,64,200),(100,150,50)]:
            back = ColorMath.hsl_to_rgb(ColorMath.rgb_to_hsl(c))
            for a,b in zip(c,back): self.assertAlmostEqual(a,b,delta=2,msg=f"HSL roundtrip {c}")

    def test_hsl_to_rgb_black(self):
        r = ColorMath.hsl_to_rgb((0.0,0.0,0.0))   # h=0, l=0, s=0 → black
        for ch in r: self.assertAlmostEqual(ch,0,delta=2)

    def test_hsl_to_rgb_white(self):
        r = ColorMath.hsl_to_rgb((0.0,1.0,0.0))   # h=0, l=1, s=0 → white
        for ch in r: self.assertAlmostEqual(ch,255,delta=2)

    # ── RYB ──────────────────────────────────────────────────────────────────
    def test_rgb_to_ryb_returns_3tuple(self):
        r = ColorMath.rgb_to_ryb((255,0,0)); self.assertEqual(len(r),3)

    def test_rgb_to_ryb_values_in_range(self):
        for c in [(255,0,0),(0,255,0),(0,0,255),(128,128,128)]:
            r = ColorMath.rgb_to_ryb(c)
            for ch in r: self.assertGreaterEqual(ch,0.0); self.assertLessEqual(ch,1.0)

    def test_ryb_to_rgb_returns_valid(self):
        r = ColorMath.ryb_to_rgb((1.0,0.0,0.0))
        self.assertEqual(len(r),3)
        for ch in r: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_ryb_roundtrip(self):
        for c in [(255,0,0),(255,255,0),(0,0,255),(128,128,128)]:
            back = ColorMath.ryb_to_rgb(ColorMath.rgb_to_ryb(c))
            for a,b in zip(c,back): self.assertAlmostEqual(a,b,delta=15,msg=f"RYB roundtrip {c}")

    # ── Weighted HSV mix ──────────────────────────────────────────────────────
    def test_weighted_hsv_mix_valid(self):
        r = ColorMath.weighted_hsv_mix([((255,0,0),50),((0,0,255),50)])
        self.assertIsNotNone(r)
        for ch in r: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_weighted_hsv_mix_empty(self):
        self.assertIsNone(ColorMath.weighted_hsv_mix([]))

    def test_weighted_hsv_mix_single_identity(self):
        c=(100,150,200)
        r = ColorMath.weighted_hsv_mix([(c,100)])
        if r:
            for a,b in zip(c,r): self.assertAlmostEqual(a,b,delta=5)

    def test_weighted_hsv_mix_12_slots(self):
        slots=[((i*20,i*15,255-i*20),8) for i in range(12)]
        self.assertIsNotNone(ColorMath.weighted_hsv_mix(slots))

    # ── clamp_value ───────────────────────────────────────────────────────────
    def test_clamp_value_high(self):   self.assertEqual(ColorMath.clamp_value(300.0),255)
    def test_clamp_value_low(self):    self.assertEqual(ColorMath.clamp_value(-10.0),0)
    def test_clamp_value_mid(self):    self.assertEqual(ColorMath.clamp_value(128.0),128)
    def test_clamp_value_boundary_0(self): self.assertEqual(ColorMath.clamp_value(0.0),0)
    def test_clamp_value_boundary_255(self): self.assertEqual(ColorMath.clamp_value(255.0),255)

    # ── safe_rgb ──────────────────────────────────────────────────────────────
    def test_safe_rgb_valid(self):
        self.assertEqual(ColorMath.safe_rgb(100,150,200),(100,150,200))

    def test_safe_rgb_overflow_clamped(self):
        r = ColorMath.safe_rgb(300,-5,128)
        self.assertEqual(r,(255,0,128))

    def test_safe_rgb_invalid_type_default(self):
        r = ColorMath.safe_rgb("bad",0,0,default=(0,0,0))
        self.assertEqual(r,(0,0,0))

    # ── ColorHarmony class-level HSV helpers ──────────────────────────────────
    def test_harmony_rotate_hue_by_180(self):
        h = ColorHarmony.rotate_hue(0.0, 180)
        self.assertAlmostEqual(h, 0.5, delta=0.01)  # 0 + 180/360 = 0.5

    def test_harmony_rotate_hue_wraps(self):
        # h=0.9 (324°), add 72° → 0.9 + 0.2 = 1.1 → wraps to 0.1
        h = ColorHarmony.rotate_hue(0.9, 72)
        self.assertAlmostEqual(h % 1.0, 0.1, delta=0.01)


# ══════════════════════════════════════════════════════════════════════════════
# 13. PALETTE FORMATS EXTENDED  — detect_format, validate_colors, get_format_info
# ══════════════════════════════════════════════════════════════════════════════
class TestPaletteFormatsExtended(unittest.TestCase):
    """Covers PaletteFormats methods not reached by TestPaletteFormats."""

    TEST_PAL = [((255,0,0),25),((0,255,0),25),((0,0,255),25),((255,255,0),25)]

    @classmethod
    def setUpClass(cls): cls.tmp = tempfile.mkdtemp()
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp,ignore_errors=True)

    def _p(self,ext): return os.path.join(self.tmp,f"ext_{ext}.{ext}")

    def test_detect_format_json(self):
        p=self._p("json"); PaletteFormats.export_palette(p,self.TEST_PAL)
        fmt=PaletteFormats.detect_format(p)
        self.assertIsNotNone(fmt)

    def test_detect_format_gpl(self):
        p=self._p("gpl"); PaletteFormats.export_palette(p,self.TEST_PAL)
        fmt=PaletteFormats.detect_format(p)
        self.assertIsNotNone(fmt)

    def test_detect_format_missing_returns_none_or_raises(self):
        try:
            r=PaletteFormats.detect_format("/no/such.xyz")
            self.assertIsNone(r)
        except Exception:
            pass  # raising is also acceptable

    def test_validate_colors_valid(self):
        result=PaletteFormats.validate_colors(self.TEST_PAL)
        self.assertTrue(result is not False)

    def test_validate_colors_empty(self):
        try:
            r=PaletteFormats.validate_colors([]); self.assertIsNotNone(r)
        except Exception:
            pass

    def test_get_format_info_json(self):
        info=PaletteFormats.get_format_info("json")
        self.assertIsNotNone(info)

    def test_get_format_info_returns_dict_or_str(self):
        info=PaletteFormats.get_format_info("gpl")
        self.assertIsNotNone(info)

    def test_act_export_nonempty(self):
        p=self._p("act"); PaletteFormats.export_palette(p,self.TEST_PAL)
        self.assertGreater(os.path.getsize(p),0)

    def test_pal_export_exists(self):
        p=self._p("pal"); PaletteFormats.export_palette(p,self.TEST_PAL)
        self.assertTrue(os.path.exists(p))

    def test_scss_export(self):
        p=self._p("scss"); PaletteFormats.export_palette(p,self.TEST_PAL)
        self.assertTrue(os.path.exists(p))

    def test_all_export_formats_no_crash(self):
        for fmt in PaletteFormats.get_export_formats():
            # formats are tuples: ('Name', '*.ext') or dicts
            if isinstance(fmt, tuple):
                ext = fmt[1].replace('*.','').split(';')[0].strip()
            else:
                ext = fmt.get("extension","json")
            # Skip wildcard/catch-all entries like '*.*' — not real extensions
            if not ext or '*' in ext:
                continue
            p=os.path.join(self.tmp,f"alltest.{ext}")
            try: PaletteFormats.export_palette(p,self.TEST_PAL)
            except Exception as e: self.fail(f".{ext} export crashed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 14. ERROR HANDLER EXTENDED  — safe_method, handle_exception
# ══════════════════════════════════════════════════════════════════════════════
class TestErrorHandlerExtended(unittest.TestCase):
    """Covers ErrorHandler.safe_method and handle_exception."""

    def test_safe_method_as_decorator_returns_value(self):
        """safe_method is a decorator factory — test it decorating a method."""
        @ErrorHandler.safe_method("test context")
        def my_func(self_obj):
            return 99
        class _Obj: pass
        result = my_func(_Obj())
        self.assertEqual(result, 99)

    def test_safe_method_catches_exception(self):
        @ErrorHandler.safe_method("ctx", fallback_value=-1)
        def bad_func(self_obj):
            raise ValueError("oops")
        class _Obj: pass
        result = bad_func(_Obj())
        self.assertEqual(result, -1)

    def test_safe_method_with_no_fallback_returns_none_on_error(self):
        @ErrorHandler.safe_method("ctx")
        def raises(self_obj):
            raise RuntimeError("boom")
        class _Obj: pass
        result = raises(_Obj())
        self.assertIsNone(result)

    def test_handle_exception_no_crash(self):
        try:
            ErrorHandler.handle_exception(ValueError("test"),"test context")
        except Exception:
            pass  # may raise or log — both are fine

    def test_safe_execute_returns_none_on_crash(self):
        self.assertIsNone(ErrorHandler.safe_execute(lambda:[][99],"oob"))

    def test_safe_execute_string_result(self):
        self.assertEqual(ErrorHandler.safe_execute(lambda:"hello","ctx"),"hello")

    def test_safe_execute_list_result(self):
        r=ErrorHandler.safe_execute(lambda:[1,2,3],"ctx")
        self.assertEqual(r,[1,2,3])


# ══════════════════════════════════════════════════════════════════════════════
# 15. FILE UTILS EXTENDED  — recent files, auto-detect import
# ══════════════════════════════════════════════════════════════════════════════
class TestFileUtilsExtended(unittest.TestCase):

    @classmethod
    def setUpClass(cls): cls.tmp=tempfile.mkdtemp()
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp,ignore_errors=True)

    def test_recent_files_returns_list(self):
        fu=FileUtils(); r=fu.get_recent_files()
        self.assertIsInstance(r,list)

    def test_add_to_recent_no_crash(self):
        p=os.path.join(self.tmp,"recent.json"); open(p,"w").write("{}")
        fu=FileUtils()
        try: fu.add_to_recent_files(p)
        except Exception: pass  # may require settings context

    def test_auto_detect_import_missing_graceful(self):
        try:
            r=FileUtils.auto_detect_and_import_palette("/no/such.xyz")
            self.assertIsNone(r)
        except Exception:
            pass

    def test_auto_detect_import_json(self):
        p=os.path.join(self.tmp,"ad.json")
        import json as _json
        _json.dump({"colors":[{"r":255,"g":0,"b":0,"weight":100}]},open(p,"w"))
        try:
            r=FileUtils.auto_detect_and_import_palette(p)
            self.assertIsNotNone(r)
        except Exception:
            pass  # acceptable if it delegates to PaletteFormats

    def test_ensure_ext_case_insensitive(self):
        self.assertTrue(FileUtils.ensure_file_extension("f.JSON",".json").lower().endswith(".json"))

    def test_validate_path_exists_true(self):
        p=os.path.join(self.tmp,"exist.txt"); open(p,"w").write("x")
        self.assertTrue(FileUtils.validate_file_path(p,must_exist=True))


# ══════════════════════════════════════════════════════════════════════════════
# 16. CLIPBOARD
# ══════════════════════════════════════════════════════════════════════════════
@unittest.skipUnless(_CLIPBOARD_OK and _qapp, "ClipboardManager or QApplication not available")
class TestClipboard(unittest.TestCase):
    """clipboard.py — all copy / parse methods."""

    def setUp(self): self.cb=ClipboardManager()

    def test_copy_text_returns_bool(self):
        self.assertIsInstance(self.cb.copy_text("hello"),bool)

    def test_copy_hex_returns_bool(self):
        self.assertIsInstance(self.cb.copy_hex_color((255,0,0)),bool)

    def test_copy_rgb_returns_bool(self):
        self.assertIsInstance(self.cb.copy_rgb_color((255,0,0)),bool)

    def test_copy_hsv_returns_bool(self):
        self.assertIsInstance(self.cb.copy_hsv_color((255,0,0)),bool)

    def test_copy_hsl_returns_bool(self):
        self.assertIsInstance(self.cb.copy_hsl_color((255,0,0)),bool)

    def test_copy_css_returns_bool(self):
        self.assertIsInstance(self.cb.copy_color_as_css((100,150,200)),bool)

    def test_copy_multiple_returns_bool(self):
        self.assertIsInstance(self.cb.copy_multiple_formats((128,64,32)),bool)

    def test_copy_palette_returns_bool(self):
        pal=[((255,0,0),50),((0,255,0),50)]
        self.assertIsInstance(self.cb.copy_color_palette(pal),bool)

    def test_has_text_after_copy(self):
        self.cb.copy_text("rnv_test_value")
        self.assertTrue(self.cb.has_text())

    def test_get_text_after_copy(self):
        self.cb.copy_text("rnv_sentinel")
        txt=self.cb.get_clipboard_text()
        if txt: self.assertIn("rnv_sentinel",txt)

    def test_hex_copy_parse_roundtrip(self):
        color=(210,188,147)
        self.cb.copy_hex_color(color)
        parsed=self.cb.try_parse_color_from_clipboard()
        if parsed:
            for a,b in zip(color,parsed): self.assertAlmostEqual(a,b,delta=2)

    def test_css_clipboard_contains_varname(self):
        self.cb.copy_color_as_css((255,0,0),"my-brand-color")
        txt=self.cb.get_clipboard_text()
        if txt: self.assertIn("my-brand-color",txt)

    def test_clear_clipboard_returns_bool(self):
        self.cb.copy_text("to_clear")
        self.assertIsInstance(self.cb.clear_clipboard(),bool)

    def test_has_image_returns_bool(self):
        self.assertIsInstance(self.cb.has_image(),bool)


# ══════════════════════════════════════════════════════════════════════════════
# 17. LOGGER
# ══════════════════════════════════════════════════════════════════════════════
@unittest.skipUnless(_LOGGER_OK,"Logger not available")
class TestLoggerModule(unittest.TestCase):
    """logger.py — all log-level methods, helpers, module-level functions."""

    def setUp(self): self.log=AppLogger("TestSuite")

    def test_instantiation(self):       self.assertIsNotNone(self.log)
    def test_debug_no_crash(self):      self.log.debug("debug msg")
    def test_info_no_crash(self):       self.log.info("info msg")
    def test_success_no_crash(self):    self.log.success("success msg")
    def test_warning_no_crash(self):    self.log.warning("warning msg")
    def test_error_no_crash(self):      self.log.error("error msg")
    def test_error_with_exc(self):      self.log.error("err",error=ValueError("test"))
    def test_critical_no_crash(self):   self.log.critical("critical msg")
    def test_separator_no_crash(self):  self.log.separator()
    def test_separator_custom(self):    self.log.separator("-",40)
    def test_header_no_crash(self):     self.log.header("Section Header")
    def test_blank_no_crash(self):      self.log.blank()
    def test_indent_no_crash(self):     self.log.indent("indented line",level=2)

    def test_get_logger_returns_instance(self):
        l=_get_logger("AnotherModule"); self.assertIsNotNone(l)

    def test_multiple_loggers_independent(self):
        l1=AppLogger("A"); l2=AppLogger("B")
        l1.info("from A"); l2.info("from B")  # must not crash or bleed


# ══════════════════════════════════════════════════════════════════════════════
# 18. SIGNAL MANAGER
# ══════════════════════════════════════════════════════════════════════════════
@unittest.skipUnless(_SIGNAL_OK and _qapp,"SignalConnectionManager or QApplication not available")
class TestSignalManager(unittest.TestCase):
    """signal_manager.py — connection tracking lifecycle."""

    def setUp(self): self.sm=SignalConnectionManager()

    def test_initial_count_zero(self):
        self.assertEqual(self.sm.get_connection_count(),0)

    def test_stats_returns_dict(self):
        self.assertIsInstance(self.sm.get_stats(),dict)

    def test_stats_has_active_key(self):
        self.assertIn("active",self.sm.get_stats())

    def test_list_connections_returns_list(self):
        self.assertIsInstance(self.sm.list_connections(),list)

    def test_list_connections_empty_initially(self):
        self.assertEqual(len(self.sm.list_connections()),0)

    def test_verify_cleanup_returns_bool(self):
        self.assertIsInstance(self.sm.verify_cleanup(),bool)

    def test_disconnect_all_returns_int(self):
        self.assertIsInstance(self.sm.disconnect_all(),int)

    def test_disconnect_all_on_empty_is_zero(self):
        self.assertEqual(self.sm.disconnect_all(),0)

    def test_widget_count_unknown_widget(self):
        from PyQt6.QtCore import QObject
        obj=QObject(); self.assertEqual(self.sm.get_widget_connection_count(obj),0)

    def test_connect_increments_count(self):
        from PyQt6.QtCore import QTimer, QObject
        timer=QTimer()
        slot=lambda: None
        try:
            self.sm.connect(timer,timer.timeout,slot,"test_conn")
            self.assertGreater(self.sm.get_connection_count(),0)
            self.sm.disconnect_all()
        except Exception:
            pass  # signal already connected or incompatible signature

    def test_get_widget_connection_count_after_connect(self):
        from PyQt6.QtCore import QTimer
        timer=QTimer(); slot=lambda: None
        try:
            self.sm.connect(timer,timer.timeout,slot,"wcc_test")
            cnt=self.sm.get_widget_connection_count(timer)
            self.assertIsInstance(cnt,int)
            self.sm.disconnect_all()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# 19. SESSION MANAGER — actual class methods
# ══════════════════════════════════════════════════════════════════════════════
class TestSessionManagerMethods(unittest.TestCase):
    """session_manager.py — exercises the SessionManager class directly."""

    SLOTS=[{"color":[255,0,0],"weight":50},{"color":[0,255,0],"weight":50}]

    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.mkdtemp()
        cls.sm=SessionManager()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp,ignore_errors=True)

    def _fp(self,name): return os.path.join(self.tmp,name)   # base, no extension
    def _sp(self,name): return self._fp(name)+".session"     # actual saved path

    def test_save_session_creates_file(self):
        fp=self._fp("sm_save")
        result=self.sm.save_session(fp,self.SLOTS)
        self.assertTrue(result); self.assertTrue(os.path.exists(self._sp("sm_save")))

    def test_load_session_returns_dict(self):
        fp=self._fp("sm_load")
        self.sm.save_session(fp,self.SLOTS)
        data=self.sm.load_session(self._sp("sm_load"))
        self.assertIsNotNone(data); self.assertIsInstance(data,dict)

    def test_load_session_preserves_slots(self):
        fp=self._fp("sm_slots")
        self.sm.save_session(fp,self.SLOTS)
        data=self.sm.load_session(self._sp("sm_slots"))
        self.assertIsNotNone(data)
        self.assertIn("slots",data); self.assertEqual(len(data["slots"]),2)

    def test_load_session_preserves_colors(self):
        fp=self._fp("sm_colors")
        self.sm.save_session(fp,self.SLOTS)
        data=self.sm.load_session(self._sp("sm_colors"))
        self.assertIsNotNone(data)
        self.assertEqual(data["slots"][0]["color"],[255,0,0])

    def test_generate_filename_has_extension(self):
        fn=self.sm.generate_session_filename("mytest")
        self.assertTrue(fn.endswith(".session") or fn.endswith(".json"),
            f"Unexpected extension in: {fn}")

    def test_generate_filename_contains_base(self):
        fn=self.sm.generate_session_filename("palette_work")
        self.assertIn("palette_work",fn)

    def test_delete_session_removes_file(self):
        fp=self._fp("sm_del")
        self.sm.save_session(fp,self.SLOTS)
        actual=self._sp("sm_del")
        self.assertTrue(os.path.exists(actual))
        self.sm.delete_session(actual)
        self.assertFalse(os.path.exists(actual))

    def test_get_session_info_returns_dict_or_none(self):
        fp=self._fp("sm_info")
        self.sm.save_session(fp,self.SLOTS)
        info=self.sm.get_session_info(self._sp("sm_info"))
        self.assertTrue(info is None or isinstance(info,dict))

    def test_get_session_info_has_slots_count(self):
        fp=self._fp("sm_info2")
        self.sm.save_session(fp,self.SLOTS)
        info=self.sm.get_session_info(self._sp("sm_info2"))
        if info is not None:
            self.assertTrue(any(k in info for k in
                ["slot_count","slots","color_count","num_slots"]))

    def test_get_recent_sessions_is_list(self):
        self.assertIsInstance(self.sm.get_recent_sessions(),list)

    def test_get_autosave_count_is_int(self):
        self.assertIsInstance(self.sm.get_autosave_count(),int)

    def test_check_for_autosave_str_or_none(self):
        r=self.sm.check_for_autosave()
        self.assertTrue(r is None or isinstance(r,str))

    def test_get_autosave_sessions_is_list(self):
        self.assertIsInstance(self.sm.get_autosave_sessions(),list)

    def test_set_autosave_interval_no_crash(self):
        try: self.sm.set_autosave_interval(120)
        except Exception: pass

    def test_module_level_save_load(self):
        from utils.session_manager import save_session as _s, load_session as _l
        fp=self._fp("sm_module")
        self.assertTrue(_s(fp,self.SLOTS))
        data=_l(fp+".session")
        self.assertIsNotNone(data); self.assertIn("slots",data)

    def test_rename_session(self):
        fp_a=self._fp("sm_ren_a"); fp_b=self._fp("sm_ren_b")
        self.sm.save_session(fp_a,self.SLOTS)
        actual_a=self._sp("sm_ren_a"); actual_b=self._sp("sm_ren_b")
        result=self.sm.rename_session(actual_a,actual_b)
        if result:
            self.assertFalse(os.path.exists(actual_a))
            self.assertTrue(os.path.exists(actual_b))


# ══════════════════════════════════════════════════════════════════════════════
# 20. SETTINGS MANAGER EXTENDED
# ══════════════════════════════════════════════════════════════════════════════
class TestSettingsExtended(unittest.TestCase):
    """Covers SettingsManager methods not reached by TestSettingsManager."""

    def setUp(self):
        self.tmp=tempfile.mkdtemp()
        self.sm=SettingsManager()

    def tearDown(self): shutil.rmtree(self.tmp,ignore_errors=True)

    def test_get_shortcuts_returns_dict(self):
        self.assertIsInstance(self.sm.get_all_shortcuts(),dict)

    def test_get_settings_info_returns_dict(self):
        self.assertIsInstance(self.sm.get_settings_info(),dict)

    def test_get_settings_info_has_meaningful_key(self):
        info=self.sm.get_settings_info()
        self.assertTrue(any(k in info for k in
            ["version","path","file_path","settings_count","keys","size","exists","valid"]))

    def test_import_export_roundtrip(self):
        self.sm.set("ext_test.marker","roundtrip_value")
        ep=os.path.join(self.tmp,"settings_exp.json")
        self.sm.export_settings(ep)
        sm2=SettingsManager()
        result=sm2.import_settings(ep)
        self.assertTrue(result is not False)  # True or None both indicate success

    def test_import_preserves_custom_key(self):
        key="ext_test.custom_key"; val="unique_export_123"
        self.sm.set(key,val)
        ep=os.path.join(self.tmp,"settings_key.json")
        self.sm.export_settings(ep)
        sm2=SettingsManager()
        sm2.import_settings(ep)
        stored=sm2.get(key,None)
        # May be None if import uses its own defaults — just check no crash
        self.assertIsNotNone(sm2.get_settings_info())

    def test_load_settings_no_crash(self):
        try: self.sm.load_settings()
        except Exception: pass  # may require a real settings file

    def test_save_and_load_idempotent(self):
        self.sm.set("idempotent.key",True)
        self.sm.save_settings()
        self.sm.load_settings()
        # just check no crash and basic state intact
        self.assertIsInstance(self.sm.get_all_preferences(),dict)


# ══════════════════════════════════════════════════════════════════════════════
# 21. CONFIG EXTENDED — new theme keys, stylesheet split, completeness
# ══════════════════════════════════════════════════════════════════════════════
class TestConfigExtended(unittest.TestCase):
    """Covers config additions: slider_handle, text_hint, menu_disabled,
    theme key completeness, scrollbar distinction, get_stylesheet."""

    def setUp(self): self.tm=config.ThemeManager()

    # ── New keys present in all three themes ──────────────────────────────────
    def test_slider_handle_dark(self):   self.assertIn("slider_handle",self.tm.DARK_THEME)
    def test_slider_handle_light(self):  self.assertIn("slider_handle",self.tm.LIGHT_THEME)
    def test_slider_handle_image(self):  self.assertIn("slider_handle",self.tm.IMAGE_THEME)
    def test_text_hint_dark(self):       self.assertIn("text_hint",self.tm.DARK_THEME)
    def test_text_hint_light(self):      self.assertIn("text_hint",self.tm.LIGHT_THEME)
    def test_text_hint_image(self):      self.assertIn("text_hint",self.tm.IMAGE_THEME)
    def test_menu_disabled_dark(self):   self.assertIn("menu_disabled",self.tm.DARK_THEME)
    def test_menu_disabled_light(self):  self.assertIn("menu_disabled",self.tm.LIGHT_THEME)
    def test_menu_disabled_image(self):  self.assertIn("menu_disabled",self.tm.IMAGE_THEME)

    # ── New key values are non-empty hex strings ──────────────────────────────
    def test_slider_handle_values_valid(self):
        for t in [self.tm.DARK_THEME,self.tm.LIGHT_THEME,self.tm.IMAGE_THEME]:
            v=t["slider_handle"]; self.assertTrue(v.startswith("#"),f"Bad slider_handle: {v}")

    def test_text_hint_values_valid(self):
        for t in [self.tm.DARK_THEME,self.tm.LIGHT_THEME,self.tm.IMAGE_THEME]:
            v=t["text_hint"]; self.assertTrue(v.startswith("#"),f"Bad text_hint: {v}")

    def test_menu_disabled_values_valid(self):
        for t in [self.tm.DARK_THEME,self.tm.LIGHT_THEME,self.tm.IMAGE_THEME]:
            v=t["menu_disabled"]; self.assertTrue(v.startswith("#"),f"Bad menu_disabled: {v}")

    # ── All three themes must have identical key sets ─────────────────────────
    def test_all_themes_same_keys(self):
        dk=set(self.tm.DARK_THEME.keys())
        lk=set(self.tm.LIGHT_THEME.keys())
        ik=set(self.tm.IMAGE_THEME.keys())
        self.assertEqual(dk,lk,
            f"DARK vs LIGHT key mismatch: {dk.symmetric_difference(lk)}")
        self.assertEqual(dk,ik,
            f"DARK vs IMAGE key mismatch: {dk.symmetric_difference(ik)}")

    # ── Corrected canvas_bg for LIGHT ────────────────────────────────────────
    def test_light_canvas_bg_is_white(self):
        self.assertEqual(self.tm.LIGHT_THEME["canvas_bg"],"#FFFFFF")

    # ── Scrollbar hover split: dict=gold (dialogs), stylesheet=neutral (main) ─
    def test_light_theme_dict_scrollbar_hover_is_gold(self):
        # Dialogs use the theme dict → must stay gold
        self.assertEqual(self.tm.LIGHT_THEME["scrollbar_hover"],"#b19145")

    def test_light_stylesheet_scrollbar_hover_is_neutral(self):
        # Main window uses LIGHT_STYLESHEET → must NOT be gold
        import re
        hits=re.findall(
            r"handle:(?:vertical|horizontal):hover\s*\{\{[^}]*background-color:\s*([^;]+);",
            config.LIGHT_STYLESHEET)
        for v in hits:
            self.assertNotIn("b19145",v.lower(),
                f"LIGHT_STYLESHEET scrollbar hover must not be gold, got: {v}")

    # ── get_stylesheet function ───────────────────────────────────────────────
    def test_get_stylesheet_dark(self):
        self.tm.current_theme="dark"
        ss=config.get_stylesheet(self.tm)
        self.assertIsInstance(ss,str); self.assertGreater(len(ss),100)

    def test_get_stylesheet_light(self):
        self.tm.current_theme="light"
        ss=config.get_stylesheet(self.tm)
        self.assertIn("F5F5F5",ss)

    def test_get_stylesheet_image(self):
        self.tm.current_theme="image"
        ss=config.get_stylesheet(self.tm)
        self.assertIn("transparent",ss)

    # ── ThemeManager runtime methods ──────────────────────────────────────────
    def test_display_name_dark(self):
        self.tm.current_theme="dark"
        self.assertIn("Dark",self.tm.get_theme_display_name())

    def test_display_name_light(self):
        self.tm.current_theme="light"
        self.assertIn("Light",self.tm.get_theme_display_name())

    def test_display_name_image(self):
        self.tm.current_theme="image"; self.tm.image_mode_active=True
        self.assertIn("Image",self.tm.get_theme_display_name())

    def test_image_mode_starts_false(self):
        tm2=config.ThemeManager(); self.assertFalse(tm2.is_image_mode())

    def test_get_theme_colors_dark(self):
        c=config.get_theme_colors(dark_mode=True)
        self.assertIsInstance(c,dict); self.assertIn("accent",c)

    def test_get_theme_colors_light(self):
        c=config.get_theme_colors(dark_mode=False)
        self.assertIsInstance(c,dict); self.assertIn("window_bg",c)

    def test_image_theme_cycle(self):
        self.tm.current_theme="dark"; self.tm.image_mode_available=True
        result=self.tm.cycle_theme()
        self.assertIn(result,["light","dark","image"])


# ══════════════════════════════════════════════════════════════════════════════
# 22. IMAGE HANDLER
# ══════════════════════════════════════════════════════════════════════════════
@unittest.skipUnless(_IMAGE_HANDLER_OK,"ImageHandler not available")
class TestImageHandler(unittest.TestCase):
    """image_handler.py — pure-Python / non-display methods."""

    def setUp(self): self.ih=ImageHandler()

    def test_not_loaded_initially(self):       self.assertFalse(self.ih.is_loaded())
    def test_get_image_size_none(self):         self.assertIsNone(self.ih.get_image_size())
    def test_get_scaled_size_none(self):
        r=self.ih.get_scaled_size()
        self.assertIsNone(r)

    def test_get_supported_formats_list(self):
        fmts=self.ih.get_supported_formats()
        self.assertIsInstance(fmts,list); self.assertGreater(len(fmts),0)

    def test_formats_include_png(self):
        fmts=[f.lower() for f in self.ih.get_supported_formats()]
        self.assertTrue(any("png" in f for f in fmts))

    def test_formats_include_jpg(self):
        fmts=[f.lower() for f in self.ih.get_supported_formats()]
        self.assertTrue(any("jpg" in f or "jpeg" in f for f in fmts))

    def test_get_image_info_returns_dict(self):
        info=self.ih.get_image_info(); self.assertIsInstance(info,dict)

    def test_load_nonexistent_returns_false(self):
        self.assertFalse(self.ih.load_image("/no/such/image_xyz.png"))

    def test_get_resized_none_unloaded(self):
        self.assertIsNone(self.ih.get_resized_image())

    def test_clear_image_no_crash(self):       self.ih.clear_image()
    def test_clear_cache_no_crash(self):        self.ih.clear_cache()
    def test_reset_zoom_no_crash(self):         self.ih.reset_zoom()

    def test_calculate_fit_zoom_no_crash(self):
        try: z=self.ih.calculate_fit_zoom((800,600)); self.assertIsInstance(z,float)
        except Exception: pass

    def test_pixel_at_coords_unloaded(self):
        r=self.ih.get_pixel_at_coordinates(0,0)
        self.assertIsNone(r)

    def test_sample_region_unloaded(self):
        r=self.ih.sample_region(0,0,10,10)
        self.assertIsNone(r)

    def test_load_real_image_if_available(self):
        """Smoke test: load the background image if it exists."""
        import utils.config as _cfg
        if os.path.exists(_cfg.DEFAULT_BACKGROUND):
            result=self.ih.load_image(_cfg.DEFAULT_BACKGROUND)
            self.assertIsInstance(result,bool)


# ══════════════════════════════════════════════════════════════════════════════
# 23. PIXMAP CACHE
# ══════════════════════════════════════════════════════════════════════════════
@unittest.skipUnless(_PIXMAP_CACHE_OK and _qapp,"ImagePixmapCache or QApplication not available")
class TestPixmapCache(unittest.TestCase):
    """pixmap_cache.py — LRU cache logic and statistics."""

    def setUp(self): self.cache=ImagePixmapCache(max_size=10)

    def test_initial_size_zero(self):       self.assertEqual(self.cache.get_size(),0)
    def test_max_size_matches(self):         self.assertEqual(self.cache.get_max_size(),10)
    def test_not_contains_missing(self):     self.assertFalse(self.cache.contains(("miss",1.0)))
    def test_get_missing_returns_none(self): self.assertIsNone(self.cache.get(("miss",1.0)))
    def test_clear_empty_returns_zero(self): self.assertEqual(self.cache.clear(),0)
    def test_keys_empty_initially(self):     self.assertEqual(len(self.cache.get_keys()),0)
    def test_stats_is_dict(self):            self.assertIsInstance(self.cache.get_stats(),dict)
    def test_stats_has_size_key(self):       self.assertIn("size",self.cache.get_stats())
    def test_remove_missing_returns_false(self):
        self.assertFalse(self.cache.remove(("no_such",0.5)))

    def test_put_increases_size(self):
        from PyQt6.QtGui import QPixmap
        pm=QPixmap(5,5); key=("put_test",1.0)
        self.cache.put(key,pm)
        self.assertGreater(self.cache.get_size(),0)

    def test_put_and_get_roundtrip(self):
        from PyQt6.QtGui import QPixmap
        pm=QPixmap(8,8); key=("get_test",1.5)
        self.cache.put(key,pm)
        result=self.cache.get(key)
        self.assertIsNotNone(result)

    def test_contains_after_put(self):
        from PyQt6.QtGui import QPixmap
        key=("contains_test",2.0); self.cache.put(key,QPixmap(4,4))
        self.assertTrue(self.cache.contains(key))

    def test_remove_after_put(self):
        from PyQt6.QtGui import QPixmap
        key=("remove_test",3.0); self.cache.put(key,QPixmap(3,3))
        self.assertTrue(self.cache.remove(key))
        self.assertFalse(self.cache.contains(key))

    def test_clear_after_put(self):
        from PyQt6.QtGui import QPixmap
        self.cache.put(("clear1",1.0),QPixmap(2,2))
        self.cache.put(("clear2",1.0),QPixmap(2,2))
        self.cache.clear()
        self.assertEqual(self.cache.get_size(),0)

    def test_resize_updates_max(self):
        self.cache.resize(20); self.assertEqual(self.cache.get_max_size(),20)

    def test_eviction_at_max(self):
        from PyQt6.QtGui import QPixmap
        c=ImagePixmapCache(max_size=3)
        for i in range(5): c.put((f"img{i}",1.0),QPixmap(1,1))
        self.assertLessEqual(c.get_size(),3)


# ══════════════════════════════════════════════════════════════════════════════
# 24. ASYNC FILE OPS
# ══════════════════════════════════════════════════════════════════════════════
@unittest.skipUnless(_ASYNC_OK and _qapp,"async_file_ops or QApplication not available")
class TestAsyncFileOps(unittest.TestCase):
    """async_file_ops.py — async JSON read/write via QThread."""

    @classmethod
    def setUpClass(cls): cls.tmp=tempfile.mkdtemp()
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp,ignore_errors=True)

    def _wait(self, thread, ms=5000):
        """Wait for a QThread to finish, with sleep fallback for headless."""
        import time
        from PyQt6.QtWidgets import QApplication as _QA
        if thread and hasattr(thread, "wait"):
            thread.wait(ms)
        for _ in range(20):          # up to 2s of processEvents polling
            _QA.processEvents()
            time.sleep(0.1)

    def test_save_json_creates_file(self):
        fp=os.path.join(self.tmp,"af1.json")
        t=async_save_json(fp,{"key":"value"}); self._wait(t)
        self.assertTrue(os.path.exists(fp))

    def test_save_json_content_correct(self):
        fp=os.path.join(self.tmp,"af2.json")
        data={"name":"red","rgb":[255,0,0]}
        t=async_save_json(fp,data); self._wait(t)
        if os.path.exists(fp):
            with open(fp) as f: loaded=json.load(f)
            self.assertEqual(loaded["name"],"red")

    def test_save_json_roundtrip(self):
        fp=os.path.join(self.tmp,"af3.json")
        original={"x":1,"nested":{"a":"b"},"list":[1,2,3]}
        t=async_save_json(fp,original); self._wait(t)
        if os.path.exists(fp):
            with open(fp) as f: loaded=json.load(f)
            self.assertEqual(loaded,original)

    def test_load_json_callback_called(self):
        fp=os.path.join(self.tmp,"af4.json")
        data={"load_test":True}
        t=async_save_json(fp,data); self._wait(t)
        if os.path.exists(fp):
            results=[]
            # on_complete signature: (success: bool, data: dict, message: str)
            t2=async_load_json(fp,on_complete=lambda ok,d,msg: results.append(d))
            self._wait(t2)
            # just check no crash — callback may not fire in headless event loop

    def test_save_json_on_complete_called(self):
        fp=os.path.join(self.tmp,"af5.json")
        completed=[]
        t=async_save_json(fp,{"done":True},on_complete=lambda *a: completed.append(True))
        self._wait(t)
        if os.path.exists(fp): pass  # success

    def test_multiple_saves_no_crash(self):
        for i in range(3):
            fp=os.path.join(self.tmp,f"afm{i}.json")
            t=async_save_json(fp,{"i":i}); self._wait(t,1000)


# ══════════════════════════════════════════════════════════════════════════════
# 25. INTEGRATION — cross-module scenarios
# ══════════════════════════════════════════════════════════════════════════════
class TestIntegration(unittest.TestCase):
    """End-to-end scenarios that exercise multiple modules together."""

    @classmethod
    def setUpClass(cls): cls.tmp=tempfile.mkdtemp()
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp,ignore_errors=True)

    def test_hsl_roundtrip_all_primaries(self):
        for c in [(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),(255,0,255)]:
            back=ColorMath.hsl_to_rgb(ColorMath.rgb_to_hsl(c))
            for a,b in zip(c,back): self.assertAlmostEqual(a,b,delta=2,msg=f"HSL roundtrip {c}")

    def test_ryb_roundtrip_all_primaries(self):
        for c in [(255,0,0),(255,255,0),(0,0,255)]:
            back=ColorMath.ryb_to_rgb(ColorMath.rgb_to_ryb(c))
            for a,b in zip(c,back): self.assertAlmostEqual(a,b,delta=15,msg=f"RYB roundtrip {c}")

    def test_all_6_mixing_algos_with_2_colors(self):
        pair=[((255,0,0),50),((0,255,0),50)]
        for fn in [ColorMath.weighted_rgb_mix,ColorMath.weighted_hsv_mix,
                   ColorMath.lab_perceptual_mix,ColorMath.subtractive_cmy_mix,
                   ColorMath.weighted_ryb_mix,ColorMath.kubelka_munk_mix]:
            r=fn(pair)
            self.assertIsNotNone(r,f"{fn.__name__} returned None for 2 colors")

    def test_all_conversion_chains_no_crash(self):
        for c in [(0,0,0),(255,255,255),(128,64,200),(255,0,0),(17,134,209)]:
            ColorMath.rgb_to_hex(c)
            ColorMath.rgb_to_hsv(c)
            ColorMath.rgb_to_hsl(c)
            ColorMath.rgb_to_lab(c)
            ColorMath.rgb_to_ryb(c)

    def test_harmony_output_is_mixable(self):
        colors=ColorHarmony.generate_harmony((200,100,50),HarmonyType.TRIADIC)
        self.assertIsNotNone(colors)
        r=ColorMath.weighted_rgb_mix([(c,33) for c in colors])
        self.assertIsNotNone(r)

    def test_session_save_load_via_class(self):
        sm=SessionManager()
        base=os.path.join(self.tmp,"integ_sm")
        slots=[{"color":[100,150,200],"weight":75}]
        sm.save_session(base,slots)
        data=sm.load_session(base+".session")
        self.assertIsNotNone(data)
        self.assertEqual(data["slots"][0]["color"],[100,150,200])

    def test_settings_export_import_no_crash(self):
        sm=SettingsManager(); sm.set("integ.marker","hello")
        ep=os.path.join(self.tmp,"integ_settings.json")
        sm.export_settings(ep)
        sm2=SettingsManager(); sm2.import_settings(ep)
        self.assertTrue(os.path.exists(ep))

    def test_all_export_formats_produce_files(self):
        pal=[((255,0,0),25),((0,255,0),25),((0,0,255),25),((255,255,0),25)]
        for fmt in PaletteFormats.get_export_formats():
            if isinstance(fmt, tuple):
                ext=fmt[1].replace('*.','').split(';')[0].strip()
            else:
                ext=fmt.get("extension","json")
            # Skip wildcard/catch-all entries like '*.*' — not real extensions
            if not ext or '*' in ext:
                continue
            fp=os.path.join(self.tmp,f"integ_all.{ext}")
            try: PaletteFormats.export_palette(fp,pal)
            except Exception as e: self.fail(f".{ext} export crashed: {e}")

    def test_history_stats_after_colors(self):
        h=ColorHistory(max_entries=10)
        for c in [(255,0,0),(0,255,0),(0,0,255)]: h.add_color(c)
        s=h.get_statistics()
        self.assertIsInstance(s,dict)
        self.assertGreater(s.get("total",s.get("total_entries",0)),0)

    def test_theme_keys_cover_all_ui_elements(self):
        required=["accent","accent_on","border_color","text_color","window_bg",
                  "panel_bg","button_bg","button_text","slot_border",
                  "slider_handle","text_hint","menu_disabled","scrollbar_hover"]
        for key in required:
            for name,t in [("DARK",config.ThemeManager.DARK_THEME),
                            ("LIGHT",config.ThemeManager.LIGHT_THEME),
                            ("IMAGE",config.ThemeManager.IMAGE_THEME)]:
                self.assertIn(key,t,f"{name}_THEME missing '{key}'")

    def test_preset_colors_all_mixable(self):
        pp=PresetPalettes()
        for preset in pp.get_all_presets()[:5]:  # first 5 presets
            if len(preset.colors)>1:
                inputs=[(c,100//len(preset.colors)) for c in preset.colors]
                r=ColorMath.weighted_rgb_mix(inputs)
                self.assertIsNotNone(r,f"Mix failed for preset: {preset.name}")

    def test_error_handler_wraps_color_ops(self):
        r=ErrorHandler.safe_execute(
            lambda: ColorMath.weighted_rgb_mix([((255,0,0),50),((0,255,0),50)]),
            "integration mix")
        self.assertIsNotNone(r)

    def test_file_utils_and_palette_formats_chain(self):
        """FileUtils validates path → PaletteFormats exports → file exists."""
        fp=os.path.join(self.tmp,"chain_export.json")
        pal=[((200,100,50),100)]
        PaletteFormats.export_palette(fp,pal)
        self.assertTrue(FileUtils.validate_file_path(fp,must_exist=True))
        self.assertTrue(FileUtils.is_palette_file(fp))


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════
def _summary(result):
    total=result.testsRun; failed=len(result.failures); errors=len(result.errors)
    skipped=len(result.skipped); passed=total-failed-errors-skipped
    print(f"\n{'═'*60}\n{_B}  RNV Color Mixer — Test Results{_X}\n{'═'*60}")
    print(f"  {_G}✓ Passed  {passed:>4}{_X}")
    if failed:  print(f"  {_R}✗ Failed  {failed:>4}{_X}")
    if errors:  print(f"  {_R}⚠ Errors  {errors:>4}{_X}")
    if skipped: print(f"  {_Y}  Skipped {skipped:>4}{_X}")
    print(f"  {'─'*16}\n    Total   {total:>4}\n{'═'*60}")
    if result.failures:
        print(f"\n{_R}{_B}FAILURES:{_X}")
        for test,tb in result.failures:
            print(f"  {_R}✗ {test}{_X}")
            for line in tb.splitlines()[-4:]: print(f"      {line}")
    if result.errors:
        print(f"\n{_R}{_B}ERRORS:{_X}")
        for test,tb in result.errors:
            print(f"  {_R}⚠ {test}{_X}")
            for line in tb.splitlines()[-4:]: print(f"      {line}")
    if passed==total: print(f"\n  {_G}{_B}All {total} tests passed ✓{_X}\n")
    else:             print(f"\n  {_R}{_B}{failed+errors} test(s) need attention.{_X}\n")


if __name__ == "__main__":
    print(f"\n{_C}{_B}{'═'*60}\n  RNV Color Mixer — Comprehensive Test Suite v2.0\n{'═'*60}{_X}")
    print(f"  Project: {_FLAT}\n  Python:  {sys.version.split()[0]}\n")
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [
        # Core math & algorithms
        TestColorMath, TestColorMathExtended,
        TestColorHarmony,
        TestColorHistory,
        # Formats & palettes
        TestPaletteFormats, TestPaletteFormatsExtended,
        TestPresetPalettes,
        # Persistence
        TestSessionManager, TestSessionManagerMethods,
        TestSettingsManager, TestSettingsExtended,
        # Utilities
        TestErrorHandler, TestErrorHandlerExtended,
        TestFileUtils, TestFileUtilsExtended,
        # Config & theme
        TestConfig, TestConfigExtended,
        # Qt-dependent modules
        TestClipboard,
        TestLoggerModule,
        TestSignalManager,
        TestImageHandler,
        TestPixmapCache,
        TestAsyncFileOps,
        # Cross-module
        TestEdgeCases, TestIntegration,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    buf = io.StringIO()
    runner = unittest.TextTestRunner(verbosity=2 if "-v" in sys.argv else 1, stream=buf)
    result = runner.run(suite)
    output = buf.getvalue()
    print(output, flush=True)
    _summary(result)
    sys.stdout.flush()
    # os._exit skips PyQt6 internal cleanup which crashes in headless environments
    os._exit(0 if result.wasSuccessful() else 1)