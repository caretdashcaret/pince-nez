"""
A simple script to procedurally generate 3D printable eyeglasses frames from an SVG.

The order of operations is in the run method.
In addition to the arguments, run expects a SVG to be loaded and selected in Blender.
"""
import bpy


def deselect_all_vertices():
    """certain operations will leave vertices selected which will interfere with subsequent operations.
    This will try to deselect everything."""
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")


def extrude_curve(path, bevel, make_thin):
    """create the basic extrusion from curve"""
    bpy.ops.object.mode_set(mode="OBJECT")
    #move the object to the center
    bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN")

    #extrude path to create mesh
    path.extrude = 0.003
    #bevel the edges
    if bevel:
        path.bevel_depth = 0.002
        path.bevel_resolution = 2
        #path offset will create a thinner frame since beveling thickens it
        #however, may create artifacts if the SVG is too thin
        if make_thin:
            path.offset = -0.001
    
    #convert from curve to mesh
    bpy.ops.object.convert(target='MESH', keep_original=False)


def rotate_object():
    """Rotate the object 90 degrees on the X axis."""
    deselect_all_vertices()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    #Blender uses radians internally instead of degrees
    rotation_value = 1.570797
    bpy.ops.transform.rotate(value=rotation_value, constraint_axis=(False, True, True))


def move_to_origin(selected_object):
    """move the selected object to origin"""
    bpy.ops.object.mode_set(mode="OBJECT")
    
    selected_object.location = (0.0, 0.0, 0.0)
  
    
def bisect(midpoint, number_of_segments, spacing):
    """bisect area around an midpoint, based on the number of segments and spacing"""
    bpy.ops.object.mode_set(mode="EDIT")

    lower_range = int(-1 * number_of_segments/2)
    upper_range = int(number_of_segments/2 + 1)
    spread = range(lower_range, upper_range)
    bisection_points = [x * spacing + midpoint for x in spread]

    for x_coord in bisection_points:
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.bisect(plane_co=(x_coord, 0.0, 0.0),
                            plane_no=(1.0, 0.0, 0.0),
                            threshold=0,
                            xstart=0,
                            xend=10,
                            ystart=0,
                            yend=100)


def find_half_length(mesh):
    """returns the length of half of the frame, assumed to be the max x coordinate,
    since mesh is centered at the global origin"""
    half_length = max([vertex.co[0] for vertex in mesh.vertices])
    return half_length


def find_bridge_area(half_length):
    """suppose the bridge area is 16% of the entire length of the frame,
    only return half of that because it's split across the origin"""
    return 0.16 * half_length
    

def bisect_bridge_area(bridge_area):
    """bisect the bridge area into segments"""
    deselect_all_vertices()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    
    segments = 80
    delta = bridge_area / segments
    
    bisect(midpoint=0.0, number_of_segments=segments, spacing=delta)

    #the operation actually requires a mode change to take effect
    bpy.ops.object.mode_set(mode="OBJECT")


def bend_object(selected_object):
    """apply the bend simple deform modifier"""
    bpy.ops.object.mode_set(mode="OBJECT")

    #add simple deform modifier
    bpy.ops.object.modifier_add(type="SIMPLE_DEFORM")
    simple_deform_modifier = selected_object.modifiers["SimpleDeform"]
    simple_deform_modifier.deform_method = "BEND"

    #Bend 25 degrees, or 0.436332 radians
    simple_deform_modifier.angle = 0.436332

    #Apply modifier
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="SimpleDeform")


def scale_for_manipulation(value=100.0):
    """scale the object to 100x"""
    deselect_all_vertices()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    bpy.ops.transform.resize(value=(100.0, 100.0, 100.0))


def find_mid_lens_coord(half_length):
    """assume the middle of the lens is half way between the middle and one of the ends,
    return that point"""
    return half_length/2
        

def bisect_mid_lens_areas(mid_lens_point, max_x_co):
    """bisect the area around the middle of each lens"""
    left_lens_area = -1 * mid_lens_point
    right_lens_area = mid_lens_point

    #5% of the width of half the frame
    delta = 0.05 * max_x_co
    
    for point in [left_lens_area, right_lens_area]:
        bisect(midpoint=point, number_of_segments=7, spacing=delta)


def select_mid_bridge_points(mesh, delta=0.025):
    """select the vertices around the middle section of the bridge.
    The delta should be the same value as the spacing in the bisect_bridge"""
    deselect_all_vertices()
    bpy.ops.object.mode_set(mode="OBJECT")
    
    region = delta * 3

    for vertex in mesh.vertices:
        x_co = vertex.co[0]
        if (x_co >= -1 * region) and (x_co <= region):
            vertex.select = True


