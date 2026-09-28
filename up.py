#!/usr/bin/env python3
"""nav.py -- /aiii/ gets the site nav; /resume/'s nav matches every other page.

Built against rnvizion.github.io @ main 5a7de11.

TWO FILES MOVE. Both are checked before either is written; if either has
moved, nothing is written at all.

aiii/index.html -- five guarded edits:
  1. the Google Fonts link requests Montserrat 900. The nav draws the RNVizion
     mark, and drawing it without loading the face renders it in system-ui.
  2. the comment explaining why Montserrat was NOT loaded is retired. It
     described an absence this change ends; left in, it is a fossil caution.
  3. the nav CSS, copied from demos/rnv-publishing-agent/index.html lines
     98-204 -- through the close of the 640px block. The note cited 98-190,
     which stops before `.nav-links.open`: the rule that makes the phone menu
     open. That range produces a hamburger that toggles a class nothing reads.
  4. the nav markup, six items, none active (this page is not one of the six).
  5. the toggle script, demos lines 799-812 -- one line past the note's 811,
     which ends inside the forEach and does not parse. It deliberately starts
     at 799: line 797 sets #year, this page has no #year, and that line would
     throw before either listener attached.

resume/index.html -- six guarded edits. Operator ruling 2026-09-27: decision
#9 (the resume link stays out of the nav; footer only) covers the resume
page's own nav too, and that nav matches every other non-home page.
  1. the nav markup is replaced with bio/index.html's, verbatim: About, Stack,
     Work, Demos, Blog, Contact, none active. The Resume item goes; Stack and
     Contact, which only this page lacked, come back. The footer keeps its
     Resume link, which is where #9 puts it.
  2-6. the nav CSS gains what every other nav page has and this one never did
     -- it has been this shape since the page was created on 2026-06-21, five
     weeks before #9 existed: the 32px gap (it was 28), `position: relative`
     on the links, the gold underline that slides in on hover, the hamburger
     that turns into an X when open, and no underline inside the phone menu.
     Written in this page's own one-line style. Compared by parsed
     declarations, its nav CSS is now identical to the twelve pages that
     share one.
  Left as they are: the toggle script (same behaviour), the 73px comment
  (still true), and the footer.

WHY AIII'S NAV PALETTE IS DECLARED ON nav, NOT :root. The nav's CSS references
six tokens aiii does not declare. Rewriting them to aiii's own tokens is not
equivalent: --text is #e8e8f0 (cool) where aiii's --ink is #e7e3d8 (warm);
--border-soft is solid #1e1e2e where --hair is translucent gold. Declaring them
on nav gives the exact site values without putting the parent's names into
AIII's own register. The resume page needs none of this: it already declares
the site palette in :root.

VERIFIED BEFORE HANDOVER, and the limits are stated beside the results:
  * rendered in headless Chromium at 1280 and 390 wide: both navs have zero
    computed-style differences from the reference nav, the open-menu state
    included; nothing else on either page moved except the space aiii's
    sticky nav occupies; both phone menus open with all six links reachable.
  * Brand Infrastructure's verify_type passes both pages, and fails a copy of
    aiii with Montserrat removed from the link.
  * Ask the Corpus strips <nav> before ingesting, so neither page's corpus
    text changes and no eval case moves.
  * NOT verified: typography. Google Fonts is blocked in the sandbox that
    rendered this, so every face was a fallback. Look at it on your phone.

Refuses on any unexpected base and writes nothing. Re-running is a no-op.
  python nav.py --check   # report what would change, write nothing
  python nav.py           # apply
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, check=True).stdout.strip())

FILES = json.loads(r"""{"aiii/index.html": [["font link requests Montserrat", "<link href=\"https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800&family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600;700&display=swap\"", "<link href=\"https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800&family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600;700&family=Montserrat:wght@900&display=swap\""], ["retire the comment explaining why Montserrat was not loaded", "\n    /* Defined but NOT loaded on this page: the font link deliberately omits\n       Montserrat, because this page carries no site nav and therefore no\n       RNVizion wordmark to set in it. The token stays so the five-token\n       vocabulary is identical everywhere. If this page ever draws the mark,\n       restore `&family=Montserrat:wght@900` to the link IN THE SAME CHANGE --\n       using it without loading it renders the wordmark in system-ui, which\n       looks wrong on a live page rather than merely wasting a request. */", ""], ["nav CSS, with its palette scoped to nav", "</style>", "\n  /* ---------- Site nav ----------------------------------------------------\n     The parent brand's chrome on an initiative page. Its palette is declared\n     ON nav, not :root, so the page's own vocabulary stays AIII's: --text here\n     is the site's cool #e8e8f0, which is not this page's warm --ink, and\n     --border-soft is a solid near-black, not this page's translucent --hair.\n     Rewriting the references to this page's tokens would render the nav in\n     the wrong palette; declaring them globally would put the parent's names\n     into a register that is deliberately its own.\n     The second rule gives the nav the site's body context in place of this\n     page's register (decision #16: Bricolage at 340, 1.75, warm ink). The\n     nav's links set family and size but inherit weight, leading and tracking,\n     so without it they compute differently here than on every other page. The third and fourth are base rules every\n     other nav page gets globally and this page does not have. */\n  nav{\n    --accent:#d2bc93; --text:#e8e8f0; --text-dim:#9a9ab0;\n    --border:#25253a; --border-soft:#1e1e2e; --max-width:1200px;\n  }\n  nav{\n    font-family:var(--font-body); font-size:17px; font-weight:400; line-height:1.7;\n    letter-spacing:normal; color:var(--text); text-rendering:auto;\n  }\n  nav a{ text-decoration:none; transition:color .2s ease; }\n  nav .container{ max-width:var(--max-width); margin:0 auto; padding:0 32px; }\n\n    nav {\n      position: sticky; top: 0;\n      backdrop-filter: blur(20px);\n      background: rgba(10, 10, 15, 0.7);\n      border-bottom: 1px solid var(--border-soft);\n      padding: 16px 0; z-index: 100;\n    }\n\n    nav .container {\n      display: flex; justify-content: space-between; align-items: center;\n    }\n\n    .logo { font-family: var(--font-mark); font-weight: 900; font-size: 14px; letter-spacing: 0.09em; color: var(--text); display: flex; align-items: center; gap: 8px; }\n\n    .logo .dot {\n      flex-shrink: 0;\n      width: 8px; height: 8px;\n      background: var(--accent); border-radius: 50%;\n      box-shadow: 0 0 12px var(--accent);\n      animation: pulse 2.4s ease-in-out infinite;\n    }\n\n    @keyframes pulse {\n      0%, 100% { opacity: 1; }\n      50% { opacity: 0.4; }\n    }\n\n    .nav-links {\n      display: flex; gap: 32px;\n      font-family: var(--font-mono); font-size: 13px;\n    }\n\n    .nav-links a { color: var(--text-dim); position: relative; }\n    .nav-links a:hover { color: var(--accent); }\n    .nav-links a.active { color: var(--accent); }\n    .nav-links a:hover { text-decoration: none; }\n\n    .nav-links a::after {\n      content: ''; position: absolute;\n      left: 0; bottom: -4px;\n      width: 0; height: 1px; background: var(--accent);\n      transition: width 0.25s ease;\n    }\n\n    .nav-links a:hover::after, .nav-links a.active::after { width: 100%; }\n\n    .nav-toggle {\n      display: none;\n      background: transparent;\n      border: 1px solid var(--border);\n      border-radius: 6px;\n      width: 40px; height: 40px;\n      cursor: pointer; padding: 0;\n      flex-direction: column;\n      justify-content: center;\n      align-items: center;\n      gap: 5px;\n      transition: border-color 0.2s ease;\n    }\n\n    .nav-toggle:hover { border-color: var(--accent); }\n\n    .nav-toggle span {\n      display: block; width: 18px; height: 1.5px;\n      background: var(--text);\n      transition: transform 0.25s ease, opacity 0.25s ease;\n    }\n\n    .nav-toggle.open span:nth-child(1) {\n      transform: translateY(6.5px) rotate(45deg);\n      background: var(--accent);\n    }\n\n    .nav-toggle.open span:nth-child(2) { opacity: 0; }\n\n    .nav-toggle.open span:nth-child(3) {\n      transform: translateY(-6.5px) rotate(-45deg);\n      background: var(--accent);\n    }\n\n    @media (max-width: 640px) {\n      .nav-toggle { display: flex; }\n\n      .nav-links {\n        position: fixed; top: 73px; left: 0; right: 0;\n        background: rgba(10, 10, 15, 0.96);\n        backdrop-filter: blur(20px);\n        border-bottom: 1px solid var(--border-soft);\n        flex-direction: column; gap: 0;\n        padding: 16px 32px 24px;\n        transform: translateY(-12px);\n        opacity: 0; pointer-events: none;\n        transition: transform 0.25s ease, opacity 0.25s ease;\n      }\n\n      .nav-links.open {\n        transform: translateY(0); opacity: 1; pointer-events: auto;\n      }\n\n      .nav-links a {\n        padding: 14px 0; font-size: 15px;\n        border-bottom: 1px solid var(--border-soft);\n      }\n\n      .nav-links a:last-child { border-bottom: none; }\n      .nav-links a::after { display: none; }\n    }\n</style>"], ["nav markup after <body>", "<body>\n<main class=\"wrap\">", "<body>\n  <nav>\n    <div class=\"container\">\n      <a href=\"/\" class=\"logo\">\n        <span class=\"dot\"></span>\n        RNVizion\n      </a>\n      <div class=\"nav-links\" id=\"nav-links\">\n        <a href=\"/#about\">About</a>\n        <a href=\"/#stack\">Stack</a>\n        <a href=\"/#work\">Work</a>\n        <a href=\"/demos/\">Demos</a>\n        <a href=\"/blog/\">Blog</a>\n        <a href=\"/#contact\">Contact</a>\n      </div>\n      <button class=\"nav-toggle\" id=\"nav-toggle\" aria-label=\"Toggle menu\" aria-expanded=\"false\">\n        <span></span><span></span><span></span>\n      </button>\n    </div>\n  </nav>\n<main class=\"wrap\">"], ["toggle script before </body>", "</main>\n</body>", "</main>\n  <script>\n    const navToggle = document.getElementById('nav-toggle');\n    const navLinks = document.getElementById('nav-links');\n    navToggle.addEventListener('click', () => {\n      const open = navLinks.classList.toggle('open');\n      navToggle.classList.toggle('open', open);\n      navToggle.setAttribute('aria-expanded', open);\n    });\n    navLinks.querySelectorAll('a').forEach(a => {\n      a.addEventListener('click', () => {\n        navLinks.classList.remove('open');\n        navToggle.classList.remove('open');\n        navToggle.setAttribute('aria-expanded', 'false');\n      });\n    });\n  </script>\n</body>"]], "resume/index.html": [["nav: six items, none active (bio's nav, verbatim)", "  <nav>\n    <div class=\"container\">\n      <a href=\"/\" class=\"logo\"><span class=\"dot\"></span> RNVizion</a>\n      <div class=\"nav-links\" id=\"nav-links\">\n        <a href=\"/#about\">About</a>\n        <a href=\"/#work\">Work</a>\n        <a href=\"/demos/\">Demos</a>\n        <a href=\"/blog/\">Blog</a>\n        <a href=\"/resume/\" class=\"active\">Résumé</a>\n      </div>\n      <button class=\"nav-toggle\" id=\"nav-toggle\" aria-label=\"Toggle menu\" aria-expanded=\"false\">\n        <span></span><span></span><span></span>\n      </button>\n    </div>\n  </nav>", "  <nav>\n    <div class=\"container\">\n      <a href=\"/\" class=\"logo\">\n        <span class=\"dot\"></span>\n        RNVizion\n      </a>\n      <div class=\"nav-links\" id=\"nav-links\">\n        <a href=\"/#about\">About</a>\n        <a href=\"/#stack\">Stack</a>\n        <a href=\"/#work\">Work</a>\n        <a href=\"/demos/\">Demos</a>\n        <a href=\"/blog/\">Blog</a>\n        <a href=\"/#contact\">Contact</a>\n      </div>\n      <button class=\"nav-toggle\" id=\"nav-toggle\" aria-label=\"Toggle menu\" aria-expanded=\"false\">\n        <span></span><span></span><span></span>\n      </button>\n    </div>\n  </nav>"], ["nav gap 28px -> 32px", "    .nav-links { display: flex; gap: 28px; font-family: var(--font-mono); font-size: 13px; }", "    .nav-links { display: flex; gap: 32px; font-family: var(--font-mono); font-size: 13px; }"], ["nav links positioned for the underline", "    .nav-links a { color: var(--text-dim); }", "    .nav-links a { color: var(--text-dim); position: relative; }"], ["hover/active underline", "    .nav-links a.active { color: var(--accent); }\n", "    .nav-links a.active { color: var(--accent); }\n    .nav-links a::after { content: ''; position: absolute; left: 0; bottom: -4px; width: 0; height: 1px; background: var(--accent); transition: width 0.25s ease; }\n    .nav-links a:hover::after, .nav-links a.active::after { width: 100%; }\n"], ["hamburger turns to X when open", "    .nav-toggle span { display: block; width: 18px; height: 1.5px; background: var(--text); transition: transform 0.25s ease, opacity 0.25s ease; }\n", "    .nav-toggle span { display: block; width: 18px; height: 1.5px; background: var(--text); transition: transform 0.25s ease, opacity 0.25s ease; }\n    .nav-toggle.open span:nth-child(1) { transform: translateY(6.5px) rotate(45deg); background: var(--accent); }\n    .nav-toggle.open span:nth-child(2) { opacity: 0; }\n    .nav-toggle.open span:nth-child(3) { transform: translateY(-6.5px) rotate(-45deg); background: var(--accent); }\n"], ["no underline inside the phone menu", "      .nav-links a:last-child { border-bottom: none; }\n    }", "      .nav-links a:last-child { border-bottom: none; }\n      .nav-links a::after { display: none; }\n    }"]]}""")


def state(text, old, new):
    """applied / pending / moved, judged on the edit's own text.

    An edit is applied when its replacement is present (for a deletion: when
    the deleted text is gone). It is pending only when its anchor occurs
    exactly once. Anything else means the file is not the one this was cut
    against. Anchors like </style> survive the patch, so their presence alone
    answers nothing -- practices section 1."""
    if new and new in text:
        return "applied"
    if not new and old not in text:
        return "applied"
    if text.count(old) == 1:
        return "pending"
    return "moved"


def main():
    check = "--check" in sys.argv[1:]
    staged, done = {}, []
    for rel, edits in FILES.items():
        path = ROOT / rel
        if not path.exists():
            sys.exit("%s not found -- wrong repo? This is for rnvizion.github.io." % rel)
        text = path.read_text(encoding="utf-8")
        states = [state(text, old, new) for _, old, new in edits]
        if all(s == "applied" for s in states):
            done.append(rel)
            continue
        if any(s != "pending" for s in states):
            bad = [name for (name, _, _), s in zip(edits, states) if s != "pending"]
            sys.exit("REFUSED: %s is partly changed or has moved since 5a7de11 (%s).\n"
                     "Nothing was written to either file; re-cut this against live."
                     % (rel, "; ".join(bad)))
        for name, old, new in edits:
            text = text.replace(old, new, 1)
        staged[rel] = text

    for rel in done:
        print("already applied -- %s. Nothing to do there." % rel)
    for rel, edits in FILES.items():
        if rel in staged:
            print(rel)
            for name, _, _ in edits:
                print("  %s %s" % ("would" if check else "done ", name))
    if not staged:
        return 0

    print()
    print("Left alone, deliberately:")
    print("  - every other page. These two now match them; they do not change them.")
    print("  - aiii's .wordmark rule. That is the AIII title, not the RNVizion mark.")
    print("  - the resume page's footer link. Decision #9 puts it there.")
    print("  - rnv-brand/profile.json. Its no_canonical_link entry for aiii is now")
    print("    unneeded, but that file is Brand Infrastructure's, and it must move")
    print("    AFTER this lands.")
    if check:
        print("\n--check: nothing written.")
        return 0

    for rel, text in staged.items():
        (ROOT / rel).write_text(text, encoding="utf-8")
    print()
    for t in ("test_post_shape.py", "test_template_pairing.py"):
        if (ROOT / "tests" / t).exists():
            r = subprocess.run([sys.executable, str(ROOT / "tests" / t)])
            if r.returncode != 0:
                print("\n%s fails on the tree as it stands. Read it before committing." % t)
                return r.returncode
    print()
    if "aiii/index.html" in staged:
        print("  git add aiii/index.html")
        print('  git commit -m "aiii: carry the site nav; load the mark face it now draws"')
    if "resume/index.html" in staged:
        print("  git add resume/index.html")
        print('  git commit -m "resume: nav matches the site -- six items, no Resume link (decision #9)"')
    print("Then delete this runner rather than committing it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
