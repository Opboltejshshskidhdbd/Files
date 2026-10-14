#!/usr/bin/env python3
"""ROBLOX UI LINT v2 - static UI analysis for generated Luau (pure Python, no Roblox needed).

What it does
  1. Legacy text rules: emoji/glyph icons, fabricated/repeated asset ids, loading text never hidden, unguarded :Init().
  2. LAYOUT ENGINE: symbolically runs the UI-building code, rebuilds the Instance tree and computes rectangles for
     phone-landscape / phone-portrait / tablet / laptop / desktop viewports. Finds overlapping panels, covered text,
     content outside the screen/parent, UI under the Roblox top bar, clipped/tiny text, small touch targets,
     fixed-pixel layouts that cannot fit phones, low contrast.
Limits (be honest): it is an ESTIMATE of layout, not Roblox. Runtime-created/tweened UI and values it cannot resolve are
skipped (reported as coverage). Passing this lint does not prove the UI looks right on a device.

Usage: python ui_lint.py file.luau [more] [--viewports phone-landscape,desktop] [--json] [--png DIR] [--map] [--fail-on-warn]
Exit code 1 when any FAIL. Add `-- ui-lint: allow-overlap` anywhere to silence intentional overlay overlap findings."""
import re, sys, os, json
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------------ legacy text rules
PICTO = re.compile('[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u2190-\u21FF\u2300-\u23FF\u25A0-\u25FF]')
STRING = re.compile(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`[^`\n]*`")

def strip_comments(code):
    code = re.sub(r'--\[(=*)\[.*?\]\1\]', '', code, flags=re.S)
    return '\n'.join(re.sub(r'--.*$', '', l) if "'" not in l and '"' not in l else strip_line_comment(l) for l in code.split('\n'))

def strip_line_comment(line):
    in_s = None; i = 0
    while i < len(line):
        c = line[i]
        if in_s:
            if c == '\\': i += 2; continue
            if c == in_s: in_s = None
        else:
            if c in '\'"`': in_s = c
            elif line.startswith('--', i): return line[:i]
        i += 1
    return line

def legacy_lint(code, filename='<source>', layout_ran=False):
    out = []
    def add(rule, sev, msg, pos=None):
        out.append({'rule': rule, 'severity': sev, 'message': msg, 'line': (code[:pos].count('\n') + 1) if pos is not None else 0, 'viewports': []})
    src = strip_comments(code)
    manifest_like = bool(re.search(r'asset|icon|manifest', os.path.basename(filename), re.I))
    log_spans = []
    for m in re.finditer(r'\b(print|warn|error)\s*\(', src):
        depth, j = 1, m.end()
        while j < len(src) and depth:
            depth += {'(': 1, ')': -1}.get(src[j], 0); j += 1
        log_spans.append((m.start(), j))
        if PICTO.search(src[m.start():j]):
            add('emoji.in_log', 'FAIL', 'emoji/symbol in print/warn/error renders as an empty box in the output window; use ASCII', m.start())
    if not layout_ran:
        for m in STRING.finditer(src):
            if PICTO.search(m.group(0)) and not any(a <= m.start() < b for a, b in log_spans):
                add('emoji.in_ui_text', 'WARN', 'emoji/symbol in a string may render as an empty box; use an ImageLabel icon or a drawn shape', m.start())
    ids = [(m.group(1), m.start()) for m in re.finditer(r'rbxassetid://(\d+)', src)]
    counts = Counter(i for i, _ in ids)
    for aid, n in counts.items():
        if n >= 3:
            add('asset.repeated_id', 'FAIL', f'asset id {aid} is used {n} times: one id for several items usually means it is fabricated or a copied placeholder', next(p for i, p in ids if i == aid))
    for aid, pos in ids:
        digits = set(aid)
        if len(aid) < 6 or len(digits) <= 3 or aid in ('123456789', '1234567890', '987654321'):
            add('asset.suspicious_id', 'FAIL', f'asset id {aid} looks fabricated (too short or too few distinct digits)', pos)
    if ids and not manifest_like:
        add('asset.id_outside_manifest', 'WARN', 'asset ids should live in an AssetManifest module, not inline in UI code', ids[0][1])
    if not layout_ran:
        if re.search(r'IgnoreGuiInset\s*=\s*true', src) and not re.search(r'ScreenInsets', src):
            m = re.search(r'IgnoreGuiInset\s*=\s*true', src)
            add('ui.topbar_overlap_risk', 'WARN', 'IgnoreGuiInset = true lets interactive UI sit under the Roblox top bar; use ScreenInsets = TopbarSafeInsets unless this is a full-screen overlay', m.start())
        for m in re.finditer(r'TextSize\s*=\s*(\d+)', src):
            if int(m.group(1)) < 12: add('ui.small_text', 'WARN', f'TextSize {m.group(1)} is below the 12 minimum', m.start())
    lm = re.search(r"Text\s*=\s*['\"]Loading", src)
    if lm and not re.search(r'[Ll]oading\w*\.Visible\s*=\s*false|[Ll]oading\w*:Destroy\(\)|[Ll]oading\w*\.Enabled\s*=\s*false', src):
        add('ui.loading_never_hidden', 'WARN', 'a "Loading" element is created but never hidden or destroyed: it can stay on top of the content', lm.start())
    im = re.search(r'\b\w+:(Init|Start)\(', src)
    if im and not re.search(r'\.(Init|Start)\s+then|typeof\([^)]*\.(Init|Start)\)|type\([^)]*\.(Init|Start)\)|\.(Init|Start)\s*(==|~=)', src):
        add('lifecycle.unguarded_init', 'WARN', f"calling :{im.group(1)}() without checking the method exists causes \"attempt to call missing method '{im.group(1)}' of table\" for modules that do not define it", im.start())
    if 'ScreenGui' in src and not re.search(r'ZIndexBehavior', src):
        add('ui.zindex_behavior', 'INFO', 'set ScreenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling so ZIndex is predictable per parent', None)
    return out