def protrude_bridge():
    """translate the middle section of the bridge, with propotional selection"""
    bpy.ops.object.mode_set(mode="EDIT")
    
    bpy.ops.transform.translate(value=(0.0, -0.4, 0.0), proportional="ENABLED", proportional_edit_falloff="SMOOTH", proportional_size=1.0)


def scale_to_lifesize(half_length, lifesize):
    """scale to the correct size for 3D printing"""
    deselect_all_vertices()
    
    scale = lifesize / (half_length * 2) * 100
    
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.transform.resize(value=(scale, scale, scale))


def in_bridge_area(vertex, bridge_area):
    x,y,z = vertex.co
    
    return (x <= bridge_area/2) and (x >= -1 * bridge_area/2)


def in_right_nosepad_area(vertex, bridge_area):
    x,y,z = vertex.co
    
    return (x<= -1 * bridge_area/2) and (x >= -1 * bridge_area * 3/2)


def in_left_nosepad_area(vertex, bridge_area):
    x,y,z = vertex.co
    
    return (x<= bridge_area * 3/2) and (x >= bridge_area/2)


def in_nosepad_bridge_region(vertex, bridge_area):
    x,y,z = vertex.co
    
    return (x<= 2*bridge_area) and (x >= -2 * bridge_area)


def find_nosepads_values(mesh, bridge_area):
    """
    left nosepad --- bridge area --- right nosepad
    suppose each nosepad area is the same width as the bridge area

    the bottom_of_bridge and bottom_of_nosepad are used to calculate how high (z) is the peak from the bottom
    right_nosepad_vertices and left_nosepad_vertices are vertices in the region of the left and right nosepads

    front_vertices are vertices that may be changed by the transformations that create the nosepads
    and have to be reverted. I think it's easier to revert the changes, than computing a gaussian for figuring out
    how much to extrude the nosepad around its peak
    """
    
    bottom_of_bridge = 100
    bottom_of_nosepad = 100
    
    right_nosepad_vertices = []
    left_nosepad_vertices = []

    front_vertices = {}
    
    for vertex in mesh.vertices:
        if in_nosepad_bridge_region(vertex, bridge_area):
            if in_bridge_area(vertex, bridge_area):
                height = vertex.co[2]
                if height < bottom_of_bridge:
                    bottom_of_bridge = height
            
            if in_right_nosepad_area(vertex, bridge_area):
                #need to store index otherwise can't perform vertex selections due to
                #loss of reference-of-objects?
                right_nosepad_vertices.append(vertex.index)
                #assume the frame is symmetrical, so only need to get the value from one side
                height = vertex.co[2]
                if height < bottom_of_nosepad:
                    bottom_of_nosepad = height
            
            if in_left_nosepad_area(vertex, bridge_area):
                left_nosepad_vertices.append(vertex.index)
            
        y_depth = vertex.co[1]
         #future manipulations could affect a wider area than the region
        if y_depth <= 0:
            #extracted for immutability
            x, y, z = vertex.co
            front_vertices[vertex.index] = (x,y,z)
        
    return [bottom_of_bridge, bottom_of_nosepad], front_vertices, [right_nosepad_vertices, left_nosepad_vertices]


def find_nosepad_peak_height(nosepad_z_height_range):
    """find the height (z) of the set of vertices to select for where the peak of the nosepad is"""

    bottom_of_bridge, bottom_of_nosepad = nosepad_z_height_range
    
    distance = bottom_of_bridge - bottom_of_nosepad
    
    peak = bottom_of_bridge - 0.4 * distance
    delta = 0.05 * distance
    
    return peak + delta, peak - delta


def select_nosepad_peak_vertices(nosepad_peak_z_height_range, nosepad_vertex_indices, mesh):
    """select the vertices that will become the peak for the nosepad"""
    deselect_all_vertices()
    bpy.ops.object.mode_set(mode="OBJECT")

    upper_nosepad_peak, bottom_nosepad_peak = nosepad_peak_z_height_range

    for index in nosepad_vertex_indices:
        vertex = mesh.vertices[index]
        height = vertex.co[2]
        
        if (height <= upper_nosepad_peak) and (height >= bottom_nosepad_peak):
            vertex.select = True


def extrude_nosepad_peak():
    """translate the nosepad along the y-axis"""
    bpy.ops.object.mode_set(mode="EDIT")
    
    bpy.ops.transform.translate(value=(0.0, 1.0, 0.25), proportional="ENABLED", proportional_edit_falloff="SMOOTH", proportional_size=2.5)


def shrink_nosepad():
    """make the nosepad thinner than the frame part"""
    bpy.ops.object.mode_set(mode="EDIT")
    
    bpy.ops.transform.shrink_fatten(value=0.2, proportional="ENABLED", proportional_edit_falloff="SMOOTH", proportional_size=1.0)


