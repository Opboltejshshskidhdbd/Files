"""Approximate Roblox GUI layout engine. Takes the Node tree from ui_interp and computes absolute rectangles for a
given viewport (UDim2 sizes, AnchorPoint, UIListLayout, UIGridLayout, UIPadding, UISizeConstraint, UIAspectRatioConstraint,
UIScale, AutomaticSize, ScrollingFrame canvas, text measurement). It is an ESTIMATE, not Roblox itself."""
import math
from ui_interp import Node, UNK, GUI_CLASSES, MODIFIER_CLASSES

VIEWPORTS = {'phone-small': (640, 360), 'phone-landscape': (800, 360), 'phone-large': (932, 430), 'phone-portrait': (360, 780), 'tablet': (1024, 768), 'laptop': (1366, 768), 'desktop': (1920, 1080)}
TOPBAR_H = 58          # Roblox top bar height (px) used for inset / overlap checks
TOPBAR_LEFT_W = 172    # logo + menu + chat cluster width on the left
TEXT_CLASSES = {'TextLabel', 'TextButton', 'TextBox'}
IMAGE_CLASSES = {'ImageLabel', 'ImageButton'}
BUTTON_CLASSES = {'TextButton', 'ImageButton'}
DEFAULT_SIZE = {'Frame': (0, 100, 0, 100), 'TextLabel': (0, 200, 0, 50), 'TextButton': (0, 200, 0, 50), 'TextBox': (0, 200, 0, 50),
                'ImageLabel': (0, 100, 0, 100), 'ImageButton': (0, 100, 0, 100), 'ScrollingFrame': (0, 100, 0, 100),
                'CanvasGroup': (0, 100, 0, 100), 'ViewportFrame': (0, 100, 0, 100), 'VideoFrame': (0, 100, 0, 100)}
FONT_W = {'gotham': 0.54, 'gothambold': 0.58, 'gothamblack': 0.62, 'gothamsemibold': 0.56, 'sourcesans': 0.47, 'sourcesansbold': 0.5,
          'arial': 0.52, 'arialbold': 0.55, 'montserrat': 0.6, 'code': 0.6, 'ubuntu': 0.52, 'fredokaone': 0.58, 'builder': 0.54}

def enum_name(v):
    if isinstance(v, tuple) and len(v) == 3 and v[0] == 'Enum': return v[2]
    return None

class Item:
    __slots__ = ('node', 'x', 'y', 'w', 'h', 'scale', 'in_scroll_y', 'in_scroll_x', 'clip', 'text', 'root')
    def __init__(self, node, root): self.node, self.root = node, root; self.scale = 1.0; self.in_scroll_y = self.in_scroll_x = False; self.clip = None; self.text = None

