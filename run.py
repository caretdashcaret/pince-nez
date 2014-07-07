import bpy

def extrude_curve(selected_object):
    """create the basic extrusion from curve"""
    bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN") #move the object to the center
    
    path = selected_object.data #path data of the glasses
    
    path.extrude = 0.005 #extrude path to create mesh
    #path.bevel_depth = 0.001 #bevel the edges

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
    
    selected_object.location = (0.0, 0.0, 0.0)
    
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
    simple_deform_modifier.angle = 0.436332 #Bend 25 degrees

    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="SimpleDeform") #apply modifier
    
def scale(value=100.0):
    """scale the object to 100x the size"""
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.transform.resize(value=(100.0, 100.0, 100.0)) #scale 100x for easier translations

def bisect_mid_lens_areas():
    """bisect the area around the middle of each lens to lessen the artifacts of transformations"""
    left_lens_area = -8.0
    right_lens_area = 8.0
    
    for point in [left_lens_area, right_lens_area]:
        bisect(midpoint=point, number_of_segments=5, spacing=1.0)
        
def select_mid_bridge_points(selected_object, delta=0.0025):
    """select the points around the middle section of the bridge, select only works if the mode is OBJECT while selecting, and then changed to EDIT for subsequent operations"""
    
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh = selected_object.data #mesh data of the selected object
    
    #iterating through a lot of vertexes :(
    for vertex in mesh.vertices:
        x_co = vertex.co[0]
        if (x_co >= -1 * delta) and (x_co <= delta):
            vertex.select = True
            
def deselect_all(selected_object):
    """Certain operations will leave vertices selected which will interfere with subsequent operations. This will try to deselect everything."""
    bpy.ops.object.mode_set(mode="EDIT")
    mesh = selected_object.data
    if mesh.total_vert_sel > 0:
        bpy.ops.mesh.select_all()
    
def protrude_bridge():
    """translate the middle section of the bridge, with propotional selection"""
    bpy.ops.object.mode_set(mode="EDIT")
    
    bpy.ops.transform.translate(value=(0.0, -0.4, 0.0), proportional="ENABLED", proportional_edit_falloff="SMOOTH", proportional_size=0.7)
    

def run():
    selected_object = bpy.context.scene.objects.active #imported glasses

    extrude_curve(selected_object)

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
    
    #protrude the upper bridge region
    deselect_all(selected_object)
    select_mid_bridge_points(selected_object)
    protrude_bridge()

run()
print("Success")
