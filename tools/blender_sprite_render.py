#!/usr/bin/env python3
"""In Blender (headless) ein animiertes GLB als transparente Frontal-Sprite-Sequenz rendern.

Aufruf:
    blender -b -P tools/blender_sprite_render.py -- <model.glb> <outdir> [--res 512]
        [--test] [--back] [--frames-step N]

--test       nur EINEN Frame (Mitte) rendern, zum Ausrichten pruefen.
--back       Kamera auf die Rueckseite (+Y) statt Front (-Y), falls Modell andersrum steht.
"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
model = argv[0]
outdir = argv[1]
res = 512
test = "--test" in argv
back = "--back" in argv
step = 1
if "--res" in argv:        res = int(argv[argv.index("--res") + 1])
if "--frames-step" in argv: step = int(argv[argv.index("--frames-step") + 1])
os.makedirs(outdir, exist_ok=True)

# --- Szene leeren ---
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# --- GLB importieren ---
bpy.ops.import_scene.gltf(filepath=model)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
arms   = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]

# --- Animations-Framebereich aus der Action ---
fstart, fend = 1, 30
for a in arms:
    if a.animation_data and a.animation_data.action:
        r = a.animation_data.action.frame_range
        fstart, fend = int(r[0]), int(r[1])
bpy.context.scene.frame_start = fstart
bpy.context.scene.frame_end = fend

# --- Bounding-Box ueber alle Meshes (im aktuellen Frame, Weltkoordinaten) ---
bpy.context.scene.frame_set((fstart + fend) // 2)
bpy.context.view_layer.update()
mn = Vector((1e9, 1e9, 1e9)); mx = Vector((-1e9, -1e9, -1e9))
for m in meshes:
    for c in m.bound_box:
        w = m.matrix_world @ Vector(c)
        mn = Vector((min(mn[i], w[i]) for i in range(3)))
        mx = Vector((max(mx[i], w[i]) for i in range(3)))
center = (mn + mx) / 2
size = mx - mn
height = size.z if size.z > 0 else max(size)

# --- Ortho-Kamera frontal (-Y) bzw. hinten (+Y), Z = oben ---
cam_data = bpy.data.cameras.new("Cam"); cam_data.type = "ORTHO"
cam_data.ortho_scale = height * 1.15
cam = bpy.data.objects.new("Cam", cam_data); bpy.context.scene.collection.objects.link(cam)
dist = max(size) * 4 + 5
if back:
    cam.location = (center.x, center.y + dist, center.z)
    cam.rotation_euler = (math.pi / 2, 0, math.pi)
else:
    cam.location = (center.x, center.y - dist, center.z)
    cam.rotation_euler = (math.pi / 2, 0, 0)
bpy.context.scene.camera = cam

# --- Licht: Key-Sun von vorn-oben + weiches Ambient ueber die Welt ---
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_d); bpy.context.scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0, math.radians(-15 if not back else 195))
world = bpy.data.worlds.new("W"); bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 1.1  # ambient strength

# --- Render-Settings: EEVEE, transparent, quadratisch ---
scn = bpy.context.scene
try:
    scn.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    scn.render.engine = "BLENDER_EEVEE"
scn.render.film_transparent = True
scn.render.resolution_x = res
scn.render.resolution_y = res
scn.render.image_settings.file_format = "PNG"
scn.render.image_settings.color_mode = "RGBA"

def render_frame(f, name):
    scn.frame_set(f)
    scn.render.filepath = os.path.join(outdir, name)
    bpy.ops.render.render(write_still=True)

if test:
    render_frame((fstart + fend) // 2, "test.png")
    print(f"TEST gerendert: bbox h={height:.2f} frames {fstart}..{fend}")
else:
    i = 0
    for f in range(fstart, fend + 1, step):
        render_frame(f, f"{i:02d}.png")
        i += 1
    print(f"SEQUENZ gerendert: {i} Frames ({fstart}..{fend} step {step})")