# ------------------------------------------------------------------ layout-based rules
DECOR = re.compile(r'(glow|shadow|decor|particle|backdrop|vignette|stroke|gradient|spark|aura|shine|reflection|scanline|bgimage|shimmer|halo)', re.I)
TOAST = re.compile(r'(toast|notif|tooltip|popup|modal|overlay|dialog|snackbar|banner)', re.I)

def enum_name_(v):
    return v[2] if isinstance(v, tuple) and len(v) == 3 and v[0] == 'Enum' else None

def srgb(c): c /= 255; return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
def lum(col): return 0.2126 * srgb(col[1]) + 0.7152 * srgb(col[2]) + 0.0722 * srgb(col[3])
def contrast(a, b):
    la, lb = lum(a), lum(b); hi, lo = max(la, lb), min(la, lb); return (hi + 0.05) / (lo + 0.05)

def analyze_layout(code, filename, viewports, png_dir=None, show_map=False):
    from ui_parse import parse, ParseError
    from ui_interp import Interp, UNK, GUI_CLASSES
    import ui_layout as UL
    findings, info = [], {'parsed': False}
    try:
        ast = parse(code)
    except ParseError as e:
        return findings, {'parsed': False, 'error': str(e)}
    first = UL.VIEWPORTS[viewports[0]]
    interp = Interp(viewport=first, touch=viewports[0].startswith('phone')); interp.run(ast)
    nodes = [n for n in interp.nodes]
    gui = [n for n in nodes if n.cls in GUI_CLASSES and n.cls != 'ScreenGui']
    info.update({'parsed': True, 'nodes': len(nodes), 'gui_nodes': len(gui), 'notes': interp.notes, 'skipped_statements': interp.skipped})
    if not gui:
        findings.append({'rule': 'ui.layout_coverage', 'severity': 'INFO', 'line': 0, 'viewports': [], 'message': 'no UI tree could be extracted statically (UI may be built dynamically or in modules); layout checks skipped'})
        return findings, info
    allow_overlap = bool(re.search(r'ui-lint:\s*allow-overlap', code))
    raw = []  # (key, finding)
    footprints = {}; suppressed = [0]
    flagged_nodes = defaultdict(set)
    total_unresolved = 0
    for vp in viewports:
        if vp == viewports[0]: vp_nodes = nodes
        else:
            vi = Interp(viewport=UL.VIEWPORTS[vp], touch=vp.startswith('phone')); vi.run(ast); vp_nodes = vi.nodes
        L = UL.compute(vp_nodes, vp)
        total_unresolved += L.unresolved
        vw, vh = L.vw, L.vh
        items = L.items
        phone = vp.startswith('phone')
        # effective visibility + ancestors + z keys
        def anc_ids(n):
            s = set(); p = n.parent
            while p is not None: s.add(p.id); p = p.parent
            return s
        anc = {i: anc_ids(it.node) for i, it in items.items()}
        def zkey(n):
            chain = []
            while n is not None:
                z = n.props.get('ZIndex', 1); z = z if isinstance(z, (int, float)) else 1
                sib = n.parent.children.index(n) if n.parent is not None and n in n.parent.children else 0
                chain.append((z, sib)); n = n.parent
            return tuple(reversed(chain))
        zk = {i: zkey(it.node) for i, it in items.items()}
        def eff_visible(n):
            while n is not None:
                if n.props.get('Visible', True) is False: return False
                if n.cls == 'ScreenGui' and n.props.get('Enabled', True) is False: return False
                n = n.parent
            return True
        def vis_rect(it):
            x0, y0, x1, y1 = it.x, it.y, it.x + it.w, it.y + it.h
            c = it.clip
            while c is not None:
                x0, y0, x1, y1 = max(x0, c.x), max(y0, c.y), min(x1, c.x + c.w), min(y1, c.y + c.h); c = c.clip
            return x0, y0, x1, y1
        def num(n, k, d):
            v = n.props.get(k, d); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
        def bg_alpha(n):
            if n.cls not in UL.TEXT_CLASSES | UL.IMAGE_CLASSES | {'Frame', 'ScrollingFrame', 'CanvasGroup', 'ViewportFrame', 'VideoFrame'}: return 0
            return 1 - num(n, 'BackgroundTransparency', 0)
        def is_text(it):
            return bool(it.text) and num(it.node, 'TextTransparency', 0) < 0.9
        def is_image(n):
            if n.cls not in UL.IMAGE_CLASSES: return False
            img = n.props.get('Image', '')
            return (img is UNK or bool(img)) and num(n, 'ImageTransparency', 0) < 0.9
        def interactive(n):
            return n.cls in UL.BUTTON_CLASSES or bool(n.handlers)
        def decor(n):
            m = n
            while m is not None:
                if DECOR.search(m.name): return True
                m = m.parent
            return False
        def has_leaf_desc(n):
            for c in n.children:
                it = items.get(c.id)
                if it and eff_visible(c) and (is_text(it) or is_image(c) or interactive(c)): return True
                if has_leaf_desc(c): return True
            return False
        live = {i: it for i, it in items.items() if eff_visible(it.node)}
        def path(n): return n.path()
        strip_roots = {r.id for r, region, kind in L.roots if kind == 'topbar_strip'}
        def root_id(n):
            while n.parent is not None: n = n.parent
            return n.id
        def add(rule, sev, it_or_node, msg, line=None, partner=''):
            n = it_or_node.node if hasattr(it_or_node, 'node') else it_or_node
            if strip_roots and rule != 'ui.screeninsets_topbar_strip' and root_id(n) in strip_roots:
                suppressed[0] += 1; return
            flagged_nodes[vp].add(n.id)
            raw.append(((rule, path(n), partner), {'rule': rule, 'severity': sev, 'line': line or n.line, 'viewport': vp, 'message': f'{path(n)} - {msg}'}))
        # ---- safe area / ScreenInsets semantics
        for r, region, kind in L.roots:
            rl = [it for it in live.values() if it.root is r]
            if kind == 'topbar_strip':
                tall = [it for it in rl if (bg_alpha(it.node) > 0.2 or is_text(it)) and (it.y + it.h) > region[1] + region[3] + 10]
                clipped_kids = [it for it in rl if it.node.cls in ('ScrollingFrame', 'CanvasGroup')]
                if tall or clipped_kids or len(rl) > 6:
                    add('ui.screeninsets_topbar_strip', 'FAIL', r, f"ScreenInsets = TopbarSafeInsets confines this ScreenGui to the top-bar strip (~{int(region[3])}px high, starting right of the Roblox logo/menu/chat buttons). Full-screen/menu UI collapses to a sliver and ScrollingFrames clip everything. Remove the ScreenInsets line (default CoreUISafeInsets = below the top bar) and keep IgnoreGuiInset = false")
            elif r.cls == 'ScreenGui' and enum_name_(r.props.get('ScreenInsets')) not in (None, 'CoreUISafeInsets', 'None', 'DeviceSafeInsets'):
                add('ui.screeninsets_nondefault', 'WARN', r, 'non-default ScreenInsets value: verify on a real device')
            if kind == 'full':
                zone = (0, 0, UL.TOPBAR_LEFT_W, UL.TOPBAR_H)
                for i, it in live.items():
                    if it.root is not r: continue
                    n = it.node
                    leaf = is_text(it) or is_image(n) or interactive(n)
                    if not leaf: continue
                    x0, y0, x1, y1 = vis_rect(it)
                    ox = max(0, min(x1, zone[2]) - max(x0, zone[0])); oy = max(0, min(y1, zone[3]) - max(y0, zone[1]))
                    if ox * oy >= 120 and ox * oy >= 0.12 * max((x1 - x0) * (y1 - y0), 1):
                        add('ui.topbar_overlap', 'FAIL', it, f'sits under the Roblox top-bar buttons (logo/menu/chat) on {vp}; leave IgnoreGuiInset = false (default CoreUISafeInsets) or start content below y={UL.TOPBAR_H}')
        # ---- collapsed containers (content hidden by a tiny parent) + footprint
        def desc_extent(n):
            mb = 0; cnt = 0
            stack = list(n.children)
            while stack:
                c = stack.pop(); ci = items.get(c.id)
                if ci and eff_visible(c) and (is_text(ci) or is_image(c) or interactive(c) or bg_alpha(c) > 0.2):
                    mb = max(mb, ci.y + ci.h); cnt += 1
                stack.extend(c.children)
            return mb, cnt
        for i, it in live.items():
            n = it.node
            if n.cls not in ('Frame', 'ScrollingFrame', 'CanvasGroup') or not n.children: continue
            mb, cnt = desc_extent(n)
            if cnt == 0: continue
            clip = n.props.get('ClipsDescendants') is True or n.cls in ('ScrollingFrame', 'CanvasGroup')
            for dim, size in (('height', it.h), ('width', it.w)):
                if size < 16 and (n.cls == 'ScrollingFrame' or clip or (bg_alpha(n) > 0.2 and dim == 'height' and mb - it.y > 60)):
                    sev = 'FAIL' if clip else 'WARN'
                    add('ui.collapsed_container', sev, it, f"is only {int(size)}px {dim} on {vp} but holds {cnt} visible elements{' (clipped: they are hidden)' if clip else ''} - a parent size/ScreenGui area/scale math collapses it; fix the Size (check negative offsets and ScreenInsets)")
                    break
        surf = [it for it in live.values() if bg_alpha(it.node) > 0.2 and it.w >= 40 and it.h >= 40 and it.node.parent is not None and it.node.parent.cls != 'ScreenGui' or (bg_alpha(it.node) > 0.2 and it.w >= 40 and it.h >= 40)]
        if surf:
            x0 = min(max(i.x, 0) for i in surf); y0 = min(max(i.y, 0) for i in surf)
            x1 = max(min(i.x + i.w, vw) for i in surf); y1 = max(min(i.y + i.h, vh) for i in surf)
            foot = max(x1 - x0, 0) * max(y1 - y0, 0) / (vw * vh)
            footprints[vp] = foot
        # ---- offscreen / overflow
        for i, it in live.items():
            n = it.node
            surf = bg_alpha(n) > 0.2 or is_text(it) or is_image(n) or interactive(n)
            if not surf: continue
            if it.w <= 0 or it.h <= 0: continue
            x0, y0, x1, y1 = it.x, it.y, it.x + it.w, it.y + it.h
            if it.clip is not None and not it.in_scroll_y and not it.in_scroll_x: pass
            over_l, over_t = -x0, -y0
            over_r, over_b = x1 - vw, y1 - vh
            if it.in_scroll_x: over_l = over_r = 0
            if it.in_scroll_y: over_t = over_b = 0
            worst = max(over_l, over_t, over_r, over_b)
            par = n.parent
            pit = items.get(par.id) if par is not None else None
            if worst > 8:
                # report only the top-most offender
                if pit is not None:
                    pl, pt_, pr, pb = -pit.x, -pit.y, pit.x + pit.w - vw, pit.y + pit.h - vh
                    if max(pl, pt_, pr, pb) >= worst - 2 and not it.in_scroll_y and eff_visible(par): continue
                side = max((over_l, 'left'), (over_t, 'top'), (over_r, 'right'), (over_b, 'bottom'))[1]
                sev = 'FAIL' if (worst >= 20 or worst >= 0.1 * min(it.w, it.h)) else 'WARN'
                add('ui.offscreen', sev, it, f'extends {int(worst)}px past the {side} edge of the {vp} screen ({vw}x{vh}); content is cut off - use scale sizes, UISizeConstraint, a ScrollingFrame or a compact layout for small screens')
        for i, it in live.items():
            n = it.node; par = n.parent
            if par is None or par.id not in items or it.in_scroll_y or it.in_scroll_x: continue
            pit = items[par.id]
            if par.cls == 'ScreenGui': continue
            leaf = is_text(it) or is_image(n) or interactive(n)
            if not leaf: continue
            ex = max(pit.x - it.x, pit.y - it.y, (it.x + it.w) - (pit.x + pit.w), (it.y + it.h) - (pit.y + pit.h))
            if ex > 6 and bg_alpha(par) > 0.2 and not decor(n):
                clipped = pit.node.props.get('ClipsDescendants') is True
                add('ui.overflow_parent', 'FAIL' if (clipped or ex > 14) else 'WARN', it, f"overflows its panel '{par.name}' by {int(ex)}px on {vp}" + (' and is clipped (ClipsDescendants)' if clipped else ''))
        # ---- overlap / covered
        if not allow_overlap:
            lst = [(i, it) for i, it in live.items() if it.w >= 6 and it.h >= 6]
            leaves = [(i, it) for i, it in lst if (is_text(it) or is_image(it.node) or interactive(it.node)) and not decor(it.node) and not TOAST.search(it.node.name)]
            conts = [(i, it) for i, it in lst if bg_alpha(it.node) >= 0.5 and it.w >= 40 and it.h >= 40 and not decor(it.node) and it.node.cls != 'ScrollingFrame' or (bg_alpha(it.node) >= 0.5 and it.w >= 40 and it.h >= 40 and not decor(it.node))]
            def inter(a, b):
                ax0, ay0, ax1, ay1 = vis_rect(a); bx0, by0, bx1, by1 = vis_rect(b)
                w = min(ax1, bx1) - max(ax0, bx0); h = min(ay1, by1) - max(ay0, by0)
                return w * h if w > 0 and h > 0 else 0
            def area(it):
                x0, y0, x1, y1 = vis_rect(it); return max(x1 - x0, 0) * max(y1 - y0, 0)
            seen = set(); covered_leaves = set(); flagged_pairs = []
            depth = lambda it: it.node.path().count('.')
            conts.sort(key=lambda x: depth(x[1]))
            # 1) text/buttons/images hidden by a panel drawn above them
            for ia, ita in leaves:
                reported_by = []
                for ic, itc in conts:
                    if ita.root is not itc.root or ic in anc[ia] or ia in anc[ic] or ic == ia: continue
                    if zk[ic] <= zk[ia]: continue
                    ov = inter(ita, itc)
                    if ov <= 0 or ov / (area(ita) or 1) < 0.25 or ov < 80: continue
                    if any(rc in anc[ic] for rc in reported_by): continue   # parent panel already reported
                    reported_by.append(ic); covered_leaves.add(ia)
                    what = 'button' if interactive(ita.node) else ('text' if is_text(ita) else 'image')
                    add('ui.covered', 'FAIL', ita, f"{what} is covered by '{itc.node.name}' ({int(100 * ov / area(ita))}% hidden) on {vp}: the panel is drawn above it - separate their regions or fix ZIndex/layout", partner=itc.node.name)
            # 2) two readable/clickable things on the same spot
            for a in range(len(leaves)):
                ia, ita = leaves[a]
                for b in range(a + 1, len(leaves)):
                    ib, itb = leaves[b]
                    if ita.root is not itb.root or ib in anc[ia] or ia in anc[ib]: continue
                    if ia in covered_leaves or ib in covered_leaves: continue
                    if any(p in covered_leaves for p in (ia, ib)): continue
                    ov = inter(ita, itb)
                    if ov <= 0: continue
                    m = min(area(ita), area(itb)) or 1
                    if ov / m >= 0.25 and ov >= 80:
                        key = frozenset((ia, ib))
                        if key in seen: continue
                        seen.add(key)
                        top, other = (itb, ita) if zk[ib] > zk[ia] else (ita, itb)
                        add('ui.overlap', 'FAIL', top, f"overlaps '{other.node.name}' by {int(100 * ov / m)}% on {vp}: two readable/clickable elements occupy the same space - re-layout with UIListLayout/UIGridLayout or reserve separate regions", partner=other.node.name)
            # 3) panels stacked on panels
            for a in range(len(conts)):
                ia, ita = conts[a]
                for b in range(a + 1, len(conts)):
                    ib, itb = conts[b]
                    if ita.root is not itb.root or ib in anc[ia] or ia in anc[ib]: continue
                    ov = inter(ita, itb)
                    m = min(area(ita), area(itb)) or 1
                    if ov > 0 and ov / m >= 0.2 and ov >= 1600:
                        if any((pa in anc[ia] | {ia}) and (pb in anc[ib] | {ib}) or (pb in anc[ia] | {ia}) and (pa in anc[ib] | {ib}) for pa, pb in flagged_pairs): continue
                        flagged_pairs.append((ia, ib))
                        both = has_leaf_desc(ita.node) and has_leaf_desc(itb.node)
                        top, other = (itb, ita) if zk[ib] > zk[ia] else (ita, itb)
                        add('ui.panel_overlap', 'FAIL' if both else 'WARN', top, f"panel overlaps '{other.node.name}' by {int(100 * ov / m)}% on {vp}: panels should not stack on top of each other unless one is an intentional overlay (name it ...Overlay/Toast or add `-- ui-lint: allow-overlap`)", partner=other.node.name)
            # toasts / popups over content
            for ia, ita in lst:
                if not TOAST.search(ita.node.name) or ita.node.parent is None: continue
                for ib, itb in leaves:
                    if ita.root is not itb.root or ib in anc[ia] or ia in anc[ib] or TOAST.search(itb.node.name): continue
                    if any(TOAST.search(p.name) for p in _ancestors(itb.node)): continue
                    ov = inter(ita, itb)
                    if ov >= 200 and ov / (area(itb) or 1) >= 0.3:
                        add('ui.toast_overlap', 'WARN', ita, f"overlay/toast covers '{itb.node.name}' on {vp}: anchor it in a free corner (below the top bar) or push content aside")
                        break
        # ---- text rules
        for i, it in live.items():
            n = it.node
            if not is_text(it): continue
            tm = it.text
            size = tm['size']
            if size < 10: add('ui.text_small', 'FAIL', it, f"effective text size {size:.0f}px on {vp} is unreadable (minimum 12px); raise TextSize/MinTextSize or use a compact layout")
            elif size < 12: add('ui.text_small', 'WARN', it, f"effective text size {size:.0f}px on {vp} is below 12px")
            if not tm['scaled']:
                if not tm['wrapped'] and tm['lines'] == 1 and tm['natural_w'] > it.w * 1.06 and it.w > 0 and enum_trunc(n) == 'AtEnd':
                    add('ui.text_truncated', 'WARN', it, f"text '{tm['text'][:28]}' needs ~{int(tm['natural_w'])}px but the box is {int(it.w)}px wide on {vp}: it will be cut with '...' - widen the box or shorten the text")
                elif not tm['wrapped'] and tm['lines'] == 1 and tm['natural_w'] > it.w * 1.06 and it.w > 0:
                    ratio = tm['natural_w'] / it.w
                    add('ui.text_overflow', 'FAIL' if ratio > 1.15 else 'WARN', it, f"text '{tm['text'][:28]}' needs ~{int(tm['natural_w'])}px but the box is {int(it.w)}px wide on {vp}: it will spill over or clip - widen the box, enable TextWrapped/TextScaled+UITextSizeConstraint, or shorten")
                elif tm['wrapped'] and tm['h'] > it.h * 1.12 and it.h > 0:
                    add('ui.text_overflow', 'FAIL' if tm['h'] > it.h * 1.3 else 'WARN', it, f"wrapped text '{tm['text'][:28]}' needs ~{int(tm['h'])}px height but the box is {int(it.h)}px on {vp}: increase height or use AutomaticSize.Y")
            if it.w > 0 and not n.props.get('TextColor3') in (None, UNK):
                tc = n.props.get('TextColor3'); bgc = None; m = n
                while m is not None and bgc is None:
                    col = m.props.get('BackgroundColor3')
                    if isinstance(col, tuple) and col and col[0] == 'Color' and bg_alpha(m) >= 0.5: bgc = col
                    elif col is UNK and bg_alpha(m) >= 0.5: break
                    m = m.parent
                if isinstance(tc, tuple) and tc and tc[0] == 'Color' and bgc:
                    cr = contrast(tc, bgc)
                    if cr < 3.0: add('ui.contrast', 'FAIL' if cr < 1.6 else 'WARN', it, f"text/background contrast {cr:.1f}:1 is too low (aim for >= 4.5:1, minimum 3:1)")
        # ---- touch targets (phones)
        if phone:
            for i, it in live.items():
                n = it.node
                if n.cls in UL.BUTTON_CLASSES or (n.handlers and n.cls in GUI_CLASSES):
                    m = min(it.w, it.h)
                    if m < 24: add('ui.touch_target', 'FAIL', it, f"tap target is only {int(it.w)}x{int(it.h)}px on {vp} (minimum ~40px)")
                    elif m < 38: add('ui.touch_target', 'WARN', it, f"tap target is {int(it.w)}x{int(it.h)}px on {vp}; aim for >= 40px")
        # ---- fixed pixel sizes that cannot fit phones
        if phone:
            for i, it in live.items():
                n = it.node
                if n.cls not in ('Frame', 'ScrollingFrame', 'CanvasGroup', 'ImageLabel'): continue
                sz = n.props.get('Size')
                if not (isinstance(sz, tuple) and sz and sz[0] == 'UDim2'): continue
                if anc_has(n, 'UIScale') or n.parent is None: pass
                px_w = sz[1] == 0 and sz[2] >= 0.9 * vw; px_h = sz[3] == 0 and sz[4] >= 0.9 * vh
                if (px_w or px_h) and not _has_mod(n, 'UISizeConstraint') and not anc_has(n, 'UIScale') and not _has_mod(n, 'UIAspectRatioConstraint') and not _has_mod(n, 'UIScale'):
                    add('ui.fixed_size_too_big', 'FAIL', it, f"fixed pixel size {int(sz[2])}x{int(sz[4])} does not fit the {vp} screen ({vw}x{vh}); use scale sizes + UISizeConstraint or a responsive layout")
        if png_dir:
            try: render_png(L, os.path.join(png_dir, f"{os.path.splitext(os.path.basename(filename))[0]}-{vp}.png"), flagged_nodes[vp], live)
            except Exception as e: info.setdefault('png_error', str(e))
        if show_map:
            print(f"\n--- layout map [{vp} {vw}x{vh}] ---")
            for i, it in live.items():
                n = it.node
                print(f"  {'  ' * min(n.path().count('.'), 8)}{n.cls:<14} {n.name[:24]:<24} x={it.x:7.0f} y={it.y:7.0f} w={it.w:6.0f} h={it.h:6.0f}")
    # merge identical findings across viewports
    merged = {}
    for key, f in raw:
        if key not in merged:
            merged[key] = dict(f); merged[key]['viewports'] = [f['viewport']]
        else:
            if f['viewport'] not in merged[key]['viewports']: merged[key]['viewports'].append(f['viewport'])
            if f['severity'] == 'FAIL': merged[key]['severity'] = 'FAIL'
    for f in merged.values():
        f.pop('viewport', None); findings.append(f)
    if suppressed[0]:
        findings.append({'rule': 'ui.consequential_hidden', 'severity': 'INFO', 'line': 0, 'viewports': [], 'message': f'{suppressed[0]} layout findings hidden because they are consequences of ui.screeninsets_topbar_strip; fix that first and re-run'})
    if footprints and not suppressed[0]:
        small = {k: v for k, v in footprints.items() if v < 0.35}
        findings.append({'rule': 'ui.footprint', 'severity': 'WARN' if small else 'INFO', 'line': 0, 'viewports': list(small) if small else [],
                         'message': 'screen coverage of the main UI block: ' + ', '.join(f"{k} {int(v * 100)}%" for k, v in footprints.items()) + (' - the UI occupies only a small part of the screen on ' + ', '.join(small) + ' (check insets/sizes); HUD-style UIs may do this on purpose' if small else '')})
    cov = f"layout engine placed {sum(1 for _ in gui)} UI objects across {len(viewports)} viewports; unresolved property reads: {total_unresolved // max(len(viewports), 1)}; skipped statements: {interp.skipped}"
    if interp.notes: cov += '; ' + '; '.join(sorted(set(interp.notes))[:3])
    findings.append({'rule': 'ui.layout_coverage', 'severity': 'INFO', 'line': 0, 'viewports': [], 'message': cov + ' (estimate only; runtime/tweened layout not simulated)'})
    # sloppy-default checks
    for n in gui:
        if n.cls in ('TextLabel', 'TextButton', 'TextBox') and 'Size' not in n.props and n.props.get('Size') is not UNK and not (n.parent is not None and any(c.cls == 'UIGridLayout' for c in n.parent.children)):
            findings.append({'rule': 'ui.default_size', 'severity': 'WARN', 'line': n.line, 'viewports': [], 'message': f'{n.path()} - no Size set: Roblox default 200x50 px is used, which is rarely intended'})
    # emoji/glyph icons using resolved nodes
    for n in gui:
        t = n.props.get('Text')
        if isinstance(t, str) and t.strip():
            core = t.strip()
            glyphs = len(PICTO.findall(core))
            if glyphs and (len(core) <= 4 or glyphs / max(len(core), 1) >= 0.5):
                findings.append({'rule': 'ui.glyph_icon', 'severity': 'FAIL', 'line': n.line, 'viewports': [], 'message': f"{n.path()} - emoji/symbol '{core}' used as an icon: it renders as an empty box or inconsistent glyph on many devices; use an ImageLabel with a verified asset or draw the icon with Frames"})
            elif glyphs:
                findings.append({'rule': 'emoji.in_ui_text', 'severity': 'WARN', 'line': n.line, 'viewports': [], 'message': f"{n.path()} - emoji/symbol inside text may render as an empty box"})
    return findings, info

