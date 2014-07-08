import bpy

def extrude_curve(selected_object):
    """create the basic extrusion from curve"""
    bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN") #move the object to the center
    
    path = selected_object.data #path data of the glasses
    
    path.extrude = 0.003 #extrude path to create mesh
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
    bpy.ops.mesh.select_all()

    lower_range = int(-1 * number_of_segments/2)
    upper_range = int(number_of_segments/2 + 1)
    spread = range(lower_range, upper_range)
    bisection_points = [x * spacing + midpoint for x in spread]

    for x_co in bisection_points:
        bpy.ops.mesh.select_all() #toggle select
        bpy.ops.mesh.select_all() #toggle select
        bpy.ops.mesh.bisect(plane_co=(x_co, 0.0, 0.0), plane_no=(1.0, 0.0, 0.0), threshold=0, xstart=0, xend=10, ystart=0, yend=100)
        
def find_max_x(selected_object):
    """Returns the max x cordinate of all the vertices"""
    mesh = selected_object.data
    max_x_co = max([vertex.co[0] for vertex in mesh.vertices])
    return max_x_co
        
def find_bridge_area(max_x_co):
    """Suppose the bridge area is 16% of the entire length of the frame, only return half of that because it's split across the origin"""
    return 0.14 * max_x_co
    

def bisect_bridge_area(bridge_area):
    """bisect the bridge area into 20 segments"""
    bpy.ops.object.mode_set(mode="EDIT")
    #bpy.ops.mesh.select_all()
    
    segments = 80
    delta = bridge_area / segments
    
    bisect(midpoint=0.0, number_of_segments=segments, spacing=delta)
    
    bpy.ops.object.mode_set(mode="OBJECT") #need to toggle mode to confirm changes

def bend_object(selected_object):
    """apply the bend simple deform modifier"""
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.modifier_add(type="SIMPLE_DEFORM") #add simple deform modifier
    simple_deform_modifier = selected_object.modifiers["SimpleDeform"]
    simple_deform_modifier.deform_method = "BEND"
    simple_deform_modifier.angle = 0.436332 #Bend 25 degrees

    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="SimpleDeform") #apply modifier
    
def scale(value=100.0):
    """scale the object to 100x the size for easier manipulation"""
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.transform.resize(value=(100.0, 100.0, 100.0))

def find_mid_lens_point(max_x_co):
    """assume the middle of the lens is half way between the middle and one of the ends, find that point"""
    
    return max_x_co/2
        

def bisect_mid_lens_areas(mid_lens_point, max_x_co):
    """bisect the area around the middle of each lens to lessen the artifacts of transformations"""
    left_lens_area = -1 * mid_lens_point
    right_lens_area = mid_lens_point
    
    delta = 0.05 * max_x_co #5% of the width of half the frame
    
    for point in [left_lens_area, right_lens_area]:
        bisect(midpoint=point, number_of_segments=7, spacing=delta)
        
def select_mid_bridge_points(selected_object, delta=0.025):
    """Select the points around the middle section of the bridge, select only works if the mode is OBJECT while selecting, and then changed to EDIT for subsequent operations. The delta should be the same value as the spacing in the bisect bridge"""
    
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh = selected_object.data #mesh data of the selected object
    
    region = delta * 3
    
    #iterating through a lot of vertexes :(
    for vertex in mesh.vertices:
        x_co = vertex.co[0]
        if (x_co >= -1 * region) and (x_co <= region):
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
    
    bpy.ops.transform.translate(value=(0.0, -0.4, 0.0), proportional="ENABLED", proportional_edit_falloff="SMOOTH", proportional_size=1.0)
    
def scale_to_lifesize(max_x_co, lifesize):
    """Scale to the correct size for 3D printing. The scale is 1 STL unit = 1 mm"""
    scale = lifesize / (max_x_co * 2) * 100
    
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.transform.resize(value=(scale, scale, scale))

def in_bridge_area(vertex, bridge_area):
    x,y,z = vertex.co
    
    return (x <= bridge_area/2) and (x >= -1 * bridge_area/2)

def in_left_nosepad_area(vertex, bridge_area):
    x,y,z = vertex.co
    
    return (x<= -1 * bridge_area/2) and (x >= -1 * bridge_area * 3/2)

def in_right_nosepad_area(vertex, bridge_area):
    x,y,z = vertex.co
    
    return (x<= bridge_area * 3/2) and (x >= bridge_area/2)

def in_nosepad_bridge_region(vertex, bridge_area):
    x,y,z = vertex.co
    
    return (x<= 2*bridge_area) and (x >= -2 * bridge_area)

def find_key_values(selected_object, bridge_area):
    mesh = selected_object.data
    
    bottom_of_bridge = 100
    
    front_points = {}
    
    bottom_of_nosepad_area = 100
    
    left_nosepad_points = []
    right_nosepad_points = []
    
    #left nosepad --- bridge area --- right nosepad
    #suppose each nosepad area is the same as bridge area
    
    for vertex in mesh.vertices:
        if in_nosepad_bridge_region(vertex, bridge_area):
            if in_bridge_area(vertex, bridge_area):
                height = vertex.co[2]
                if height < bottom_of_bridge:
                    bottom_of_bridge = height
            
            if in_left_nosepad_area(vertex, bridge_area):
                left_nosepad_points.append(vertex.index)
                height = vertex.co[2]
                if height < bottom_of_nosepad_area:
                    bottom_of_nosepad_area = height
            
            if in_right_nosepad_area(vertex, bridge_area):
                right_nosepad_points.append(vertex.index)
                height = vertex.co[2]
                if height < bottom_of_nosepad_area:
                    bottom_of_nosepad_area = height
            
        y_depth = vertex.co[1]
        if y_depth <= 0: #future manipulations could affect a wider area than the region
            x, y, z = vertex.co #extracted for immutability
            front_points[vertex.index] = (x,y,z)
        
    return bottom_of_bridge, bottom_of_nosepad_area, [front_points], [left_nosepad_points, right_nosepad_points]