def reset_normal_vertices(normal_vertices, mesh):
    """set the location of vertices to specified positions"""
    bpy.ops.object.mode_set(mode="OBJECT")
    
    for index, coord in normal_vertices.items():
        mesh.vertices[index].co = coord


def remove_duplicate_vertices():
    """remove duplicate vertices by welding them together"""
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    bpy.ops.mesh.remove_doubles(use_unselected=True)
    #need to switch modes for the remove doubles to apply
    bpy.ops.object.mode_set(mode="OBJECT")


def select_all_nosepad_vertices(nosepad_vertex_indices, nosepad_z_height_range, mesh):
    """select all the points in the nosepad region less than the max nosepad_z_height"""
    deselect_all_vertices()
    bpy.ops.object.mode_set(mode="OBJECT")

    upper_bound = nosepad_z_height_range[0]

    for index in nosepad_vertex_indices:
        vertex = mesh.vertices[index]
        height = vertex.co[2]
        
        if height < upper_bound:
            vertex.select = True


def bisect_origin():
    """splits down the origin"""
    deselect_all_vertices()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    bpy.ops.mesh.bisect(plane_co=(0.0, 0.0, 0.0), plane_no=(1.0, 0.0, 0.0), threshold=0, xstart=0, xend=10, ystart=0, yend=100)


def move_object_origin_to_center_of_mass():
    """
    move object origin to center of mass
    """
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS")


def run(lifesize=120, protruded_bridge=True, bevel=True, make_thin=True):
    """
    lifesize is the width of the frame, where 1 STL unit = 1 mm
    protruded_bridge is a toggle for where the bridge should be protruded
    """

    #imported SVG of eyeglasses frame
    selected_object = bpy.context.scene.objects.active
    #path data associated with the SVG
    path = selected_object.data

    #create a 3D mesh from the 2D path
    extrude_curve(path, bevel, make_thin)
    #after the 2D to 3D conversion, the data will be mesh data
    mesh = selected_object.data
    
    #fancy display to better visualize the changes
    selected_object.data.materials[0].diffuse_color = (1.0, 1.0, 1.0)

    #since Bend only bends around the Z axis, the frame have to be rotated.
    rotate_object()

    #for some reason there's a translation that happens that offsets the object origin
    move_object_origin_to_center_of_mass()

    #scale the frame for easier manipulation
    scale_for_manipulation()

    #move to global origin so that it's easy to know where the center is
    move_to_origin(selected_object)
    
    #removes duplicate vertexes (like artifacts from converting paths to mesh and beveling)
    #which also welds the seams
    remove_duplicate_vertices()
    
    half_length = find_half_length(mesh)
    
    bridge_area = find_bridge_area(half_length)

    #bisect middle to lessen artifacts from creating nosepads
    #the bisect_bridge_area method isn't called here, because that increases artifacts when scaling the nosepads
    #it's a delicate balance
    bisect_origin()
    
    #calculate information necessary for nosepads
    nosepad_z_height_range, normal_vertices, nosepad_vertices = find_nosepads_values(mesh, bridge_area)
    
    right_nosepad_vertex_indices, left_nosepad_vertex_indices = nosepad_vertices
    nosepad_peak_z_height_range = find_nosepad_peak_height(nosepad_z_height_range)
    
    #create left nosepad
    select_all_nosepad_vertices(right_nosepad_vertex_indices, nosepad_z_height_range, mesh)
    shrink_nosepad()
    select_nosepad_peak_vertices(nosepad_peak_z_height_range, right_nosepad_vertex_indices, mesh)
    extrude_nosepad_peak()
    
    #create right nosepad
    select_all_nosepad_vertices(left_nosepad_vertex_indices, nosepad_z_height_range, mesh)
    shrink_nosepad()
    select_nosepad_peak_vertices(nosepad_peak_z_height_range, left_nosepad_vertex_indices, mesh)
    extrude_nosepad_peak()

    #reset all undesired manipulations from proportional editing
    reset_normal_vertices(normal_vertices, mesh)

    #bisect the bridge area to reduce artifacts from bending as well as protrusion
    bisect_bridge_area(bridge_area)

    #bisect the area around each lens to lessen the artifacts from bending
    mid_lens_coord = find_mid_lens_coord(half_length)
    bisect_mid_lens_areas(mid_lens_coord, half_length)

    #bend the frame slightly
    bend_object(selected_object)
        
    if protruded_bridge:
        #protrude the upper bridge region
        select_mid_bridge_points(mesh)
        protrude_bridge()

    scale_to_lifesize(half_length, lifesize)

    #remove artifacts / cleanup
    remove_duplicate_vertices()
    
    #end in object mode for better viewing
    bpy.ops.object.mode_set(mode="OBJECT")

    print("O-O success!")
    
run()