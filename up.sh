python3 - <<'EOF'
import re,pathlib,sys
H=re.compile(r'#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Fa-f])')
T=["utils/config.py","ui/colors.py","utils/dialog_styles.py"]
F={"test_rnv_color_mixer.py":[('LIGHT_THEME["canvas_bg"],"#FFFFFF"','LIGHT_THEME["canvas_bg"],"#ffffff"')],
"test_rnv_icon_builder.py":[('(CONTRAST_ON_DARK, "#FFFFFF")','(CONTRAST_ON_DARK, "#ffffff")'),
("DARK_THEME_COLORS['main_btn_bg'], '#1A1A1A'","DARK_THEME_COLORS['main_btn_bg'], '#1a1a1a'"),
("LIGHT_THEME_COLORS['main_btn_bg'], '#FFFFFF'","LIGHT_THEME_COLORS['main_btn_bg'], '#ffffff'"),
("LIGHT_THEME['button_pressed_text'], '#FFFFFF'","LIGHT_THEME['button_pressed_text'], '#ffffff'")]}
c=[p for p in map(pathlib.Path,T) if p.is_file() and H.search(p.read_text())]
if len(c)!=1: sys.exit(f"STOP: expected 1 colour file, found {len(c)}: {c}")
p=c[0]; b=p.read_text(); a=H.sub(lambda m:m.group(0).lower(),b)
if b.lower()!=a.lower() or len(b)!=len(a): sys.exit("STOP: change is not case-only")
n=sum(1 for m in H.finditer(b) if not m.group(0)[1:].isdigit() and not m.group(0)[1:].islower())
p.write_text(a); print(f"{p}: {n} normalised")
for fn,eds in F.items():
    q=pathlib.Path(fn)
    if not q.is_file(): continue
    t=q.read_text()
    for old,new in eds:
        k=t.count(old)
        if k!=1: sys.exit(f"STOP: {fn} expected 1 of {old!r}, found {k}")
        t=t.replace(old,new)
    q.write_text(t); print(f"{fn}: {len(eds)} assertion(s) fixed")
print("done - run the tests")
EOF
