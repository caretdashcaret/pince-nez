import bpy

def extrude_curve(selected_curve):
    """create the basic extrusion from curve"""
    bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN") #move the object to the center
    
    selected_curve.extrude = 0.005 #extrude path to create mesh
    #selected_curve.bevel_depth = 0.001 #bevel the edges

    bpy.ops.object.convert(target='MESH', keep_original=False) #convert from curve to mesh
    
def rotate_object():
    """Rotate the object 90 degrees on the X axis. Blender uses radians so rotate value is 1.570797"""

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all()
    bpy.ops.transform.rotate(value=1.570797, constraint_axis=(False, True, True)) #rotate 90 degrees only on the X
    bpy.ops.object.mode_set(mode="OBJECT")

def move_to_origin(selected_object):
    """move the selected object to origin"""
    bpy.ops.object.mode_set(mode="OBJECT")
    
    current_location = selected_object.location
    translation_vector = (-1*current_location[0], -1*current_location[1], -1*current_location[2]) #move to global origin
    bpy.ops.transform.translate(value=translation_vector)
    
def bisect(midpoint, number_of_segments, spacing):
    """bisect area around the midpoint, based on the number of segments and spacing"""
    bpy.ops.object.mode_set(mode="EDIT")

    lower_range = int(-1 * number_of_segments/2)
    upper_range = int(number_of_segments/2 + 1)
    spread = range(lower_range, upper_range)
    bisection_points = [x * spacing + midpoint for x in spread]

    for x_co in bisection_points:
        bpy.ops.mesh.select_all() #toggle select
        bpy.ops.mesh.select_all() #toggle select
        bpy.ops.mesh.bisect(plane_co=(x_co, 0.0, 0.0), plane_no=(1.0, 0.0, 0.0), threshold=0, xstart=0, xend=10, ystart=0, yend=100)

def bisect_bridge_area():
    """bisect the bridge area into 20 segments"""
    bisect(midpoint=0.0, number_of_segments=80, spacing=0.025)

def bend_object(selected_object):
    """apply the bend simple deform modifier"""
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.modifier_add(type="SIMPLE_DEFORM") #add simple deform modifier
    simple_deform_modifier = selected_object.modifiers["SimpleDeform"]
    simple_deform_modifier.deform_method = "BEND"
    simple_deform_modifier.angle = 0.523599 #Bend 30 degrees

    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="SimpleDeform") #apply modifier
    
def scale(value=100.0):
    """scale the object to 100x the size"""
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.transform.resize(value=(100.0, 100.0, 100.0)) #scale 100x for easier translations

def bisect_left_lens_area():
    bisect(midpoint=-8.0, number_of_segments=5, spacing=1.0)
def bisect_right_lens_area():
    bisect(midpoint=8.0, number_of_segments=5, spacing=1.0)

def bisect_mid_lens_areas():
    bisect_left_lens_area()
    bisect_right_lens_area()

def run():
    selected_object = bpy.context.scene.objects.active #imported glasses
    path = selected_object.data #path data of the glasses

    extrude_curve(path)

    #Since Bend only bends around the Z axis, the glasses have to be rotated. It needs to be rotated in EDIT mode otherwise the Z will be relative to the original mesh.
    rotate_object()

    ##Create extra segments to increase detail for Bend as well as protruding the bridge

    bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS") #move object origin to center of mass

    scale()
    
    move_to_origin(selected_object)

    #the bisects help with future transforms and prevent distortions due to long faces
    bisect_bridge_area()
    bisect_mid_lens_areas()
    
    bend_object(selected_object)


run()
print("Success")