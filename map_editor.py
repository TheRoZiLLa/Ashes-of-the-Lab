"""
map_editor.py  v3  –  AOFT - Map Editor
═══════════════════════════════════════════════════════════════════════
Run from the project root:
    python map_editor.py

New in v3
─────────
  • Branded title   – "AOFT - Map Editor" header panel + window caption
  • Resizable window – drag any edge; F10 maximise; F11 fullscreen
  • Layer reorder   – ^ Move Up / v Move Down buttons in Layers tab
  • Layer rename    – Double-click a layer name to rename inline
  • Layer colour    – Click the colour dot to cycle through a palette
  • Help overlay    – Press F1 for full shortcut reference
  • Status bar      – Shows live window resolution

Controls
────────
  Left Click             Place / select / move / resize
  Right Click            Delete object under cursor
  Middle Mouse Drag      Pan camera
  WASD / Arrow keys      Move camera
  Mouse Wheel (viewport) Zoom in / out  (0.12x – 5x)
  Mouse Wheel (panel)    Scroll asset list
  Ctrl+S                 Save  (native dialog when tkinter available)
  Ctrl+L                 Load
  Ctrl+E                 Export game-ready map
  Ctrl+Z / Ctrl+Y        Undo / Redo  (100 levels)
  Ctrl+D                 Duplicate selected object
  G                      Toggle grid display
  S  (no Ctrl)           Toggle snap-to-grid
  Delete / Backspace     Delete selected object
  Escape                 Deselect / cancel placement / cancel rename
  F1                     Toggle help overlay
  F10                    Maximise / restore default window size (1280×720)
  F11                    Toggle fullscreen
  Q                      Quit

  Layer tab
  ─────────
  Double-click name      Rename layer  (Enter = confirm, Esc = cancel)
  Click colour dot       Cycle layer colour through palette

Export JSON format (game-compatible)
─────────────────────────────────────
{
  "world":        {"width":…,"height":…},
  "layers":       [{"name":…,"visible":…,"locked":…}, …],
  "platforms":    [{"x":…,"y":…,"w":…,"h":…,"layer":…}, …],
  "ground":       […],
  "enemy_spawns": [{"x":…,"y":…,"layer":…}, …],
  "player_spawn": {"x":…,"y":…},
  "pickups":      […],
  "decorations":  […],
  "sprites":      [{"x":…,"y":…,"w":…,"h":…,"asset":"file.png","layer":…}, …]
}
"""

from __future__ import annotations

import sys
import os
import math
import json
import copy
from enum import Enum
from typing import Optional, List, Tuple, Dict

import pygame

try:
    import tkinter as tk
    from tkinter import filedialog
    _HAS_TK = True
except ImportError:
    _HAS_TK = False


# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

SCREEN_W, SCREEN_H = 1280, 720
PANEL_W   = 260
STATUS_H  = 30
HEADER_H  = 36           # AOFT brand strip at top of panel
TAB_H     = 28

VP_X = PANEL_W
VP_Y = 0
VP_W = SCREEN_W - PANEL_W
VP_H = SCREEN_H - STATUS_H

GRID_SIZE       = 32
DEFAULT_WORLD_W = 6400
DEFAULT_WORLD_H = 1440

DEFAULT_SAVE = "map_editor_save.json"
EXPORT_FILE  = "export_map.json"

POINT_R  = 14
HANDLE_R = 5
MIN_RECT = GRID_SIZE

# Colour palette for layer cycling (click colour dot to cycle)
LAYER_PALETTE = [
    (100, 100, 200), ( 80, 180,  80), (160, 100, 200),
    (200, 100, 100), (180, 180,  80), (100, 180, 180),
    (220, 130,  50), (160,  60, 120), ( 60, 160, 160),
    ( 80,  80,  80),
]

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG         = ( 14,  11,  20)
C_WORLD_BG   = ( 19,  15,  26)
C_PANEL      = ( 23,  19,  33)
C_PANEL_EDGE = ( 50,  42,  68)
C_STATUS_BG  = ( 16,  13,  23)
C_TEXT       = (210, 200, 235)
C_TEXT_DIM   = ( 95,  88, 115)
C_TEXT_ACT   = (255, 225,  90)
C_GRID       = ( 29,  25,  40)
C_GRID_MAJ   = ( 44,  38,  58)
C_GRID_AXIS  = ( 55,  47,  75)
C_WORLD_EDGE = ( 75,  55, 115)
C_HOVER      = (255, 255, 255,  18)
C_SEL        = (255, 215,  55)
C_HANDLE     = (255, 195,  60)
C_HANDLE_HOV = (255, 255, 140)
C_BTN        = ( 38,  32,  52)
C_BTN_HOV    = ( 58,  50,  78)
C_BTN_ACT    = ( 82,  68, 128)
C_BTN_TXT    = (215, 205, 240)
C_TAB        = ( 28,  23,  40)
C_TAB_ACT    = ( 42,  36,  60)
C_TAB_EDGE   = ( 60,  50,  82)
C_LAYER_ROW  = ( 30,  25,  44)
C_LAYER_ACT  = ( 48,  40,  72)
C_LAYER_HOV  = ( 40,  34,  58)
# AOFT header
C_HEADER_BG  = ( 18,  14,  28)
C_HEADER_ACT = (140, 100, 220)
C_HEADER_DIM = ( 70,  55, 100)
# Help overlay
C_HELP_BG    = (  8,   6,  14, 220)
C_HELP_HDR   = (140, 100, 220)
# Rename / input field
C_RENAME_BG  = ( 10,  50,  30)
C_RENAME_BOR = ( 60, 200, 110)

OBJ_COLORS: Dict[str, tuple] = {
    "platform":     ( 76,  68,  98),
    "ground":       ( 55,  50,  74),
    "enemy_spawn":  (205,  50,  50),
    "player_spawn": ( 65, 158, 252),
    "pickup":       (248, 206,  48),
    "decoration":   ( 84, 150,  84),
    "sprite":       (160, 110, 200),
}
OBJ_LABELS: Dict[str, str] = {
    "platform":     "Platform",
    "ground":       "Ground",
    "enemy_spawn":  "Enemy Spawn",
    "player_spawn": "Player Spawn",
    "pickup":       "Pickup",
    "decoration":   "Decoration",
    "sprite":       "Sprite",
}
OBJ_ICONS: Dict[str, str] = {
    "platform": "=", "ground": "=", "enemy_spawn": "X",
    "player_spawn": "*", "pickup": "+", "decoration": "#", "sprite": "@",
}
POINT_TYPES = {"enemy_spawn", "player_spawn", "pickup"}
RECT_TYPES  = {"platform", "ground", "decoration", "sprite"}

DEFAULT_LAYER_DEFS = [
    {"name": "Background", "color": ( 80,  80, 180), "visible": True, "locked": False},
    {"name": "Ground",     "color": ( 80, 160,  80), "visible": True, "locked": False},
    {"name": "Platforms",  "color": (130, 110, 180), "visible": True, "locked": False},
    {"name": "Entities",   "color": (200,  90,  90), "visible": True, "locked": False},
    {"name": "Foreground", "color": (180, 180,  90), "visible": True, "locked": False},
]
TOOL_DEFAULT_LAYER: Dict[str, int] = {
    "platform": 2, "ground": 1, "enemy_spawn": 3,
    "player_spawn": 3, "pickup": 3, "decoration": 0, "sprite": 4,
}

# Resize handle names and the edges they control
HANDLES     = ('tl','tm','tr','ml','mr','bl','bm','br')
HANDLE_EDGES: Dict[str, tuple] = {
    'tl':('l','t'), 'tm':('t',), 'tr':('r','t'),
    'ml':('l',),                  'mr':('r',),
    'bl':('l','b'), 'bm':('b',), 'br':('r','b'),
}


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL ENUM
# ═══════════════════════════════════════════════════════════════════════════════

class Tool(Enum):
    SELECT       = "select"
    PLATFORM     = "platform"
    GROUND       = "ground"
    ENEMY_SPAWN  = "enemy_spawn"
    PLAYER_SPAWN = "player_spawn"
    PICKUP       = "pickup"
    DECORATION   = "decoration"
    SPRITE       = "sprite"

TOOL_ORDER = [
    Tool.SELECT, Tool.PLATFORM, Tool.GROUND, Tool.ENEMY_SPAWN,
    Tool.PLAYER_SPAWN, Tool.PICKUP, Tool.DECORATION, Tool.SPRITE,
]
TOOL_LABELS: Dict[Tool, str] = {
    Tool.SELECT:       "  Select",
    Tool.PLATFORM:     "= Platform",
    Tool.GROUND:       "= Ground",
    Tool.ENEMY_SPAWN:  "X Enemy Spawn",
    Tool.PLAYER_SPAWN: "* Player Spawn",
    Tool.PICKUP:       "+ Pickup",
    Tool.DECORATION:   "# Decoration",
    Tool.SPRITE:       "@ Sprite (asset)",
}
TOOL_ACT: Dict[Tool, tuple] = {
    Tool.SELECT:       ( 50,120, 50), Tool.PLATFORM:     ( 70, 62,130),
    Tool.GROUND:       ( 50, 45, 88), Tool.ENEMY_SPAWN:  (150, 38, 38),
    Tool.PLAYER_SPAWN: ( 32, 80,168), Tool.PICKUP:       (148,122, 24),
    Tool.DECORATION:   ( 50,100, 50), Tool.SPRITE:       (110, 68,155),
}


# ═══════════════════════════════════════════════════════════════════════════════
#  DATA MODEL
# ═══════════════════════════════════════════════════════════════════════════════