class Layouter:
    def __init__(self, vp_name, vw, vh):
        self.vp_name, self.vw, self.vh = vp_name, vw, vh
        self.items = {}; self.unresolved = 0; self.roots = []
    # ---- property helpers ----
    def P(self, n, key, default=None):
        v = n.props.get(key, default)
        if v is UNK:
            self.unresolved += 1; return default
        return v
    def udim2(self, n, key, default):
        v = self.P(n, key, None)
        return v if isinstance(v, tuple) and v and v[0] == 'UDim2' else default
    def mod(self, n, cls):
        for c in n.children:
            if c.cls == cls: return c
        return None
    def num(self, n, key, default):
        v = self.P(n, key, None); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else default
    def udim(self, v, axis):
        if isinstance(v, tuple) and v and v[0] == 'UDim': return v[1] * axis + v[2]
        return 0
    def is_gui(self, n): return n.cls in GUI_CLASSES and n.cls not in ('ScreenGui', 'SurfaceGui', 'BillboardGui')
    def visible(self, n): return self.P(n, 'Visible', True) is not False
    # ---- paddings ----
    def padding(self, n, w, h):
        p = self.mod(n, 'UIPadding')
        if not p: return (0, 0, 0, 0)
        g = lambda k, ax: self.udim(p.props.get(k), ax) if not isinstance(p.props.get(k), type(UNK)) else 0
        return (g('PaddingLeft', w), g('PaddingTop', h), g('PaddingRight', w), g('PaddingBottom', h))
    # ---- text ----
    def font_factor(self, n):
        f = n.props.get('Font')
        key = ''
        if isinstance(f, tuple) and f and f[0] == 'Font': key = str(f[1]).lower().replace(' ', '')
        elif enum_name(f): key = enum_name(f).lower()
        for k in sorted(FONT_W, key=len, reverse=True):
            if k in key: return FONT_W[k]
        return 0.56
    def text_str(self, n):
        t = n.props.get('Text', '' if n.cls != 'TextBox' else n.props.get('PlaceholderText', ''))
        return t if isinstance(t, str) else None
    def text_width(self, text, size, ff):
        w = 0.0
        for ch in text:
            if ord(ch) > 0x2000: w += size * 1.05
            elif ch.isupper(): w += size * ff * 1.18
            elif ch == ' ': w += size * ff * 0.55
            elif ch in 'il.,;:!|\'': w += size * ff * 0.5
            elif ch in 'mwMW': w += size * ff * 1.35
            else: w += size * ff
        return w
    def text_metrics(self, n, box_w, box_h, scale=1.0, wrap_w=None):
        text = self.text_str(n)
        if text is None or text == '': return None
        size = self.num(n, 'TextSize', 14); ff = self.font_factor(n)
        wrapped = self.P(n, 'TextWrapped', False) is True; scaled = self.P(n, 'TextScaled', False) is True
        lh = self.num(n, 'LineHeight', 1.0) * 1.15
        tsc = self.mod(n, 'UITextSizeConstraint')
        lo = hi = None
        if tsc:
            hi = self.num(tsc, 'MaxTextSize', None); lo = self.num(tsc, 'MinTextSize', None)
        def lines_for(sz, avail):
            tw = self.text_width(text, sz, ff)
            if wrapped or scaled:
                words = text.split(' '); lines, cur = 1, 0.0
                for wd in words:
                    ww = self.text_width(wd + ' ', sz, ff)
                    if cur + ww > avail + 0.5 and cur > 0: lines += 1; cur = ww
                    else: cur += ww
                lines += text.count('\n')
                return lines, min(tw, avail)
            lines = 1 + text.count('\n')
            return lines, tw
        avail = wrap_w if wrap_w is not None else box_w
        if scaled:
            best = 1
            for sz in range(100, 0, -1):
                ln, tw = lines_for(sz, avail)
                if ln * sz * lh <= box_h + 0.5 and (tw <= avail + 0.5 or ln > 1): best = sz; break
            if hi: best = min(best, hi)
            if lo: best = max(best, lo)
            size_eff = best
        else:
            size_eff = size
        ln, tw = lines_for(size_eff, avail)
        return {'size': size_eff * scale, 'w': tw * scale, 'h': ln * size_eff * lh * scale, 'lines': ln, 'wrapped': wrapped, 'scaled': scaled, 'text': text, 'natural_w': self.text_width(text, size_eff, ff) * scale}
    # ---- measure ----
    def uiscale(self, n):
        m = self.mod(n, 'UIScale')
        if not m: return 1.0
        v = m.props.get('Scale', 1); return v if isinstance(v, (int, float)) and v > 0 else 1.0
    def constrain(self, n, w, h):
        sc = self.mod(n, 'UISizeConstraint')
        if sc:
            mn = sc.props.get('MinSize'); mx = sc.props.get('MaxSize')
            if isinstance(mn, tuple) and mn[0] == 'V2': w = max(w, mn[1]); h = max(h, mn[2])
            if isinstance(mx, tuple) and mx[0] == 'V2': w = min(w, mx[1]); h = min(h, mx[2])
        ar = self.mod(n, 'UIAspectRatioConstraint')
        if ar:
            r = ar.props.get('AspectRatio', 1)
            if isinstance(r, (int, float)) and r > 0:
                at = enum_name(ar.props.get('AspectType')) or 'FitWithinMaxSize'
                da = enum_name(ar.props.get('DominantAxis')) or 'Width'
                if at == 'ScaleWithParentSize':
                    pass
                if da == 'Width': h = w / r
                elif da == 'Height': w = h * r
                else:
                    if w / r > h: w = h * r
                    else: h = w / r
        return w, h
    def measure(self, n, pw, ph, k=1.0):
        d = DEFAULT_SIZE.get(n.cls, (0, 100, 0, 100))
        sz = self.udim2(n, 'Size', ('UDim2',) + d)
        if 'Size' not in n.props and n.cls in TEXT_CLASSES and False: pass
        w = max(sz[1] * pw + sz[2], 0); h = max(sz[3] * ph + sz[4], 0)
        auto = enum_name(n.props.get('AutomaticSize')) or 'None'
        ax = auto in ('X', 'XY'); ay = auto in ('Y', 'XY')
        if ax or ay:
            pl, pt, pr, pb = self.padding(n, w, h)
            if n.cls in TEXT_CLASSES and self.text_str(n):
                tm = self.text_metrics(n, max(w - pl - pr, 1), max(h - pt - pb, 1), wrap_w=(w - pl - pr) if not ax else None)
                if tm:
                    if ax: w = tm['natural_w'] + pl + pr
                    if ay: h = tm['h'] + pt + pb
                    if n.cls == 'TextBox': pass
            else:
                ext = self.extent(n, w - pl - pr, h - pt - pb)
                if ax: w = ext[0] + pl + pr
                if ay: h = ext[1] + pt + pb
        w, h = self.constrain(n, w, h)
        s = self.uiscale(n)
        return w * s, h * s
    def children_gui(self, n):
        return [c for c in n.children if self.is_gui(c) and self.visible(c)]
    def sorted_children(self, n, lay):
        ch = self.children_gui(n)
        so = enum_name(lay.props.get('SortOrder')) if lay else None
        idx = {c.id: i for i, c in enumerate(ch)}
        if so == 'LayoutOrder': ch.sort(key=lambda c: (self.num(c, 'LayoutOrder', 0), idx[c.id]))
        elif so == 'Name' or so is None: ch.sort(key=lambda c: (c.name, idx[c.id])) if (so == 'Name') else None
        return ch
    def extent(self, n, cw, ch):
        """max right/bottom of children relative to content origin."""
        rects = self.arrange(n, 0, 0, max(cw, 0), max(ch, 0))
        mw = mh = 0
        for c, x, y, w, h in rects:
            mw = max(mw, x + w); mh = max(mh, y + h)
        lay = self.mod(n, 'UIListLayout') or self.mod(n, 'UIGridLayout')
        if lay and rects:
            pass
        return mw, mh
    # ---- arrange children: returns [(child, x, y, w, h)] relative to given origin ----
    def arrange(self, n, ox, oy, cw, ch):
        lst = self.mod(n, 'UIListLayout'); grid = self.mod(n, 'UIGridLayout')
        out = []
        if lst:
            kids = self.sorted_children(n, lst)
            vertical = (enum_name(lst.props.get('FillDirection')) or 'Vertical') == 'Vertical'
            pad = self.udim(lst.props.get('Padding'), (ch if vertical else cw))
            ha = enum_name(lst.props.get('HorizontalAlignment')) or 'Left'; va = enum_name(lst.props.get('VerticalAlignment')) or 'Top'
            wraps = lst.props.get('Wraps') is True
            flex_h = enum_name(lst.props.get('HorizontalFlex')); flex_v = enum_name(lst.props.get('VerticalFlex'))
            sizes = [self.measure(c, cw, ch) for c in kids]
            flex = (flex_v if vertical else flex_h) or 'None'
            if flex == 'Fill' and kids:
                total = sum((s[1] if vertical else s[0]) for s in sizes) + pad * (len(kids) - 1)
                free = (ch if vertical else cw) - total
                # items with UIFlexItem Fill grow equally, otherwise all grow
                growers = [i for i, c in enumerate(kids) if (self.mod(c, 'UIFlexItem') is not None)] or list(range(len(kids)))
                if free > 0 and growers:
                    add = free / len(growers)
                    for i in growers:
                        w, h = sizes[i]; sizes[i] = (w, h + add) if vertical else (w + add, h)
            # lines (wrap)
            lines = [[]]; cur = 0.0
            for i, c in enumerate(kids):
                main = sizes[i][1] if vertical else sizes[i][0]
                if wraps and lines[-1] and cur + pad + main > (ch if vertical else cw) + 0.5:
                    lines.append([]); cur = 0.0
                lines[-1].append(i); cur += (pad if lines[-1][:-1] else 0) + main
            cross_cur = 0.0; blocks = []
            for ln in lines:
                main_total = sum((sizes[i][1] if vertical else sizes[i][0]) for i in ln) + pad * (len(ln) - 1)
                cross_max = max(((sizes[i][0] if vertical else sizes[i][1]) for i in ln), default=0)
                blocks.append((ln, main_total, cross_max))
            for ln, main_total, cross_max in blocks:
                avail_main = ch if vertical else cw
                if flex in ('SpaceBetween', 'SpaceAround', 'SpaceEvenly') and len(ln) > 0:
                    free = avail_main - sum((sizes[i][1] if vertical else sizes[i][0]) for i in ln)
                    if flex == 'SpaceBetween': gap = free / (len(ln) - 1) if len(ln) > 1 else 0; start = 0
                    elif flex == 'SpaceAround': gap = free / len(ln); start = gap / 2
                    else: gap = free / (len(ln) + 1); start = gap
                else:
                    gap = pad
                    al = va if vertical else ha
                    start = {'Top': 0, 'Left': 0, 'Center': (avail_main - main_total) / 2, 'Bottom': avail_main - main_total, 'Right': avail_main - main_total}.get(al, 0)
                pos = start
                for i in ln:
                    w, h = sizes[i]; main = h if vertical else w; cross = w if vertical else h
                    avail_cross = cw if vertical else ch
                    cal = ha if vertical else va
                    cs = {'Left': 0, 'Top': 0, 'Center': (avail_cross - cross) / 2, 'Right': avail_cross - cross, 'Bottom': avail_cross - cross}.get(cal, 0)
                    if wraps: cs = cross_cur + cs if False else cross_cur
                    x, y = (cs, pos) if vertical else (pos, cs)
                    out.append((kids[i], ox + x, oy + y, w, h)); pos += main + gap
                cross_cur += cross_max + pad
            return out
        if grid:
            kids = self.sorted_children(n, grid)
            cell = grid.props.get('CellSize'); cp = grid.props.get('CellPadding')
            cell = cell if isinstance(cell, tuple) and cell and cell[0] == 'UDim2' else ('UDim2', 0, 100, 0, 100)
            cp = cp if isinstance(cp, tuple) and cp and cp[0] == 'UDim2' else ('UDim2', 0, 5, 0, 5)
            cwid = cell[1] * cw + cell[2]; chei = cell[3] * ch + cell[4]
            px = cp[1] * cw + cp[2]; py = cp[3] * ch + cp[4]
            horiz = (enum_name(grid.props.get('FillDirection')) or 'Horizontal') == 'Horizontal'
            maxc = grid.props.get('FillDirectionMaxCells'); maxc = int(maxc) if isinstance(maxc, (int, float)) and maxc > 0 else 0
            per = max(1, int((cw + px) // (cwid + px))) if horiz else max(1, int((ch + py) // (chei + py)))
            if maxc: per = min(per, maxc)
            ha = enum_name(grid.props.get('HorizontalAlignment')) or 'Left'
            used = min(per, len(kids)) if horiz else None
            row_w = (used * cwid + (used - 1) * px) if used else 0
            start_x = {'Left': 0, 'Center': (cw - row_w) / 2, 'Right': cw - row_w}.get(ha, 0) if horiz and used else 0
            for i, c in enumerate(kids):
                if horiz: r, col = divmod(i, per)
                else: col, r = divmod(i, per)
                out.append((c, ox + start_x + col * (cwid + px), oy + r * (chei + py), cwid, chei))
            return out
        for c in self.children_gui(n):
            w, h = self.measure(c, cw, ch)
            pos = self.udim2(c, 'Position', ('UDim2', 0, 0, 0, 0)); an = c.props.get('AnchorPoint')
            an = an if isinstance(an, tuple) and an and an[0] == 'V2' else ('V2', 0, 0)
            out.append((c, ox + pos[1] * cw + pos[2] - an[1] * w, oy + pos[3] * ch + pos[4] - an[2] * h, w, h))
        return out
    # ---- place ----
    def place(self, n, x, y, w, h, root, k, in_sy=False, in_sx=False, clip=None):
        it = Item(n, root); it.x, it.y, it.w, it.h, it.scale = x, y, w, h, k
        it.in_scroll_y, it.in_scroll_x, it.clip = in_sy, in_sx, clip
        self.items[n.id] = it
        s = self.uiscale(n); w0, h0 = w / s, h / s
        pl, pt, pr, pb = self.padding(n, w0, h0)
        cw, ch = max(w0 - pl - pr, 0), max(h0 - pt - pb, 0)
        if n.cls in TEXT_CLASSES:
            it.text = self.text_metrics(n, max(cw, 1), max(ch, 1), scale=k * s if False else 1.0)
            if it.text and (k * s) != 1.0:
                for kk in ('size', 'w', 'h', 'natural_w'): it.text[kk] *= (k * s)
        sy, sx = in_sy, in_sx
        ccw, cch = cw, ch
        if n.cls == 'ScrollingFrame':
            thick = self.num(n, 'ScrollBarThickness', 12); direction = enum_name(n.props.get('ScrollingDirection')) or 'XY'
            if direction in ('Y', 'XY'): ccw = max(cw - thick, 0)
            cs = self.udim2(n, 'CanvasSize', ('UDim2', 0, 0, 2, 0))
            auto = enum_name(n.props.get('AutomaticCanvasSize')) or 'None'
            canvas_w = cs[1] * w0 + cs[2]; canvas_h = cs[3] * h0 + cs[4]
            if auto in ('Y', 'XY'):
                ext = self.extent(n, ccw, 1e9 if False else canvas_h); canvas_h = ext[1] + pt + pb
            if auto in ('X', 'XY'):
                ext = self.extent(n, canvas_w, cch); canvas_w = ext[0] + pl + pr
            cch = max(canvas_h - pt - pb, 0)
            if direction == 'Y': ccw = max(cw - thick, 0)
            elif canvas_w > 0 and direction in ('X', 'XY') and cs[1] or cs[2]: ccw = max(canvas_w - pl - pr, 0) if direction == 'X' else ccw
            sy = sx = True
            if direction == 'Y': sx = in_sx
            if direction == 'X': sy = in_sy
        clipf = it if (self.P(n, 'ClipsDescendants', False) is True or n.cls in ('ScrollingFrame', 'CanvasGroup')) else clip
        rects = self.arrange(n, x + pl * s, y + pt * s, ccw, cch) if s == 1 else self.arrange(n, 0, 0, ccw, cch)
        for c, cx, cy, cwid, chei in rects:
            if s != 1:
                cx = x + pl * s + cx * s; cy = y + pt * s + cy * s; cwid *= s; chei *= s
            self.place(c, cx, cy, cwid, chei, root, k * s, sy, sx, clipf)
    def region_for(self, r):
        """Area a ScreenGui lays out in, from IgnoreGuiInset / ScreenInsets.
        None / DeviceSafeInsets / IgnoreGuiInset=true -> full screen. CoreUISafeInsets (default) -> below the top bar.
        TopbarSafeInsets -> ONLY the top-bar strip right of the logo/menu/chat buttons (observed on device: content collapses)."""
        ignore = self.P(r, 'IgnoreGuiInset', False) is True
        si = enum_name(r.props.get('ScreenInsets')) if r.cls == 'ScreenGui' else None
        if ignore or si in ('None', 'DeviceSafeInsets'): return (0, 0, self.vw, self.vh), 'full'
        if si == 'TopbarSafeInsets': return (TOPBAR_LEFT_W, 0, max(self.vw - TOPBAR_LEFT_W, 0), TOPBAR_H + 2), 'topbar_strip'
        return (0, TOPBAR_H, self.vw, max(self.vh - TOPBAR_H, 0)), 'core'
    def run(self, root_nodes):
        for r in root_nodes:
            region, kind = self.region_for(r)
            self.roots.append((r, region, kind))
            rx, ry, rw, rh = region
            if r.cls == 'ScreenGui':
                kids = self.arrange(r, rx, ry, rw, rh)
                for c, x, y, w, h in kids: self.place(c, x, y, w, h, r, 1.0)
            else:
                w, h = self.measure(r, rw, rh)
                pos = self.udim2(r, 'Position', ('UDim2', 0, 0, 0, 0))
                self.place(r, rx + pos[1] * rw + pos[2], ry + pos[3] * rh + pos[4], w, h, r, 1.0)

def find_roots(nodes):
    nodes = [n for n in nodes if not n.destroyed]
    roots = [n for n in nodes if n.cls == 'ScreenGui']
    # GUI objects that were parented to an unknown instance (PlayerGui/StarterGui) act as their own root
    for n in nodes:
        if n.cls in GUI_CLASSES and n.cls not in ('ScreenGui', 'SurfaceGui', 'BillboardGui') and n.parent is None and n not in roots:
            roots.append(n)
    return roots

def compute(nodes, vp_name):
    vw, vh = VIEWPORTS[vp_name]
    L = Layouter(vp_name, vw, vh)
    L.run(find_roots(nodes))
    return L