def find_nosepad_peak_height(bottom_of_bridge, bottom_of_nosepad):
    
    distance = bottom_of_bridge - bottom_of_nosepad
    
    peak = bottom_of_bridge - 0.5 * distance
    delta = 0.15 * distance
    
    return peak + delta, peak - delta

def select_nosepad_extrusion_points(upper_nosepad_peak, bottom_nosepad_peak, selected_object, nosepad_points):
    mesh = selected_object.data
    
    bpy.ops.object.mode_set(mode="OBJECT")
    
    for index in nosepad_points:
        vertex = mesh.vertices[index]
        height = vertex.co[2]
        
        if (height <= upper_nosepad_peak) and (height >= bottom_nosepad_peak):
            vertex.select = True
                
def extrude_nosepad():
    bpy.ops.object.mode_set(mode="EDIT")
    
    bpy.ops.transform.translate(value=(0.0, 1.0, 0.25), proportional="ENABLED", proportional_edit_falloff="SMOOTH", proportional_size=2.5)
    
def scale_nosepad():
    bpy.ops.object.mode_set(mode="EDIT")
    
    bpy.ops.transform.shrink_fatten(value=0.2, proportional="ENABLED", proportional_edit_falloff="SMOOTH", proportional_size=1.0)

def reset_norm(point_sets, selected_object):
    mesh = selected_object.data
    bpy.ops.object.mode_set(mode="OBJECT")
    
    for point_set in point_sets:
        for index, coord in point_set.items():
            mesh.vertices[index].co = coord

def remove_duplicate_vertexes(selected_object):
    bpy.ops.object.mode_set(mode="EDIT")
    
    bpy.ops.mesh.select_all()
    bpy.ops.mesh.remove_doubles(use_unselected=True)
    bpy.ops.object.mode_set(mode="OBJECT") #need to switch modes for the remove doubles to apply
    
def select_all_nosepad_points(nosepad_points, upper_bound, selected_object):
    bpy.ops.object.mode_set(mode="OBJECT")
    
    mesh = selected_object.data
    
    for index in nosepad_points:
        vertex = mesh.vertices[index]
        
        height = vertex.co[2]
        
        if height < upper_bound:
            vertex.select = True

def run(lifesize=120, protruded_bridge=True):
    selected_object = bpy.context.scene.objects.active #imported glasses
    
    extrude_curve(selected_object)
    
    #fancy display to better visualize the changes
    bpy.ops.object.mode_set(mode="OBJECT")
    selected_object.data.materials[0].diffuse_color = (1.0, 1.0, 1.0)

    #Since Bend only bends around the Z axis, the glasses have to be rotated. It needs to be rotated in EDIT mode otherwise the Z will be relative to the original mesh.
    rotate_object()

    ##Create extra segments to increase detail for Bend as well as protruding the bridge

    bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS") #move object origin to center of mass

    scale()
    
    move_to_origin(selected_object)
    
    #remove duplicate vertexes (like artifacts from converting paths to mesh and beveling)
    #this will weld the seams
    deselect_all(selected_object)
    remove_duplicate_vertexes(selected_object)
    
    max_x_co = find_max_x(selected_object)
    
    bridge_area = find_bridge_area(max_x_co)
    
    #the bisects help with future transforms and prevent distortions due to long faces
    #bisect_bridge_area(bridge_area)
    
    #deselect_all(selected_object)
    #remove_duplicate_vertexes(selected_object)
    
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.bisect(plane_co=(0.0, 0.0, 0.0), plane_no=(1.0, 0.0, 0.0), threshold=0, xstart=0, xend=10, ystart=0, yend=100)
    bpy.ops.object.mode_set(mode="OBJECT")
    
    #add nosepieces
    deselect_all(selected_object)
    bottom_of_bridge, bottom_of_nosepad, normal_points, nosepad_points = find_key_values(selected_object, bridge_area)
    
    left_nosepad_points, right_nosepad_points = nosepad_points
    upper_nosepad_peak, lower_nosepad_peak = find_nosepad_peak_height(bottom_of_bridge, bottom_of_nosepad) 
    
    #left nosepad
    deselect_all(selected_object)
    select_all_nosepad_points(left_nosepad_points, bottom_of_bridge, selected_object)
    scale_nosepad()
    deselect_all(selected_object)
    select_nosepad_extrusion_points(upper_nosepad_peak, lower_nosepad_peak, selected_object, left_nosepad_points)
    extrude_nosepad()
    deselect_all(selected_object)
    
    #right nosepad
    deselect_all(selected_object)
    select_all_nosepad_points(right_nosepad_points, bottom_of_bridge, selected_object)
    scale_nosepad()
    deselect_all(selected_object)
    select_nosepad_extrusion_points(upper_nosepad_peak, lower_nosepad_peak, selected_object, right_nosepad_points)
    extrude_nosepad()
    
    
    deselect_all(selected_object)
    reset_norm(normal_points, selected_object)
    
    bisect_bridge_area(bridge_area)
    
    mid_lens_point = find_mid_lens_point(max_x_co)
    bisect_mid_lens_areas(mid_lens_point, max_x_co)
        
    bend_object(selected_object)
        
    if protruded_bridge:
        #protrude the upper bridge region
        deselect_all(selected_object)
        select_mid_bridge_points(selected_object)
        protrude_bridge()
        
    deselect_all(selected_object)
    scale_to_lifesize(max_x_co, lifesize)
    
    bpy.ops.object.mode_set(mode="OBJECT")
    

run()
print("Success")