def enum_trunc(n):
    v = n.props.get('TextTruncate')
    return v[2] if isinstance(v, tuple) and len(v) == 3 and v[0] == 'Enum' else None

def _ancestors(n):
    out = []; p = n.parent
    while p is not None: out.append(p); p = p.parent
    return out
def _has_mod(n, cls): return any(c.cls == cls for c in n.children)
def anc_has(n, cls): return any(_has_mod(p, cls) for p in _ancestors(n))

# ------------------------------------------------------------------ PNG preview
def render_png(L, path, flagged, live):
    from PIL import Image, ImageDraw, ImageFont
    import ui_layout as UL
    from ui_interp import UNK
    sc = 1.0 if L.vw <= 1100 else 0.6
    W, H = int(L.vw * sc), int(L.vh * sc)
    img = Image.new('RGBA', (W, H), (46, 52, 64, 255)); d = ImageDraw.Draw(img, 'RGBA')
    try: font = ImageFont.load_default()
    except Exception: font = None
    for r, region, kind in L.roots:
        d.rectangle([region[0] * sc, region[1] * sc, (region[0] + region[2]) * sc, (region[1] + region[3]) * sc], outline=(80, 160, 255, 220) if kind != 'full' else (120, 255, 120, 160))
        if kind == 'full': d.rectangle([0, 0, UL.TOPBAR_LEFT_W * sc, UL.TOPBAR_H * sc], fill=(255, 80, 80, 70), outline=(255, 80, 80, 200))
        elif kind == 'core': d.rectangle([0, 0, W, region[1] * sc], fill=(255, 255, 255, 25))
    def zkey(n):
        chain = []
        while n is not None:
            z = n.props.get('ZIndex', 1); z = z if isinstance(z, (int, float)) else 1
            sib = n.parent.children.index(n) if n.parent is not None and n in n.parent.children else 0
            chain.append((z, sib)); n = n.parent
        return tuple(reversed(chain))
    for i, it in sorted(live.items(), key=lambda kv: zkey(kv[1].node)):
        n = it.node
        a = 1 - (n.props.get('BackgroundTransparency', 0) if isinstance(n.props.get('BackgroundTransparency', 0), (int, float)) else 0)
        col = n.props.get('BackgroundColor3'); col = col if isinstance(col, tuple) and col and col[0] == 'Color' else ('Color', 90, 90, 100)
        box = [it.x * sc, it.y * sc, (it.x + it.w) * sc, (it.y + it.h) * sc]
        if a > 0.02: d.rectangle(box, fill=(col[1], col[2], col[3], int(255 * a)))
        d.rectangle(box, outline=(255, 40, 40, 255) if i in flagged else (255, 255, 255, 40), width=2 if i in flagged else 1)
        if it.text and font:
            tc = n.props.get('TextColor3'); tc = tc if isinstance(tc, tuple) and tc and tc[0] == 'Color' else ('Color', 235, 235, 235)
            txt = it.text['text'].replace('\n', ' ')[:max(int(it.w * sc / 6), 1)]
            d.text((box[0] + 2, box[1] + max((box[3] - box[1]) / 2 - 5, 0)), txt, fill=(tc[1], tc[2], tc[3], 255), font=font)
    d.rectangle([0, 0, W - 1, H - 1], outline=(255, 255, 255, 160))
    img.convert('RGB').save(path)