class MapObject:
    __slots__ = ("obj_type","x","y","w","h","layer_idx","asset_key")

    def __init__(self, obj_type: str, x: float, y: float,
                 w: float = 64.0, h: float = 32.0,
                 layer_idx: int = 0, asset_key: Optional[str] = None):
        self.obj_type  = obj_type
        self.x = float(x); self.y = float(y)
        self.w = float(w); self.h = float(h)
        self.layer_idx = layer_idx
        self.asset_key = asset_key

    @property
    def color(self) -> tuple:
        return OBJ_COLORS.get(self.obj_type, (110,110,110))
    @property
    def is_point(self) -> bool:
        return self.obj_type in POINT_TYPES
    @property
    def cx(self) -> float: return self.x + self.w/2
    @property
    def cy(self) -> float: return self.y + self.h/2

    def world_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x),int(self.y),max(1,int(self.w)),max(1,int(self.h)))

    def contains(self, wx: float, wy: float) -> bool:
        if self.is_point:
            return math.hypot(wx-self.cx, wy-self.cy) <= POINT_R+4
        return self.world_rect().collidepoint(wx, wy)

    def to_dict(self) -> dict:
        d: dict = {"x":int(self.x),"y":int(self.y),"layer":self.layer_idx}
        if not self.is_point:
            d["w"] = int(self.w); d["h"] = int(self.h)
        if self.asset_key:
            d["asset"] = self.asset_key
        return d

    @classmethod
    def from_dict(cls, obj_type: str, d: dict) -> "MapObject":
        return cls(obj_type, float(d.get("x",0)), float(d.get("y",0)),
                   float(d.get("w", POINT_R*2)), float(d.get("h", POINT_R*2)),
                   int(d.get("layer",0)), d.get("asset"))

    def clone(self) -> "MapObject":
        return MapObject(self.obj_type,self.x,self.y,self.w,self.h,
                         self.layer_idx,self.asset_key)


# ═══════════════════════════════════════════════════════════════════════════════
#  LAYER
# ═══════════════════════════════════════════════════════════════════════════════

class Layer:
    MAX_LAYERS = 10
    def __init__(self, name: str, color: tuple=(120,120,180),
                 visible: bool=True, locked: bool=False):
        self.name=name; self.color=color
        self.visible=visible; self.locked=locked
    def to_dict(self) -> dict:
        return {"name":self.name,"color":list(self.color),
                "visible":self.visible,"locked":self.locked}
    @classmethod
    def from_dict(cls, d: dict) -> "Layer":
        return cls(d.get("name","Layer"), tuple(d.get("color",[120,120,180])),
                   d.get("visible",True), d.get("locked",False))

def _default_layers() -> List[Layer]:
    return [Layer(**{k:v for k,v in ld.items()}) for ld in DEFAULT_LAYER_DEFS]


# ═══════════════════════════════════════════════════════════════════════════════
#  ASSET MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

THUMB_W, THUMB_H = 44, 44

class AssetManager:
    SUPPORTED = {".png",".jpg",".jpeg",".bmp",".gif",".tga",".webp"}

    def __init__(self):
        self.surfaces: Dict[str, pygame.Surface] = {}
        self.thumbs:   Dict[str, pygame.Surface] = {}
        self.paths:    Dict[str, str] = {}
        self.active_key: Optional[str] = None

    def load(self, path: str) -> Optional[str]:
        key = os.path.basename(path)
        try:
            img = pygame.image.load(path).convert_alpha()
            self.surfaces[key] = img
            self.paths[key]    = path
            iw,ih = img.get_size()
            scale = min(THUMB_W/iw, THUMB_H/ih, 1.0)
            nw,nh = max(1,int(iw*scale)), max(1,int(ih*scale))
            self.thumbs[key] = pygame.transform.smoothscale(img,(nw,nh))
            return key
        except Exception as e:
            print(f"[Assets] {path}: {e}"); return None

    def remove(self, key: str) -> None:
        for d in (self.surfaces,self.thumbs,self.paths): d.pop(key,None)
        if self.active_key == key: self.active_key = None

    def get(self, key: Optional[str]) -> Optional[pygame.Surface]:
        return self.surfaces.get(key) if key else None
    def get_thumb(self, key: str) -> Optional[pygame.Surface]:
        return self.thumbs.get(key)
    def all_keys(self) -> List[str]:
        return list(self.surfaces.keys())


# ═══════════════════════════════════════════════════════════════════════════════
#  CAMERA
# ═══════════════════════════════════════════════════════════════════════════════

class Camera:
    MIN_ZOOM=0.12; MAX_ZOOM=5.0
    def __init__(self):
        self.x=0.0; self.y=0.0; self.zoom=1.0
    def w2s(self,wx,wy):
        return (wx-self.x)*self.zoom+VP_X, (wy-self.y)*self.zoom+VP_Y
    def s2w(self,sx,sy):
        return (sx-VP_X)/self.zoom+self.x, (sy-VP_Y)/self.zoom+self.y
    def zoom_at(self,sx,sy,f):
        wx,wy=self.s2w(sx,sy)
        self.zoom=max(self.MIN_ZOOM,min(self.MAX_ZOOM,self.zoom*f))
        nx,ny=self.w2s(wx,wy)
        self.x+=(nx-sx)/self.zoom; self.y+=(ny-sy)/self.zoom
    def pan(self,dx,dy):
        self.x+=dx/self.zoom; self.y+=dy/self.zoom
    def clamp(self,ww,wh,vp_w=VP_W,vp_h=VP_H):
        m=400
        self.x=max(-m,min(ww+m-vp_w/self.zoom,self.x))
        self.y=max(-m,min(wh+m-vp_h/self.zoom,self.y))


# ═══════════════════════════════════════════════════════════════════════════════
#  BUTTON
# ═══════════════════════════════════════════════════════════════════════════════