# ------------------------------------------------------------------ public API + CLI
def lint(code, filename='<source>', viewports=None, png_dir=None, show_map=False):
    """Returns list of findings {rule, severity (FAIL/WARN/INFO), line, message, viewports}."""
    viewports = viewports or list(__import__('ui_layout').VIEWPORTS)
    layout_findings, info = [], {'parsed': False}
    try:
        layout_findings, info = analyze_layout(code, filename, viewports, png_dir, show_map)
    except Exception as e:  # never crash the pipeline
        info = {'parsed': False, 'error': f'layout engine error: {e}'}
    ran = info.get('parsed') and any(f['rule'] != 'ui.layout_coverage' or 'no UI tree' not in f['message'] for f in layout_findings) and info.get('gui_nodes', 0) > 0
    out = legacy_lint(code, filename, layout_ran=bool(ran)) + layout_findings
    if not info.get('parsed'):
        out.append({'rule': 'ui.layout_unchecked', 'severity': 'FAIL', 'line': 0, 'viewports': [], 'message': f"LAYOUT NOT CHECKED: the layout engine could not analyze this file ({info.get('error', 'unknown')}). Only text rules ran, so overlap/size/safe-area problems are NOT ruled out. Do not report the UI as lint-passed; fix the syntax or test on device."})
    order = {'FAIL': 0, 'WARN': 1, 'INFO': 2}
    out.sort(key=lambda f: (order[f['severity']], f['line'], f['rule']))
    return out