class Button:
    def __init__(self,rect,label,base=C_BTN,active=C_BTN_ACT):
        self.rect=pygame.Rect(rect); self.label=label
        self._base=base; self._active=active
        self.is_active=False; self.hovered=False
    def update(self,mx,my): self.hovered=self.rect.collidepoint(mx,my)
    def hit(self,mx,my): return self.rect.collidepoint(mx,my)
    def draw(self,surf,font,tc=C_BTN_TXT):
        col=self._active if self.is_active else(C_BTN_HOV if self.hovered else self._base)
        pygame.draw.rect(surf,col,self.rect,border_radius=4)
        e=tuple(min(255,c+28) for c in col)
        pygame.draw.rect(surf,e,self.rect,1,border_radius=4)
        t=font.render(self.label,True,tc)
        surf.blit(t,(self.rect.x+8,self.rect.centery-t.get_height()//2))


def _ask_save(initial):
    if _HAS_TK:
        r=tk.Tk(); r.withdraw(); r.update()
        p=filedialog.asksaveasfilename(defaultextension=".json",
            filetypes=[("JSON","*.json"),("All","*.*")],
            initialfile=os.path.basename(initial),title="Save Map")
        r.destroy(); return p or None
    return initial

def _ask_open(filetypes=(("JSON","*.json"),("All","*.*")),title="Open"):
    if _HAS_TK:
        r=tk.Tk(); r.withdraw(); r.update()
        p=filedialog.askopenfilename(filetypes=filetypes,title=title)
        r.destroy(); return p or None
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  MAP EDITOR
# ═══════════════════════════════════════════════════════════════════════════════

class MapEditor:
    CAM_SPEED = 440.0

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("AOFT - Map Editor")
        self._screen=pygame.display.set_mode((SCREEN_W,SCREEN_H),pygame.RESIZABLE)
        self._clock=pygame.time.Clock()

        mono="Consolas,Courier New,monospace"
        self._f11=pygame.font.SysFont(mono,11)
        self._f13=pygame.font.SysFont(mono,13)
        self._f14=pygame.font.SysFont(mono,14)
        self._f15=pygame.font.SysFont(mono,15,bold=True)

        # Current window size (updated on resize events)
        self._sw=SCREEN_W
        self._sh=SCREEN_H

        # World state
        self._world_w=DEFAULT_WORLD_W
        self._world_h=DEFAULT_WORLD_H
        self._objects:  List[MapObject]=[]
        self._layers:   List[Layer]=_default_layers()
        self._active_layer=2

        # Undo/redo: snapshots = (objects, layers, world_w, world_h)
        self._undo: List[tuple]=[]
        self._redo: List[tuple]=[]

        self._assets=AssetManager()

        self._cam=Camera()
        self._cam.y=max(0.0,self._world_h-VP_H)

        self._tool=Tool.PLATFORM
        self._show_grid=True
        self._snap=True
        self._selected: Optional[MapObject]=None

        # Placement
        self._rect_placing=False
        self._rect_start=(0.0,0.0)
        self._rect_preview: Optional[MapObject]=None
        self._point_dragging=False
        self._point_last_cell=None

        # Resize
        self._resizing=False
        self._resize_handle=""
        self._resize_orig=(0.0,0.0,0.0,0.0)
        self._resize_pre: Optional[list]=None

        # Move
        self._moving=False
        self._move_offset=(0.0,0.0)
        self._move_pre: Optional[list]=None

        # Pan
        self._panning=False
        self._pan_origin=(0,0)
        self._pan_cam0=(0.0,0.0)

        # Panel
        self._active_tab="tools"
        self._asset_scroll=0
        self._hovered_handle=""

        # Layer rename state
        self._rename_idx   = -1    # layer index being renamed (-1 = none)
        self._rename_buf   = ""    # characters typed so far
        # Double-click detection
        self._dbl_last_time  = 0.0
        self._dbl_last_layer = -1
        # Help overlay
        self._show_help = False

        self._save_path=DEFAULT_SAVE
        self._status="Welcome!  Pick a tool and start building."
        self._status_ttl=5.0

        self._build_ui()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        pw=PANEL_W; bw=pw-16; bh=28; px=8
        sh=self._sh  # current window height

        # Tabs — start below the AOFT header strip
        tab_y=HEADER_H
        tab_w=pw//4
        self._tabs={k:pygame.Rect(i*tab_w,tab_y,tab_w,TAB_H)
                    for i,k in enumerate(("tools","layers","assets","map"))}

        # Tool buttons (tools tab)
        py=HEADER_H+TAB_H+8
        self._tool_btns:Dict[Tool,Button]={}
        for t in TOOL_ORDER:
            self._tool_btns[t]=Button((px,py,bw,bh),TOOL_LABELS[t],
                                      C_BTN,TOOL_ACT.get(t,C_BTN_ACT))
            py+=bh+4
        py+=8
        self._sep_y=py; py+=6
        self._btn_save  =Button((px,py,bw,bh),"  Save   Ctrl+S");  py+=bh+4
        self._btn_load  =Button((px,py,bw,bh),"  Load   Ctrl+L");  py+=bh+4
        self._btn_export=Button((px,py,bw,bh),"  Export  Ctrl+E"); py+=bh+4
        self._btn_clear =Button((px,py,bw,bh),"  Clear All",(62,25,25),(130,40,40))
        self._action_btns=[self._btn_save,self._btn_load,
                           self._btn_export,self._btn_clear]

        # Layer tab – bottom buttons (anchored to window bottom)
        by =sh-STATUS_H-bh-8
        by2=by-bh-5
        hw=(bw-4)//2
        self._btn_add_layer   =Button((px,      by, hw,   bh),"+ Add Layer")
        self._btn_del_layer   =Button((px+hw+4, by, hw,   bh),"- Remove",(62,25,25),(130,40,40))
        self._btn_layer_up    =Button((px,      by2,hw,   bh),"^ Move Up")
        self._btn_layer_down  =Button((px+hw+4, by2,hw,   bh),"v Move Down")

        # Asset tab buttons
        aty=HEADER_H+TAB_H+8
        self._btn_load_asset  =Button((px,aty,bw,bh),"  Load Image...")
        self._btn_remove_asset=Button((px,aty+bh+4,bw,bh),
                                      "  Remove Selected",(62,25,25),(130,40,40))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _sv(self,v): return round(v/GRID_SIZE)*GRID_SIZE if self._snap else v
    def _sp(self,wx,wy): return self._sv(wx),self._sv(wy)

    def _snap_shot(self):
        return (copy.deepcopy(self._objects),copy.deepcopy(self._layers),
                self._world_w,self._world_h)

    def _push_undo(self):
        self._undo.append(self._snap_shot())
        if len(self._undo)>100: self._undo.pop(0)
        self._redo.clear()

    def _do_undo(self):
        if not self._undo: self._set_status("Nothing to undo."); return
        self._redo.append(self._snap_shot())
        o,l,w,h=self._undo.pop()
        self._objects,self._layers=o,l; self._world_w,self._world_h=w,h
        self._selected=None; self._set_status("Undo")

    def _do_redo(self):
        if not self._redo: self._set_status("Nothing to redo."); return
        self._undo.append(self._snap_shot())
        o,l,w,h=self._redo.pop()
        self._objects,self._layers=o,l; self._world_w,self._world_h=w,h
        self._selected=None; self._set_status("Redo")

    def _set_status(self,msg,ttl=3.0):
        self._status=msg; self._status_ttl=ttl

    # ── Dynamic viewport dimensions ───────────────────────────────────────────
    @property
    def _vp_w(self): return max(200, self._sw - PANEL_W)
    @property
    def _vp_h(self): return max(100, self._sh - STATUS_H)

    def _lyr_visible(self,i): return self._layers[i].visible if 0<=i<len(self._layers) else True
    def _lyr_locked (self,i): return self._layers[i].locked  if 0<=i<len(self._layers) else False
    def _active_li(self): return min(self._active_layer,len(self._layers)-1)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def _to_dict(self)->dict:
        d:dict={
            "world":{"width":self._world_w,"height":self._world_h},
            "layers":[l.to_dict() for l in self._layers],
            "platforms":[],"ground":[],"enemy_spawns":[],
            "player_spawn":None,"pickups":[],"decorations":[],"sprites":[],
        }
        for obj in self._objects:
            od=obj.to_dict(); t=obj.obj_type
            if   t=="platform":     d["platforms"].append(od)
            elif t=="ground":       d["ground"].append(od)
            elif t=="enemy_spawn":  d["enemy_spawns"].append(od)
            elif t=="player_spawn": d["player_spawn"]=od
            elif t=="pickup":       d["pickups"].append(od)
            elif t=="decoration":   d["decorations"].append(od)
            elif t=="sprite":       d["sprites"].append(od)
        return d

    def _from_dict(self,data:dict):
        self._objects.clear(); self._selected=None
        w=data.get("world",{})
        self._world_w=int(w.get("width",DEFAULT_WORLD_W))
        self._world_h=int(w.get("height",DEFAULT_WORLD_H))
        if "layers" in data:
            self._layers=[Layer.from_dict(ld) for ld in data["layers"]] or _default_layers()
            self._active_layer=min(self._active_layer,len(self._layers)-1)
        for d in data.get("platforms",   []): self._objects.append(MapObject.from_dict("platform",    d))
        for d in data.get("ground",      []): self._objects.append(MapObject.from_dict("ground",      d))
        for d in data.get("enemy_spawns",[]): self._objects.append(MapObject.from_dict("enemy_spawn", d))
        ps=data.get("player_spawn")
        if ps: self._objects.append(MapObject.from_dict("player_spawn",ps))
        for d in data.get("pickups",     []): self._objects.append(MapObject.from_dict("pickup",      d))
        for d in data.get("decorations", []): self._objects.append(MapObject.from_dict("decoration",  d))
        for d in data.get("sprites",     []): self._objects.append(MapObject.from_dict("sprite",      d))

    # ── File ops ──────────────────────────────────────────────────────────────

    def _save(self):
        p=_ask_save(self._save_path)
        if not p: return
        try:
            with open(p,"w") as f: json.dump(self._to_dict(),f,indent=2)
            self._save_path=p; self._set_status(f"Saved -> {os.path.basename(p)}")
        except Exception as e: self._set_status(f"Save error: {e}")

    def _load(self):
        p=_ask_open(title="Load Map")
        if not p: return
        try:
            with open(p) as f: data=json.load(f)
            self._push_undo(); self._from_dict(data)
            self._save_path=p
            self._set_status(f"Loaded <- {os.path.basename(p)}  ({len(self._objects)} objs)")
        except Exception as e: self._set_status(f"Load error: {e}")

    def _export(self):
        p=_ask_save(EXPORT_FILE)
        if not p: return
        try:
            with open(p,"w") as f: json.dump(self._to_dict(),f,indent=2)
            self._set_status(f"Exported -> {os.path.basename(p)}")
        except Exception as e: self._set_status(f"Export error: {e}")

    def _load_asset(self):
        exts=" ".join(f"*{e}" for e in AssetManager.SUPPORTED)
        p=_ask_open(filetypes=[("Images",exts),("PNG","*.png"),("All","*.*")],title="Load Asset")
        if not p: return
        k=self._assets.load(p)
        if k:
            self._assets.active_key=k; self._tool=Tool.SPRITE
            self._set_status(f"Asset loaded: {k}")
        else: self._set_status("Failed to load asset.")

    # ── Object helpers ────────────────────────────────────────────────────────

    def _find_at(self,wx,wy)->Optional[MapObject]:
        for obj in reversed(self._objects):
            if not self._lyr_visible(obj.layer_idx): continue
            if self._lyr_locked(obj.layer_idx):      continue
            if obj.contains(wx,wy): return obj
        return None

    def _place_point(self,obj_type,wx,wy):
        snx,sny=self._sp(wx,wy); cell=(snx,sny)
        if cell==self._point_last_cell: return
        self._point_last_cell=cell
        if obj_type=="player_spawn":
            self._objects=[o for o in self._objects if o.obj_type!="player_spawn"]
        self._push_undo()
        r=float(POINT_R)
        li=TOOL_DEFAULT_LAYER.get(obj_type,self._active_li())
        self._objects.append(MapObject(obj_type,snx-r,sny-r,r*2,r*2,li))

    def _delete_obj(self,obj):
        if obj in self._objects:
            self._push_undo(); self._objects.remove(obj)
            if self._selected is obj: self._selected=None

    def _delete_selected(self):
        if self._selected: self._delete_obj(self._selected); self._set_status("Deleted.")

    def _duplicate_selected(self):
        if not self._selected or self._selected not in self._objects: return
        self._push_undo()
        c=self._selected.clone(); c.x+=GRID_SIZE*2; c.y+=GRID_SIZE*2
        self._objects.append(c); self._selected=c; self._set_status("Duplicated.")

    # ── Resize handle helpers ─────────────────────────────────────────────────

    def _handle_pts(self,obj)->Dict[str,Tuple[int,int]]:
        sx,sy=self._cam.w2s(obj.x,obj.y)
        sw=max(4,int(obj.w*self._cam.zoom)); sh=max(4,int(obj.h*self._cam.zoom))
        cx=int(sx+sw//2); cy=int(sy+sh//2); r=int(sx+sw); b=int(sy+sh)
        return {'tl':(int(sx),int(sy)),'tm':(cx,int(sy)),'tr':(r,int(sy)),
                'ml':(int(sx),cy),                        'mr':(r,cy),
                'bl':(int(sx),b), 'bm':(cx,b),           'br':(r,b)}

    def _hit_handle(self,obj,mx,my)->str:
        if obj.is_point or self._cam.zoom<0.22: return ""
        best,bd="",float("inf")
        for n,(hx,hy) in self._handle_pts(obj).items():
            d=math.hypot(mx-hx,my-hy)
            if d<=HANDLE_R+4 and d<bd: best,bd=n,d
        return best

    def _apply_resize(self,handle,wx,wy):
        if not self._selected: return
        snx,sny=self._sp(wx,wy)
        ox,oy,ow,oh=self._resize_orig
        x,y,w,h=ox,oy,ow,oh
        edges=HANDLE_EDGES[handle]
        if 'l' in edges:
            nx=min(snx,ox+ow-MIN_RECT); w=ow+ox-nx; x=nx
        if 'r' in edges:
            w=max(MIN_RECT,max(snx,ox+MIN_RECT)-ox)
        if 't' in edges:
            ny=min(sny,oy+oh-MIN_RECT); h=oh+oy-ny; y=ny
        if 'b' in edges:
            h=max(MIN_RECT,max(sny,oy+MIN_RECT)-oy)
        self._selected.x=x; self._selected.y=y
        self._selected.w=max(MIN_RECT,w); self._selected.h=max(MIN_RECT,h)

    # ── Layer management ──────────────────────────────────────────────────────

    def _add_layer(self):
        if len(self._layers)>=Layer.MAX_LAYERS:
            self._set_status(f"Max {Layer.MAX_LAYERS} layers."); return
        self._push_undo()
        idx=len(self._layers)
        palette=[(100,100,200),(80,180,80),(160,100,200),
                 (200,100,100),(180,180,80),(100,180,180)]
        self._layers.append(Layer(f"Layer {idx}",palette[idx%len(palette)]))
        self._active_layer=idx; self._set_status(f"Added Layer {idx}")

    def _remove_layer(self):
        if len(self._layers)<=1:
            self._set_status("Cannot remove last layer."); return
        self._push_undo(); idx=self._active_li()
        for obj in self._objects:
            if obj.layer_idx==idx: obj.layer_idx=0
            elif obj.layer_idx>idx: obj.layer_idx-=1
        self._layers.pop(idx)
        self._active_layer=max(0,idx-1); self._set_status("Layer removed.")

    def _move_layer(self,direction:int):
        """Move the active layer up (-1) or down (+1) in the stack."""
        idx=self._active_li(); new_idx=idx+direction
        if new_idx<0 or new_idx>=len(self._layers):
            self._set_status("Already at the edge."); return
        self._push_undo()
        self._layers[idx],self._layers[new_idx]=self._layers[new_idx],self._layers[idx]
        for obj in self._objects:
            if   obj.layer_idx==idx:     obj.layer_idx=new_idx
            elif obj.layer_idx==new_idx: obj.layer_idx=idx
        self._active_layer=new_idx
        self._set_status(f"Layer moved {'up' if direction<0 else 'down'}.")

    # ── Map resize ────────────────────────────────────────────────────────────

    def _resize_map(self,nw,nh):
        nw=max(GRID_SIZE*20,nw); nh=max(GRID_SIZE*12,nh)
        self._push_undo(); self._world_w=nw; self._world_h=nh
        self._cam.clamp(nw,nh,self._vp_w,self._vp_h)
        self._set_status(f"Map resized to {nw}x{nh}")

    # ═══════════════════════════════════════════════════════════════════════════
    #  MAIN LOOP
    # ═══════════════════════════════════════════════════════════════════════════

    def run(self):
        while True:
            dt=self._clock.tick(60)/1000.0
            mx,my=pygame.mouse.get_pos()

            # ── Detect window resize (works for both pygame 1 and 2) ──────────
            surf_size=self._screen.get_size()
            if surf_size!=(self._sw,self._sh):
                self._sw,self._sh=surf_size
                self._build_ui()
                self._cam.clamp(self._world_w,self._world_h,self._vp_w,self._vp_h)

            for b in self._tool_btns.values(): b.update(mx,my)
            for b in self._action_btns: b.update(mx,my)
            self._btn_load_asset.update(mx,my); self._btn_remove_asset.update(mx,my)
            self._btn_add_layer.update(mx,my);  self._btn_del_layer.update(mx,my)
            self._btn_layer_up.update(mx,my);   self._btn_layer_down.update(mx,my)
            for t,b in self._tool_btns.items(): b.is_active=(t==self._tool)

            if self._status_ttl>0: self._status_ttl=max(0.0,self._status_ttl-dt)

            # Handle cursor for resize handles
            if (self._in_vp(mx,my) and self._tool==Tool.SELECT
                    and self._selected and not self._selected.is_point):
                h=self._hit_handle(self._selected,mx,my)
                self._hovered_handle=h
                cursors={
                    'tl':pygame.SYSTEM_CURSOR_SIZENWSE,'tr':pygame.SYSTEM_CURSOR_SIZENESW,
                    'bl':pygame.SYSTEM_CURSOR_SIZENESW,'br':pygame.SYSTEM_CURSOR_SIZENWSE,
                    'tm':pygame.SYSTEM_CURSOR_SIZENS,  'bm':pygame.SYSTEM_CURSOR_SIZENS,
                    'ml':pygame.SYSTEM_CURSOR_SIZEWE,  'mr':pygame.SYSTEM_CURSOR_SIZEWE,
                }
                try: pygame.mouse.set_cursor(cursors[h] if h else pygame.SYSTEM_CURSOR_ARROW)
                except Exception: pass
            else:
                self._hovered_handle=""
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            for ev in pygame.event.get():
                if ev.type==pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif ev.type==pygame.MOUSEWHEEL:
                    if self._in_vp(mx,my):
                        self._cam.zoom_at(mx,my,1.13 if ev.y>0 else 1/1.13)
                    elif self._in_panel(mx,my) and self._active_tab=="assets":
                        self._asset_scroll=max(0,self._asset_scroll-ev.y*20)
                elif ev.type==pygame.MOUSEBUTTONDOWN:
                    self._on_down(ev,mx,my)
                elif ev.type==pygame.MOUSEBUTTONUP:
                    self._on_up(ev,mx,my)
                elif ev.type==pygame.MOUSEMOTION:
                    self._on_motion(ev,mx,my)
                elif ev.type==pygame.KEYDOWN:
                    if not self._on_key(ev):
                        pygame.quit(); sys.exit()

            keys=pygame.key.get_pressed()
            spd=self.CAM_SPEED*dt
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self._cam.pan(-spd,0)
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self._cam.pan( spd,0)
            if keys[pygame.K_w] or keys[pygame.K_UP]:    self._cam.pan(0,-spd)
            if keys[pygame.K_DOWN]:                       self._cam.pan(0, spd)
            self._cam.clamp(self._world_w,self._world_h,self._vp_w,self._vp_h)
            self._draw(mx,my)

    def _in_vp(self,mx,my): return VP_X<=mx<self._sw and 0<=my<self._sh-STATUS_H
    def _in_panel(self,mx,my): return 0<=mx<PANEL_W and 0<=my<self._sh-STATUS_H

    # ═══════════════════════════════════════════════════════════════════════════
    #  EVENTS
    # ═══════════════════════════════════════════════════════════════════════════

    def _on_down(self,ev,mx,my):
        if ev.button==2 and self._in_vp(mx,my):
            self._panning=True; self._pan_origin=(mx,my)
            self._pan_cam0=(self._cam.x,self._cam.y); return

        if self._in_panel(mx,my):
            self._panel_click(mx,my); return
        if not self._in_vp(mx,my): return

        wx,wy=self._cam.s2w(mx,my)

        if ev.button==3:
            hit=self._find_at(wx,wy)
            if hit: self._delete_obj(hit)
            return

        if ev.button!=1: return

        if self._tool==Tool.SELECT:
            # 1 – check resize handles
            if self._selected and not self._selected.is_point:
                h=self._hit_handle(self._selected,mx,my)
                if h:
                    self._resizing=True; self._resize_handle=h
                    self._resize_orig=(self._selected.x,self._selected.y,
                                       self._selected.w,self._selected.h)
                    self._resize_pre=copy.deepcopy(self._objects); return
            # 2 – pick object
            hit=self._find_at(wx,wy)
            if hit:
                self._selected=hit; self._moving=True
                self._move_pre=copy.deepcopy(self._objects)
                if hit.is_point: self._move_offset=(hit.cx-wx,hit.cy-wy)
                else:            self._move_offset=(hit.x-wx,hit.y-wy)
            else: self._selected=None
            return

        obj_type=self._tool.value
        if obj_type in POINT_TYPES:
            self._point_last_cell=None
            self._place_point(obj_type,wx,wy); self._point_dragging=True
        elif obj_type=="sprite" and not self._assets.active_key:
            self._set_status("No asset selected! Go to the Assets tab first.")
        else:
            snx,sny=self._sp(wx,wy)
            self._rect_placing=True; self._rect_start=(snx,sny); self._rect_preview=None

    def _on_up(self,ev,mx,my):
        if ev.button==2: self._panning=False; return
        if ev.button!=1: return

        if self._rect_placing and self._rect_preview:
            p=self._rect_preview
            if p.w>=MIN_RECT and p.h>=MIN_RECT:
                self._push_undo(); self._objects.append(p.clone())
                self._set_status(f"Placed {OBJ_LABELS.get(p.obj_type,'?')} "
                                  f"({int(p.w)}x{int(p.h)} @ {int(p.x)},{int(p.y)})")
            self._rect_preview=None; self._rect_placing=False

        if self._resizing:
            if self._resize_pre is not None:
                o=self._resize_orig; s=self._selected
                if s and (s.x!=o[0] or s.y!=o[1] or s.w!=o[2] or s.h!=o[3]):
                    self._undo.append((self._resize_pre,copy.deepcopy(self._layers),
                                       self._world_w,self._world_h))
                    self._redo.clear()
            self._resizing=False; self._resize_handle=""; self._resize_pre=None

        if self._moving:
            if self._move_pre is not None:
                self._undo.append((self._move_pre,copy.deepcopy(self._layers),
                                   self._world_w,self._world_h))
                self._redo.clear()
            self._moving=False; self._move_pre=None

        if self._point_dragging:
            self._point_dragging=False; self._point_last_cell=None

    def _on_motion(self,ev,mx,my):
        wx,wy=self._cam.s2w(mx,my)

        if self._panning:
            dx=mx-self._pan_origin[0]; dy=my-self._pan_origin[1]
            self._cam.x=self._pan_cam0[0]-dx/self._cam.zoom
            self._cam.y=self._pan_cam0[1]-dy/self._cam.zoom
            self._cam.clamp(self._world_w,self._world_h); return

        if self._resizing and self._selected:
            self._apply_resize(self._resize_handle,wx,wy); return

        if self._moving and self._selected:
            s=self._selected; ox,oy=self._move_offset
            if s.is_point:
                snx,sny=self._sp(wx+ox,wy+oy); s.x=snx-s.w/2; s.y=sny-s.h/2
            else: s.x=self._sv(wx+ox); s.y=self._sv(wy+oy)
            return

        if self._rect_placing:
            snx,sny=self._sp(wx,wy); x0,y0=self._rect_start
            x=min(x0,snx); y=min(y0,sny)
            w=max(abs(snx-x0),MIN_RECT); h=max(abs(sny-y0),MIN_RECT)
            ot=self._tool.value
            li=TOOL_DEFAULT_LAYER.get(ot,self._active_li())
            ak=self._assets.active_key if ot=="sprite" else None
            self._rect_preview=MapObject(ot,x,y,w,h,li,ak); return

        if self._point_dragging and self._in_vp(mx,my):
            self._place_point(self._tool.value,wx,wy)

    def _on_key(self,ev)->bool:
        ctrl=ev.mod&pygame.KMOD_CTRL; shift=ev.mod&pygame.KMOD_SHIFT

        # ── Layer rename mode captures almost all keys ────────────────────────
        if self._rename_idx>=0:
            if ev.key==pygame.K_RETURN or ev.key==pygame.K_KP_ENTER:
                name=self._rename_buf.strip() or f"Layer {self._rename_idx}"
                self._push_undo()
                self._layers[self._rename_idx].name=name
                self._rename_idx=-1
                self._set_status(f"Renamed to '{name}'")
            elif ev.key==pygame.K_ESCAPE:
                self._rename_idx=-1
                self._set_status("Rename cancelled.")
            elif ev.key==pygame.K_BACKSPACE:
                self._rename_buf=self._rename_buf[:-1]
            elif ev.unicode and len(self._rename_buf)<28:
                self._rename_buf+=ev.unicode
            return True   # consume all keys while renaming

        if ev.key==pygame.K_q and not ctrl: return False
        # ── Help overlay ──────────────────────────────────────────────────────
        if ev.key==pygame.K_F1:
            self._show_help=not self._show_help; return True
        # ── Window size shortcuts ─────────────────────────────────────────────
        if ev.key==pygame.K_F11:
            flags=self._screen.get_flags()
            if flags&pygame.FULLSCREEN:
                self._screen=pygame.display.set_mode(
                    (SCREEN_W,SCREEN_H), pygame.RESIZABLE)
            else:
                self._screen=pygame.display.set_mode(
                    (0,0), pygame.FULLSCREEN|pygame.RESIZABLE)
            self._sw,self._sh=self._screen.get_size()
            self._build_ui(); return True
        if ev.key==pygame.K_F10:
            flags=self._screen.get_flags()
            if (self._sw,self._sh)==(SCREEN_W,SCREEN_H):
                info=pygame.display.Info()
                self._screen=pygame.display.set_mode(
                    (info.current_w,info.current_h), pygame.RESIZABLE)
            else:
                self._screen=pygame.display.set_mode(
                    (SCREEN_W,SCREEN_H), pygame.RESIZABLE)
            self._sw,self._sh=self._screen.get_size()
            self._build_ui(); return True
        if ctrl:
            if ev.key==pygame.K_s: self._save()
            elif ev.key==pygame.K_l: self._load()
            elif ev.key==pygame.K_e: self._export()
            elif ev.key==pygame.K_z: self._do_redo() if shift else self._do_undo()
            elif ev.key==pygame.K_y: self._do_redo()
            elif ev.key==pygame.K_d: self._duplicate_selected()
        else:
            if ev.key in(pygame.K_DELETE,pygame.K_BACKSPACE): self._delete_selected()
            elif ev.key==pygame.K_g:
                self._show_grid=not self._show_grid
            elif ev.key==pygame.K_s:
                self._snap=not self._snap
                self._set_status(f"Snap: {'ON' if self._snap else 'OFF'}")
            elif ev.key==pygame.K_ESCAPE:
                self._show_help=False
                self._selected=None; self._rect_placing=False
                self._rect_preview=None; self._point_dragging=False
        return True

    # ── Panel click dispatcher ────────────────────────────────────────────────

    def _panel_click(self,mx,my):
        for k,r in self._tabs.items():
            if r.collidepoint(mx,my): self._active_tab=k; return
        if   self._active_tab=="tools":  self._tools_click(mx,my)
        elif self._active_tab=="layers": self._layers_click(mx,my)
        elif self._active_tab=="assets": self._assets_click(mx,my)
        elif self._active_tab=="map":    self._map_click(mx,my)

    def _tools_click(self,mx,my):
        for t,b in self._tool_btns.items():
            if b.hit(mx,my):
                self._tool=t
                if t!=Tool.SPRITE: self._assets.active_key=None
                self._selected=None; return
        if self._btn_save.hit(mx,my):   self._save();   return
        if self._btn_load.hit(mx,my):   self._load();   return
        if self._btn_export.hit(mx,my): self._export(); return
        if self._btn_clear.hit(mx,my) and self._objects:
            self._push_undo(); self._objects.clear()
            self._selected=None; self._set_status("Cleared all objects.")

    def _layers_click(self,mx,my):
        if self._btn_add_layer.hit(mx,my):   self._add_layer();       return
        if self._btn_del_layer.hit(mx,my):   self._remove_layer();    return
        if self._btn_layer_up.hit(mx,my):    self._move_layer(-1);    return
        if self._btn_layer_down.hit(mx,my):  self._move_layer(+1);    return
        row_h=38; ly=HEADER_H+TAB_H+8
        now=pygame.time.get_ticks()/1000.0
        for i,layer in enumerate(self._layers):
            ry=ly+i*row_h
            if not pygame.Rect(4,ry,PANEL_W-8,row_h-2).collidepoint(mx,my):
                continue

            # ── colour dot click ─────────────────────────────────────────────
            dot_rect=pygame.Rect(10,ry+row_h//2-9,18,18)
            if dot_rect.collidepoint(mx,my):
                self._push_undo()
                cur=tuple(layer.color)
                try:    nxt=(LAYER_PALETTE.index(cur)+1)%len(LAYER_PALETTE)
                except  ValueError: nxt=0
                layer.color=LAYER_PALETTE[nxt]
                return

            # ── eye / lock icons ─────────────────────────────────────────────
            eye =pygame.Rect(PANEL_W-46,ry+6,20,24)
            lock=pygame.Rect(PANEL_W-24,ry+6,20,24)
            if eye.collidepoint(mx,my):
                self._push_undo(); layer.visible=not layer.visible; return
            if lock.collidepoint(mx,my):
                self._push_undo(); layer.locked=not layer.locked;   return

            # ── double-click → start rename ──────────────────────────────────
            if (now-self._dbl_last_time<0.35 and self._dbl_last_layer==i):
                self._rename_idx=i
                self._rename_buf=layer.name
                self._dbl_last_time=0.0
                self._set_status(f"Renaming layer {i} — type, Enter=confirm, Esc=cancel")
                return

            # ── single click → select layer ──────────────────────────────────
            self._active_layer=i
            self._dbl_last_time=now
            self._dbl_last_layer=i
            return

    def _assets_click(self,mx,my):
        if self._btn_load_asset.hit(mx,my): self._load_asset(); return
        if self._btn_remove_asset.hit(mx,my):
            if self._assets.active_key:
                self._assets.remove(self._assets.active_key)
                self._set_status("Asset removed.")
                if self._tool==Tool.SPRITE: self._tool=Tool.SELECT
            return
        aty=HEADER_H+TAB_H+8
        row_h=THUMB_H+12; ly0=aty+28+4+28+20
        for i,key in enumerate(self._assets.all_keys()):
            ry=ly0+i*row_h-self._asset_scroll
            if pygame.Rect(4,ry,PANEL_W-8,row_h-2).collidepoint(mx,my):
                if self._assets.active_key==key:
                    self._assets.active_key=None
                    if self._tool==Tool.SPRITE: self._tool=Tool.SELECT
                else:
                    self._assets.active_key=key; self._tool=Tool.SPRITE
                    self._set_status(f"Asset: {key}")
                return

    def _map_click(self,mx,my):
        cy=HEADER_H+TAB_H+14; px=8; bw=PANEL_W-16; hw=(bw-4)//2
        # Width buttons
        if pygame.Rect(px,     cy+40,hw,26).collidepoint(mx,my):
            self._resize_map(self._world_w-288,self._world_h); return
        if pygame.Rect(px+hw+4,cy+40,hw,26).collidepoint(mx,my):
            self._resize_map(self._world_w+288,self._world_h); return
        cy+=78
        # Height buttons
        if pygame.Rect(px,     cy+40,hw,26).collidepoint(mx,my):
            self._resize_map(self._world_w,self._world_h-160); return
        if pygame.Rect(px+hw+4,cy+40,hw,26).collidepoint(mx,my):
            self._resize_map(self._world_w,self._world_h+160); return
        cy+=78
        # Snap toggle
        if pygame.Rect(px,cy,bw,26).collidepoint(mx,my):
            self._snap=not self._snap
            self._set_status(f"Snap: {'ON' if self._snap else 'OFF'}"); return
        cy+=34
        # Grid toggle
        if pygame.Rect(px,cy,bw,26).collidepoint(mx,my):
            self._show_grid=not self._show_grid

    # ═══════════════════════════════════════════════════════════════════════════
    #  DRAW
    # ═══════════════════════════════════════════════════════════════════════════

    def _draw(self,mx,my):
        self._screen.fill(C_BG)
        self._draw_vp(mx,my)
        self._draw_panel(mx,my)
        self._draw_status(mx,my)
        if self._show_help:
            self._draw_help_overlay()
        self._update_caption()
        pygame.display.flip()

    def _update_caption(self):
        save_name=os.path.splitext(os.path.basename(self._save_path))[0]
        stars="*" if self._undo else ""
        pygame.display.set_caption(
            f"AOFT - Map Editor  |  {save_name}{stars}  |  "
            f"{self._world_w}x{self._world_h}  |  "
            f"{self._sw}x{self._sh}")

    def _draw_help_overlay(self):
        """Full-screen semi-transparent shortcut reference."""
        sw,sh=self._sw,self._sh
        ov=pygame.Surface((sw,sh),pygame.SRCALPHA)
        ov.fill(C_HELP_BG)
        self._screen.blit(ov,(0,0))

        cols=[(
            "NAVIGATION",
            ["WASD / Arrows  Move camera",
             "Middle drag    Pan",
             "Mouse wheel    Zoom in/out",
             "F10            Maximise/restore",
             "F11            Fullscreen toggle",
             "Q              Quit",]
        ),(
            "EDITING",
            ["Left click     Place / select",
             "Right click    Delete object",
             "Drag (rect)    Draw rectangle",
             "Drag (point)   Scatter points",
             "Delete/Bksp    Delete selected",
             "Ctrl+D         Duplicate",
             "Ctrl+Z/Y       Undo / Redo",]
        ),(
            "TOOLS & VIEW",
            ["G              Toggle grid",
             "S              Toggle snap",
             "Escape         Deselect / cancel",
             "Ctrl+S         Save",
             "Ctrl+L         Load",
             "Ctrl+E         Export map",
             "F1             Close this help",]
        ),(
            "LAYERS TAB",
            ["Click row      Set active layer",
             "Dbl-click name Rename layer",
             "Click dot      Cycle colour",
             "Eye icon       Toggle visibility",
             "Lock icon      Toggle lock",
             "^ Move Up/Down Reorder layers",]
        )]

        box_w=sw//4-20; box_h=260
        start_x=10; start_y=sh//2-box_h//2-30
        title=self._f15.render("AOFT - Map Editor  |  Shortcuts  (F1 to close)",True,C_HELP_HDR)
        self._screen.blit(title,(sw//2-title.get_width()//2, start_y-30))

        for ci,(heading,lines) in enumerate(cols):
            bx=start_x+ci*(box_w+10); by=start_y
            pygame.draw.rect(self._screen,(25,18,40,200),
                             (bx,by,box_w,box_h),border_radius=6)
            pygame.draw.rect(self._screen,C_HELP_HDR,(bx,by,box_w,box_h),1,border_radius=6)
            ht=self._f14.render(heading,True,C_HELP_HDR)
            self._screen.blit(ht,(bx+8,by+8))
            pygame.draw.line(self._screen,C_HELP_HDR,(bx+8,by+26),(bx+box_w-8,by+26))
            for li,line in enumerate(lines):
                t=self._f13.render(line,True,C_TEXT)
                self._screen.blit(t,(bx+8,by+34+li*18))

    # ── Viewport ──────────────────────────────────────────────────────────────

    def _draw_vp(self,mx,my):
        vw,vh=self._vp_w,self._vp_h
        self._screen.set_clip(pygame.Rect(VP_X,VP_Y,vw,vh))
        cam=self._cam

        # World rect
        wx0,wy0=cam.w2s(0,0); wx1,wy1=cam.w2s(self._world_w,self._world_h)
        wr=pygame.Rect(int(wx0),int(wy0),max(1,int(wx1-wx0)),max(1,int(wy1-wy0)))
        pygame.draw.rect(self._screen,C_WORLD_BG,wr)
        pygame.draw.rect(self._screen,C_WORLD_EDGE,wr,2)
        for cwx,cwy in[(0,0),(self._world_w,0),(0,self._world_h),(self._world_w,self._world_h)]:
            sx,sy=cam.w2s(cwx,cwy)
            pygame.draw.circle(self._screen,C_WORLD_EDGE,(int(sx),int(sy)),4)

        if self._show_grid: self._draw_grid(cam)

        # Draw objects sorted by layer (back to front)
        by_layer:Dict[int,List[MapObject]]={}
        for obj in self._objects: by_layer.setdefault(obj.layer_idx,[]).append(obj)
        for li in sorted(by_layer.keys()):
            if not self._lyr_visible(li): continue
            for obj in by_layer[li]:
                self._draw_obj(obj,selected=(obj is self._selected))

        if self._rect_preview:
            self._draw_obj(self._rect_preview,preview=True)

        if self._in_vp(mx,my) and self._tool!=Tool.SELECT and not self._rect_placing:
            self._draw_hover(cam,mx,my)

        self._draw_minimap()
        self._screen.set_clip(None)
        pygame.draw.line(self._screen,C_PANEL_EDGE,(VP_X,0),(VP_X,self._sh-STATUS_H),2)

    def _draw_grid(self,cam):
        vw,vh=self._vp_w,self._vp_h
        gs=GRID_SIZE*cam.zoom
        if gs<4: return
        wx0,wy0=cam.s2w(VP_X,0); wx1,wy1=cam.s2w(VP_X+vw,vh)
        gx=math.floor(wx0/GRID_SIZE)*GRID_SIZE
        while gx<=wx1+GRID_SIZE:
            sx,_=cam.w2s(gx,0)
            col=C_GRID_AXIS if gx==0 else(C_GRID_MAJ if gx%(GRID_SIZE*8)==0 else C_GRID)
            pygame.draw.line(self._screen,col,(int(sx),VP_Y),(int(sx),vh))
            gx+=GRID_SIZE
        gy=math.floor(wy0/GRID_SIZE)*GRID_SIZE
        while gy<=wy1+GRID_SIZE:
            _,sy=cam.w2s(0,gy)
            col=C_GRID_AXIS if gy==0 else(C_GRID_MAJ if gy%(GRID_SIZE*8)==0 else C_GRID)
            pygame.draw.line(self._screen,col,(VP_X,int(sy)),(VP_X+vw,int(sy)))
            gy+=GRID_SIZE

    def _draw_hover(self,cam,mx,my):
        wx,wy=cam.s2w(mx,my); snx,sny=self._sp(wx,wy)
        sx,sy=cam.w2s(snx,sny); gs=int(GRID_SIZE*cam.zoom)
        if gs<2: return
        h=pygame.Surface((gs,gs),pygame.SRCALPHA); h.fill(C_HOVER)
        self._screen.blit(h,(int(sx),int(sy)))

    def _draw_obj(self,obj,*,selected=False,preview=False):
        cam=self._cam; col=obj.color
        am=0.55 if not preview and self._lyr_locked(obj.layer_idx) else 1.0

        if obj.is_point:
            sx,sy=cam.w2s(obj.cx,obj.cy)
            r=max(5,int(POINT_R*cam.zoom))
            if preview:
                s=pygame.Surface((r*2+2,r*2+2),pygame.SRCALPHA)
                pygame.draw.circle(s,(*col,115),(r,r),r); self._screen.blit(s,(int(sx)-r,int(sy)-r))
            else:
                pygame.draw.circle(self._screen,(0,0,0),(int(sx)+2,int(sy)+2),r)
                dc=tuple(int(c*am) for c in col)
                pygame.draw.circle(self._screen,dc,(int(sx),int(sy)),r)
                rim=tuple(min(255,c+55) for c in col)
                pygame.draw.circle(self._screen,rim,(int(sx),int(sy)),r,2)
                it=self._f14.render(OBJ_ICONS.get(obj.obj_type,"?"),True,(255,255,255))
                self._screen.blit(it,(int(sx)-it.get_width()//2,int(sy)-it.get_height()//2))
                if cam.zoom>=0.55:
                    lt=self._f11.render(OBJ_LABELS.get(obj.obj_type,"").split()[0],True,(180,180,180))
                    self._screen.blit(lt,(int(sx)-lt.get_width()//2,int(sy)+r+2))
            if selected:
                pygame.draw.circle(self._screen,C_SEL,(int(sx),int(sy)),r+3,2)
        else:
            sx,sy=cam.w2s(obj.x,obj.y)
            sw=max(2,int(obj.w*cam.zoom)); sh=max(2,int(obj.h*cam.zoom))
            rect=pygame.Rect(int(sx),int(sy),sw,sh)
            if preview:
                s=pygame.Surface((max(1,rect.w),max(1,rect.h)),pygame.SRCALPHA)
                s.fill((*col,110)); self._screen.blit(s,rect.topleft)
                pygame.draw.rect(self._screen,col,rect,1)
                ht=self._f11.render(f"{int(obj.w)}x{int(obj.h)}",True,(220,220,220))
                self._screen.blit(ht,(rect.x+4,rect.y+3))
            else:
                # Sprite: render asset image
                if obj.obj_type=="sprite" and obj.asset_key:
                    img=self._assets.get(obj.asset_key)
                    if img and sw>0 and sh>0:
                        try:
                            sc=pygame.transform.scale(img,(sw,sh))
                            if am<1.0: sc=sc.copy(); sc.set_alpha(int(255*am))
                            self._screen.blit(sc,rect.topleft)
                        except Exception: pygame.draw.rect(self._screen,col,rect)
                    else:
                        pygame.draw.rect(self._screen,col,rect)
                        mt=self._f11.render("NO ASSET",True,(255,80,80))
                        self._screen.blit(mt,(rect.x+2,rect.y+2))
                else:
                    dc=tuple(int(c*am) for c in col)
                    pygame.draw.rect(self._screen,dc,rect)
                    hl=tuple(min(255,int(c*am)+42) for c in col)
                    pygame.draw.line(self._screen,hl,rect.topleft,rect.topright,2)
                    bl=tuple(max(0,int(c*am)-18) for c in col)
                    pygame.draw.rect(self._screen,bl,rect,1)

                if rect.w>50 and rect.h>14 and cam.zoom>=0.35:
                    lbl=(os.path.splitext(obj.asset_key)[0][:12]
                         if obj.obj_type=="sprite" and obj.asset_key
                         else OBJ_LABELS.get(obj.obj_type,obj.obj_type))
                    lt=self._f11.render(lbl,True,(200,200,200))
                    lx=rect.centerx-lt.get_width()//2; ly=rect.centery-lt.get_height()//2
                    if rect.collidepoint(lx,ly): self._screen.blit(lt,(lx,ly))

            if selected:
                pygame.draw.rect(self._screen,C_SEL,rect,2)
                if not obj.is_point and cam.zoom>=0.22:
                    for h,(hx,hy) in self._handle_pts(obj).items():
                        hc=C_HANDLE_HOV if h==self._hovered_handle else C_HANDLE
                        pygame.draw.rect(self._screen,(0,0,0),
                                         (hx-HANDLE_R-1,hy-HANDLE_R-1,HANDLE_R*2+2,HANDLE_R*2+2))
                        pygame.draw.rect(self._screen,hc,
                                         (hx-HANDLE_R,hy-HANDLE_R,HANDLE_R*2,HANDLE_R*2))

    def _draw_minimap(self):
        vw,vh=self._vp_w,self._vp_h
        MW=160; MH=max(40,int(160*self._world_h/max(1,self._world_w))); MH=min(MH,100)
        mmx=VP_X+vw-MW-8; mmy=vh-MH-8
        s=pygame.Surface((MW,MH),pygame.SRCALPHA); s.fill((0,0,0,165))
        scx=MW/self._world_w; scy=MH/self._world_h
        for obj in self._objects:
            if not self._lyr_visible(obj.layer_idx): continue
            c=obj.color
            if obj.is_point:
                pygame.draw.circle(s,c,(int(obj.cx*scx),int(obj.cy*scy)),2)
            else:
                rr=pygame.Rect(int(obj.x*scx),int(obj.y*scy),
                               max(1,int(obj.w*scx)),max(1,int(obj.h*scy)))
                pygame.draw.rect(s,c,rr)
        cam=self._cam; vrx=int(cam.x*scx); vry=int(cam.y*scy)
        vrw=max(2,int(vw/cam.zoom*scx)); vrh=max(2,int(vh/cam.zoom*scy))
        vi=pygame.Surface((max(2,vrw),max(2,vrh)),pygame.SRCALPHA); vi.fill((200,200,200,45))
        s.blit(vi,(vrx,vry)); pygame.draw.rect(s,(215,215,215,180),(vrx,vry,max(2,vrw),max(2,vrh)),1)
        pygame.draw.rect(s,C_PANEL_EDGE,(0,0,MW,MH),1)
        self._screen.blit(s,(mmx,mmy))
        lt=self._f11.render("MINIMAP",True,C_TEXT_DIM); self._screen.blit(lt,(mmx,mmy-14))

    # ── Panel ─────────────────────────────────────────────────────────────────

    def _draw_panel(self,mx,my):
        sh=self._sh
        pygame.draw.rect(self._screen,C_PANEL,(0,0,PANEL_W,sh-STATUS_H))

        # ── AOFT brand header ─────────────────────────────────────────────────
        pygame.draw.rect(self._screen,C_HEADER_BG,(0,0,PANEL_W,HEADER_H))
        pygame.draw.line(self._screen,C_HEADER_ACT,(0,HEADER_H-1),(PANEL_W,HEADER_H-1),1)
        # Accent bar on the left edge
        pygame.draw.rect(self._screen,C_HEADER_ACT,(0,0,3,HEADER_H))
        # Title text
        aoft=self._f15.render("AOFT",True,C_HEADER_ACT)
        sub =self._f11.render("Map Editor",True,C_HEADER_DIM)
        self._screen.blit(aoft,(10,HEADER_H//2-aoft.get_height()//2))
        self._screen.blit(sub, (10+aoft.get_width()+6, HEADER_H//2-sub.get_height()//2))
        # Object count badge (top-right of header)
        badge_txt=f"{len(self._objects)} obj"
        bt=self._f11.render(badge_txt,True,C_HEADER_DIM)
        self._screen.blit(bt,(PANEL_W-bt.get_width()-8, HEADER_H//2-bt.get_height()//2))

        # ── Tabs ──────────────────────────────────────────────────────────────
        for k,rect in self._tabs.items():
            ia=(k==self._active_tab)
            pygame.draw.rect(self._screen,C_TAB_ACT if ia else C_TAB,rect)
            pygame.draw.rect(self._screen,C_TAB_EDGE,rect,1)
            lbl={"tools":"TOOLS","layers":"LAYERS","assets":"ASSETS","map":"MAP"}[k]
            t=self._f13.render(lbl,True,C_TEXT_ACT if ia else C_TEXT_DIM)
            self._screen.blit(t,(rect.centerx-t.get_width()//2,rect.centery-t.get_height()//2))
        pygame.draw.line(self._screen,C_PANEL_EDGE,
                         (0,HEADER_H+TAB_H),(PANEL_W,HEADER_H+TAB_H),1)

        if   self._active_tab=="tools":  self._draw_tools_tab(mx,my)
        elif self._active_tab=="layers": self._draw_layers_tab(mx,my)
        elif self._active_tab=="assets": self._draw_assets_tab(mx,my)
        elif self._active_tab=="map":    self._draw_map_tab(mx,my)

        pygame.draw.line(self._screen,C_PANEL_EDGE,(PANEL_W-1,0),(PANEL_W-1,sh-STATUS_H),2)

    def _draw_tools_tab(self,mx,my):
        for b in self._tool_btns.values(): b.draw(self._screen,self._f13)
        pygame.draw.line(self._screen,C_PANEL_EDGE,(8,self._sep_y),(PANEL_W-8,self._sep_y))
        for b in self._action_btns: b.draw(self._screen,self._f13)

        # Counts
        counts:Dict[str,int]={}
        for obj in self._objects: counts[obj.obj_type]=counts.get(obj.obj_type,0)+1
        iy=self._action_btns[-1].rect.bottom+12
        pygame.draw.line(self._screen,C_PANEL_EDGE,(8,iy),(PANEL_W-8,iy)); iy+=8
        t=self._f13.render(f"Objects: {len(self._objects)}",True,C_TEXT)
        self._screen.blit(t,(10,iy)); iy+=16
        for ot,lb in OBJ_LABELS.items():
            n=counts.get(ot,0); c=OBJ_COLORS.get(ot,(150,150,150))
            t=self._f11.render(f"  {lb}: {n}",True,c if n>0 else C_TEXT_DIM)
            self._screen.blit(t,(10,iy)); iy+=13
        iy+=4
        t=self._f11.render(f"Snap:{'ON' if self._snap else 'OFF'}  "
                            f"Grid:{'ON' if self._show_grid else 'OFF'}",True,C_TEXT_DIM)
        self._screen.blit(t,(10,iy)); iy+=14
        # Selected info
        if self._selected:
            iy+=4; pygame.draw.line(self._screen,C_PANEL_EDGE,(8,iy),(PANEL_W-8,iy)); iy+=6
            s=self._selected; lb=OBJ_LABELS.get(s.obj_type,s.obj_type)
            t=self._f13.render(f"SEL: {lb}",True,C_TEXT_ACT); self._screen.blit(t,(10,iy)); iy+=15
            t=self._f11.render(f"  Pos: {int(s.x)},{int(s.y)}",True,C_TEXT); self._screen.blit(t,(10,iy)); iy+=13
            if not s.is_point:
                t=self._f11.render(f"  Size: {int(s.w)}x{int(s.h)}",True,C_TEXT)
                self._screen.blit(t,(10,iy)); iy+=13
            li=s.layer_idx
            ln=self._layers[li].name if li<len(self._layers) else f"L{li}"
            t=self._f11.render(f"  Layer: {ln}",True,C_TEXT_DIM); self._screen.blit(t,(10,iy)); iy+=13
            if s.asset_key:
                t=self._f11.render(f"  Asset: {s.asset_key[:18]}",True,C_TEXT_DIM)
                self._screen.blit(t,(10,iy))
        iy=self._sh-STATUS_H-16
        t=self._f11.render(f"Undo:{len(self._undo)}  Redo:{len(self._redo)}",True,C_TEXT_DIM)
        self._screen.blit(t,(10,iy))

    def _draw_layers_tab(self,mx,my):
        sh=self._sh; row_h=38; ly=HEADER_H+TAB_H+8
        # Reserve space for 4 bottom buttons (2 rows) + footer label
        btm_reserve=28*2+5+22
        clip_h=sh-STATUS_H-btm_reserve-ly
        self._screen.set_clip(pygame.Rect(0,ly,PANEL_W,max(0,clip_h)))
        for i,layer in enumerate(self._layers):
            ry=ly+i*row_h; ia=(i==self._active_li())
            ih=pygame.Rect(4,ry,PANEL_W-8,row_h-2).collidepoint(mx,my)
            bg=C_LAYER_ACT if ia else(C_LAYER_HOV if ih else C_LAYER_ROW)
            pygame.draw.rect(self._screen,bg,(4,ry,PANEL_W-8,row_h-2),border_radius=3)
            pygame.draw.rect(self._screen,C_PANEL_EDGE,(4,ry,PANEL_W-8,row_h-2),1,border_radius=3)

            # colour dot (clickable)
            pygame.draw.circle(self._screen,layer.color,(18,ry+row_h//2),8)
            pygame.draw.circle(self._screen,(0,0,0),(18,ry+row_h//2),8,1)

            # active arrow indicator
            if ia:
                pygame.draw.polygon(self._screen,C_TEXT_ACT,
                    [(30,ry+row_h//2-4),(30,ry+row_h//2+4),(36,ry+row_h//2)])

            # Name – show input box if currently being renamed
            if self._rename_idx==i:
                nr=pygame.Rect(38,ry+5,PANEL_W-90,row_h-10)
                pygame.draw.rect(self._screen,C_RENAME_BG,nr,border_radius=3)
                pygame.draw.rect(self._screen,C_RENAME_BOR,nr,1,border_radius=3)
                cursor="_" if (pygame.time.get_ticks()//400)%2==0 else ""
                rt=self._f13.render(self._rename_buf+cursor,True,(180,255,180))
                self._screen.blit(rt,(nr.x+4,nr.centery-rt.get_height()//2))
            else:
                nt=self._f13.render(layer.name,True,C_TEXT_ACT if ia else C_TEXT)
                self._screen.blit(nt,(38,ry+row_h//2-nt.get_height()//2))

            # eye toggle
            ex=PANEL_W-46; ec=(80,210,120) if layer.visible else(55,55,55)
            pygame.draw.ellipse(self._screen,ec,(ex+2,ry+row_h//2-5,16,10))
            pygame.draw.circle(self._screen,(10,10,10) if layer.visible else ec,(ex+10,ry+row_h//2),4)

            # lock toggle
            lkx=PANEL_W-24; lkc=(220,160,50) if layer.locked else(55,55,55)
            pygame.draw.rect(self._screen,lkc,(lkx+2,ry+row_h//2-1,12,10),border_radius=2)
            arc=pygame.Rect(lkx+3,ry+row_h//2-7,10,10)
            pygame.draw.arc(self._screen,lkc,arc,math.pi*0.1,math.pi*0.9,2)

        self._screen.set_clip(None)

        # Bottom buttons
        self._btn_layer_up.draw(self._screen,self._f13)
        self._btn_layer_down.draw(self._screen,self._f13)
        self._btn_add_layer.draw(self._screen,self._f13)
        self._btn_del_layer.draw(self._screen,self._f13)

        # Footer hint
        li=self._active_li()
        ln=self._layers[li].name if li<len(self._layers) else "?"
        hint = "Renaming…  Enter=OK  Esc=cancel" if self._rename_idx>=0 \
               else f"Active: {ln}  |  Dbl-click=rename  Dot=colour"
        t=self._f11.render(hint,True,
                           C_RENAME_BOR if self._rename_idx>=0 else C_TEXT_DIM)
        self._screen.blit(t,(6,sh-STATUS_H-14))

    def _draw_assets_tab(self,mx,my):
        sh=self._sh; aty=HEADER_H+TAB_H+8
        self._btn_load_asset.draw(self._screen,self._f13)
        self._btn_remove_asset.draw(self._screen,self._f13)
        keys=self._assets.all_keys()
        count_y=aty+28+4+28+4
        t=self._f11.render(f"Loaded: {len(keys)} asset(s)",True,C_TEXT_DIM)
        self._screen.blit(t,(10,count_y))
        row_h=THUMB_H+12; ly0=aty+28+4+28+20; lh=sh-STATUS_H-ly0
        self._screen.set_clip(pygame.Rect(0,ly0,PANEL_W,max(0,lh)))
        for i,key in enumerate(keys):
            ry=ly0+i*row_h-self._asset_scroll
            if ry+row_h<ly0 or ry>sh-STATUS_H: continue
            ia=(key==self._assets.active_key)
            ih=pygame.Rect(4,ry,PANEL_W-8,row_h-2).collidepoint(mx,my)
            bg=(50,40,75) if ia else((38,33,55) if ih else(28,24,40))
            pygame.draw.rect(self._screen,bg,(4,ry,PANEL_W-8,row_h-2),border_radius=3)
            if ia: pygame.draw.rect(self._screen,C_TEXT_ACT,(4,ry,PANEL_W-8,row_h-2),1,border_radius=3)
            thumb=self._assets.get_thumb(key)
            if thumb:
                tw2,th2=thumb.get_size()
                self._screen.blit(thumb,(10,ry+(row_h-th2)//2))
            disp=key[:16]+(".." if len(key)>16 else "")
            ft=self._f13.render(disp,True,C_TEXT_ACT if ia else C_TEXT)
            self._screen.blit(ft,(10+THUMB_W+4,ry+4))
            img=self._assets.get(key)
            if img:
                dt=self._f11.render(f"{img.get_width()}x{img.get_height()}",True,C_TEXT_DIM)
                self._screen.blit(dt,(10+THUMB_W+4,ry+20))
        self._screen.set_clip(None)
        if keys and lh>0:
            max_scroll=max(0,len(keys)*row_h-lh)
            self._asset_scroll=min(self._asset_scroll,max_scroll)

    def _draw_map_tab(self,mx,my):
        cy=HEADER_H+TAB_H+14; px=8; bw=PANEL_W-16; hw=(bw-4)//2

        def row(y,label,val,unit=""):
            t=self._f13.render(label,True,C_TEXT); self._screen.blit(t,(px,y))
            v=self._f15.render(f"{val}{unit}",True,C_TEXT_ACT); self._screen.blit(v,(px,y+16))

        def pm_btns(y,lbl_m,lbl_p):
            mr=pygame.Rect(px,     y,hw,26); pr=pygame.Rect(px+hw+4,y,hw,26)
            mc=C_BTN_HOV if mr.collidepoint(mx,my) else C_BTN
            pc=C_BTN_HOV if pr.collidepoint(mx,my) else C_BTN
            pygame.draw.rect(self._screen,mc,mr,border_radius=4)
            pygame.draw.rect(self._screen,pc,pr,border_radius=4)
            for r2,lb in((mr,lbl_m),(pr,lbl_p)):
                t=self._f13.render(lb,True,C_BTN_TXT)
                self._screen.blit(t,(r2.centerx-t.get_width()//2,r2.centery-t.get_height()//2))

        row(cy,"World Width",self._world_w,"px")
        pm_btns(cy+40,"- 288px","+ 288px"); cy+=78
        pygame.draw.line(self._screen,C_PANEL_EDGE,(8,cy),(PANEL_W-8,cy)); cy+=8
        row(cy,"World Height",self._world_h,"px")
        pm_btns(cy+40,"- 160px","+ 160px"); cy+=78
        pygame.draw.line(self._screen,C_PANEL_EDGE,(8,cy),(PANEL_W-8,cy)); cy+=10

        cw=self._world_w//GRID_SIZE; ch=self._world_h//GRID_SIZE
        t=self._f11.render(f"Grid: {GRID_SIZE}px  |  Cells: {cw}x{ch}",True,C_TEXT_DIM)
        self._screen.blit(t,(px,cy)); cy+=20
        pygame.draw.line(self._screen,C_PANEL_EDGE,(8,cy),(PANEL_W-8,cy)); cy+=10

        def toggle_btn(y,label,on):
            r2=pygame.Rect(px,y,bw,26)
            col=(50,130,55) if on else(C_BTN_HOV if r2.collidepoint(mx,my) else C_BTN)
            pygame.draw.rect(self._screen,col,r2,border_radius=4)
            pygame.draw.rect(self._screen,C_PANEL_EDGE,r2,1,border_radius=4)
            t=self._f13.render(label,True,C_BTN_TXT)
            self._screen.blit(t,(r2.centerx-t.get_width()//2,r2.centery-t.get_height()//2))

        toggle_btn(cy, f"Snap to Grid: {'ON' if self._snap else 'OFF'}  [S]",     self._snap);      cy+=34
        toggle_btn(cy, f"Show Grid:  {'ON' if self._show_grid else 'OFF'}  [G]",   self._show_grid); cy+=34
        pygame.draw.line(self._screen,C_PANEL_EDGE,(8,cy),(PANEL_W-8,cy)); cy+=10
        t=self._f11.render(f"Zoom: {self._cam.zoom:.2f}x",True,C_TEXT_DIM)
        self._screen.blit(t,(px,cy)); cy+=14
        t=self._f11.render(f"View: {int(self._vp_w/self._cam.zoom)}x{int(self._vp_h/self._cam.zoom)} world px",True,C_TEXT_DIM)
        self._screen.blit(t,(px,cy)); cy+=18
        pygame.draw.line(self._screen,C_PANEL_EDGE,(8,cy),(PANEL_W-8,cy)); cy+=8
        t=self._f11.render("F11  Fullscreen  |  F10  Maximise",True,C_TEXT_DIM)
        self._screen.blit(t,(px,cy)); cy+=14
        t=self._f11.render(f"Window: {self._sw}x{self._sh}",True,C_TEXT_DIM)
        self._screen.blit(t,(px,cy))

    # ── Status bar ────────────────────────────────────────────────────────────

    def _draw_status(self,mx,my):
        sw,sh=self._sw,self._sh
        pygame.draw.rect(self._screen,C_STATUS_BG,(0,sh-STATUS_H,sw,STATUS_H))
        pygame.draw.line(self._screen,C_PANEL_EDGE,(0,sh-STATUS_H),(sw,sh-STATUS_H))
        cam=self._cam; wx,wy=cam.s2w(mx,my); snx,sny=self._sp(wx,wy)
        tn={Tool.SELECT:"SELECT"}.get(self._tool,OBJ_LABELS.get(self._tool.value,"?").upper())
        ti=self._f14.render(f"[{tn}]",True,C_TEXT_ACT)
        self._screen.blit(ti,(8,sh-STATUS_H+7))
        if self._status_ttl>0:
            alpha=min(1.0,self._status_ttl/0.5)
            mc=tuple(int(c*alpha) for c in C_TEXT_ACT)
            mt=self._f14.render(self._status,True,mc)
            self._screen.blit(mt,(VP_X+10,sh-STATUS_H+7))
        li=self._active_li()
        ln=self._layers[li].name if li<len(self._layers) else f"L{li}"
        right=(f"World({int(wx)},{int(wy)})  "
               f"Grid({int(snx//GRID_SIZE)},{int(sny//GRID_SIZE)})  "
               f"Zoom:{cam.zoom:.2f}x  Layer:{ln}  "
               f"{sw}x{sh}")
        rt=self._f13.render(right,True,C_TEXT_DIM)
        self._screen.blit(rt,(sw-rt.get_width()-10,sh-STATUS_H+8))


# ═══════════════════════════════════════════════════════════════════════════════
#  GAME INTEGRATION HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def load_map_from_file(path: str) -> dict:
    """
    Load an exported map JSON for use in the main game.

    Usage in engine/world/level_from_file.py:
        data = load_map_from_file("export_map.json")
        for p in data["platforms"]:
            self.platforms.append(Platform(p["x"], p["y"], p["w"], p["h"]))
        for s in data.get("sprites", []):
            pass  # wire to your sprite/image entity
    """
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    MapEditor().run()