def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    opts = {a.split('=')[0]: (a.split('=', 1)[1] if '=' in a else True) for a in argv if a.startswith('--')}
    # support "--viewports a,b" and "--png dir" (space separated)
    for flag in ('--viewports', '--png'):
        if flag in argv and opts.get(flag) is True:
            i = argv.index(flag)
            if i + 1 < len(argv): opts[flag] = argv[i + 1]; args = [a for a in args if a != argv[i + 1]]
    if not args:
        print(__doc__); return 2
    import ui_layout as UL
    vps = opts.get('--viewports'); vps = [v for v in vps.split(',') if v in UL.VIEWPORTS] if isinstance(vps, str) else list(UL.VIEWPORTS)
    png = opts.get('--png') if isinstance(opts.get('--png'), str) else None
    if png: os.makedirs(png, exist_ok=True)
    bad = warn = 0; report = {}
    for p in args:
        res = lint(open(p, encoding='utf-8', errors='replace').read(), p, vps, png, bool(opts.get('--map')))
        report[p] = res
        if not opts.get('--json'):
            limit = None if opts.get('--all') else 28
            shown = 0
            for f in res:
                if f['severity'] == 'INFO' and f['rule'] != 'ui.layout_coverage' and limit: continue
                if limit and shown >= limit and f['rule'] != 'ui.layout_coverage': continue
                vp = f" [{', '.join(f['viewports'])}]" if f.get('viewports') else ''
                print(f"{p}:{f['line']}: {f['severity']} {f['rule']}{vp}: {f['message']}"); shown += 1
            nf = sum(f['severity'] == 'FAIL' for f in res); nw = sum(f['severity'] == 'WARN' for f in res)
            by_rule = Counter(f['rule'] for f in res if f['severity'] in ('FAIL', 'WARN'))
            hidden = sum(1 for f in res if f['severity'] in ('FAIL', 'WARN')) - sum(1 for f in res[:0])
            print(f"SUMMARY {p}: {nf} FAIL, {nw} WARN | " + ', '.join(f"{r} x{c}" for r, c in by_rule.most_common()) + (" | showing first 28 (use --all for everything)" if limit and (nf + nw) > limit else "") + " | layout is an estimate, not a runtime test")
        bad += sum(f['severity'] == 'FAIL' for f in res); warn += sum(f['severity'] == 'WARN' for f in res)
    if opts.get('--json'): print(json.dumps(report, indent=2))
    return 1 if (bad or (opts.get('--fail-on-warn') and warn)) else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
