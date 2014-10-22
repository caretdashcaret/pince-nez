"""
A simple script to procedurally generate 3D printable eyeglasses frames from an SVG.

The order of operations is listed in the create_eyeglasses_from_svg method.
In addition to the arguments, the script expects a SVG to be loaded and selected in Blender.
"""
import bpy
import bmesh


def deselect_all_vertices():
    """certain operations will leave vertices selected which will interfere with subsequent operations.
    This will try to deselect everything."""
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")


def extrude_curve(selected_object, extrude_amount):
    """create the basic extrusion from curve"""

    #path data associated with the SVG
    path = selected_object.data

    #default extrusion is in meters so will need to be converted
    extrude_amount_in_mm = extrude_amount / 1000

    #extrude path to create mesh
    path.extrude = extrude_amount_in_mm

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


def bend_object(selected_object, bend_degree):
    """apply the bend simple deform modifier"""
    bpy.ops.object.mode_set(mode="OBJECT")

    #add simple deform modifier
    bpy.ops.object.modifier_add(type="SIMPLE_DEFORM")
    simple_deform_modifier = selected_object.modifiers["SimpleDeform"]
    simple_deform_modifier.deform_method = "BEND"

    simple_deform_modifier.angle = bend_degree

    #Apply modifier
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="SimpleDeform")


def remove_duplicate_vertices():
    """remove duplicate vertices by welding them together"""
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    bpy.ops.mesh.remove_doubles(use_unselected=True)
    #need to switch modes for the remove doubles to apply
    bpy.ops.object.mode_set(mode="OBJECT")


def move_object_origin_to_center_of_mass():
    """
    move object origin to center of mass
    """
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS")


def setup_environment():
    """
    Sets up the scene with 1 Blender unit as 1 mm
    """
    bpy.context.scene.unit_settings.system = 'METRIC'


def create_mesh_from_svg(selected_object, desired_width, extrude_amount):
    """
    Creates a 3D mesh from the imported 2D SVG
    """
    scale_svg_to_lifesize(selected_object, desired_width)

    extrude_curve(selected_object, extrude_amount)

    change_mesh_color_for_better_visualization(selected_object)

    #clean up by wielding the sides together
    remove_duplicate_vertices()


def get_svg_width(selected_svg_object):

    absolute_bounding_box = selected_svg_object.dimensions
    width = absolute_bounding_box[0]
    return width


def compute_scaling_factor(svg_width, desired_width):

    return desired_width / svg_width


def compute_svg_scaling_factor(selected_svg_object, desired_width):

    svg_width = get_svg_width(selected_svg_object)
    scaling_factor = compute_scaling_factor(svg_width, desired_width)
    return scaling_factor


def move_svg_to_origin_for_scaling():
    """
    Moves the SVG Object to origin to prevent non-uniform scaling
    """
    bpy.ops.object.mode_set(mode="OBJECT")
    #move the object to origin
    bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN")


def scale_svg_using_scaling_factor(scaling_factor):

    move_svg_to_origin_for_scaling()

    #scale
    bpy.ops.transform.resize(value=(scaling_factor,scaling_factor, scaling_factor))


def scale_svg_to_lifesize(selected_svg_object, desired_width):
    """
    Scale the svg to desired lifesize width
    """

    scaling_factor = compute_svg_scaling_factor(selected_svg_object, desired_width)

    scale_svg_using_scaling_factor(scaling_factor)


def change_mesh_color_for_better_visualization(selected_object):

    #fancy display to better visualize the changes
    selected_object.data.materials[0].diffuse_color = (1.0, 1.0, 1.0)


def reorient_for_easier_manipulation(selected_object):

    #since Bend only bends around the Z axis, the frame have to be rotated.
    rotate_object()

    #for some reason there's a translation that happens that offsets the object origin
    move_object_origin_to_center_of_mass()

    #move to global origin so that it's easy to know where the center is
    move_to_origin(selected_object)


def form_lens_and_bridge(bridge_width,
                         lens_bend,
                         frame_bend,
                         bridge_slant,
                         bridge_protrusion_amount,
                         nosepad_shrink_amount):

    bridge_object, left_lens_object, right_lens_object = duplicate_object(2)

    form_bridge(bridge_object, bridge_width, bridge_slant, bridge_protrusion_amount)
    bottom_of_bridge = find_min_z_coord_of_object(bridge_object)

    form_left_lens_area(left_lens_object,
                        bridge_width,
                        lens_bend,
                        bridge_slant,
                        bottom_of_bridge,
                        nosepad_shrink_amount)

    form_right_lens_area(right_lens_object,
                         bridge_width,
                         lens_bend,
                         bridge_slant,
                         bottom_of_bridge,
                         nosepad_shrink_amount)

    #leave a little bit gap to lessen the artifacts when merging
    #gap is 4% of the length of the bridge
    gap = 0.04 * bridge_object.dimensions[0]
    align(left_lens_object, right_lens_object, bridge_object, gap)

    partial_frame = combine_left_lens_object_and_bridge(left_lens_object, bridge_object)
    complete_frame = combine_right_lens_object_and_partial_frame(right_lens_object, partial_frame)

    select_object(complete_frame)
    move_object_origin_to_center_of_mass()

    bend_object(complete_frame, frame_bend)



def combine_left_lens_object_and_bridge(left_lens_object, bridge_object):
    return combine_for_frame(left_lens_object, bridge_object, right_two_pieces=False)


def combine_right_lens_object_and_partial_frame(right_lens_object, partial_frame):
    return combine_for_frame(right_lens_object, partial_frame, right_two_pieces=True)


def select_object(object):
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = object
    object.select = True


def duplicate_object(number_of_duplicates):

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode":"TRANSLATION"},
                                  TRANSFORM_OT_translate={"value":(0.0,0.0,0.0)})
    bpy.ops.object.duplicate_move()

    return bpy.context.scene.objects[0], bpy.context.scene.objects[1], bpy.context.scene.objects[2]


def bisect(x_coord, clear_inner=False, clear_outer=False, z_tilt=0.0, z_translation=0.0):
    """bisect at the x coordinate"""
    deselect_all_vertices()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    bpy.ops.mesh.bisect(plane_co=(x_coord, 0.0, z_translation),
                        plane_no=(1.0, 0.0, z_tilt),
                        threshold=0,
                        xstart=0,
                        xend=10,
                        ystart=0,
                        yend=100,
                        clear_inner=clear_inner,
                        clear_outer=clear_outer)


def form_left_lens_area(left_lens_object,
                        bridge_width,
                        bend_degree,
                        bridge_slant,
                        bottom_of_bridge,
                        nosepad_shrink_amount):
    separate_left_lens_area(left_lens_object, bridge_width, bridge_slant)
    create_left_nosepad(left_lens_object, bottom_of_bridge, nosepad_shrink_amount)
    bend_lens_area(left_lens_object, bend_degree)


def form_right_lens_area(right_lens_object,
                         bridge_width,
                         bend_degree,
                         bridge_slant,
                         bottom_of_bridge,
                         nosepad_shrink_amount):
    separate_right_lens_area(right_lens_object, bridge_width, bridge_slant)
    create_right_nosepad(right_lens_object, bottom_of_bridge, nosepad_shrink_amount)
    bend_lens_area(right_lens_object, bend_degree)


def create_left_nosepad(left_lens_object, bottom_of_bridge, nosepad_shrink_amount):
    max_x, min_x = find_left_nosepad_x_coord_range(left_lens_object)

    non_nosepad_vertices_map = cache_non_nosepad_vertices(left_lens_object, max_x, min_x, bottom_of_bridge)

    select_nosepad_peak_vertices(left_lens_object, bottom_of_bridge, max_x, min_x)
    shrink_nosepad(nosepad_shrink_amount)
    extrude_nosepad_peak()

    reset_normal_vertices(left_lens_object, non_nosepad_vertices_map)


def create_right_nosepad(right_lens_object, bottom_of_bridge, nosepad_shrink_amount):
    max_x, min_x = find_right_nosepad_x_coord_range(right_lens_object)

    non_nosepad_vertices_map = cache_non_nosepad_vertices(right_lens_object, max_x, min_x, bottom_of_bridge)

    select_nosepad_peak_vertices(right_lens_object, bottom_of_bridge, max_x, min_x)
    shrink_nosepad(nosepad_shrink_amount)
    extrude_nosepad_peak()

    reset_normal_vertices(right_lens_object, non_nosepad_vertices_map)


def reset_normal_vertices(left_lens_object, non_nosepad_vertices_map):
    """set the location of vertices to specified positions"""
    deselect_all_vertices()

    bpy.ops.object.mode_set(mode="OBJECT")

    for index, coord in non_nosepad_vertices_map.items():
        left_lens_object.data.vertices[index].co = coord


def extrude_nosepad_peak():
    """translate the nosepad along the y-axis"""
    bpy.ops.object.mode_set(mode="EDIT")

    bpy.ops.transform.translate(value=(0.0, 4.0, 2.0),
                                proportional="ENABLED",
                                proportional_edit_falloff="SMOOTH",
                                proportional_size=8.0)


def shrink_nosepad(nosepad_shrink_amount):
    """make the nosepad thinner than the frame"""
    bpy.ops.object.mode_set(mode="EDIT")

    bpy.ops.transform.shrink_fatten(value=nosepad_shrink_amount,
                                    proportional="ENABLED",
                                    proportional_edit_falloff="SMOOTH",
                                    proportional_size=10.0)


def select_nosepad_peak_vertices(lens_object, bottom_of_bridge, max_x, min_x):
    bottom_of_nosepad = find_bottom_of_nosepad_region(lens_object, max_x, min_x)
    max_z, min_z = find_nosepad_peak_vertices_z_range(bottom_of_bridge, bottom_of_nosepad)

    deselect_all_vertices()

    bpy.ops.object.mode_set(mode="OBJECT")
    for vertex in lens_object.data.vertices:
        x,y,z = vertex.co
        if in_range(max_z, min_z, z) and in_range(max_x, min_x, x):
            vertex.select = True


def find_nosepad_peak_vertices_z_range(bottom_of_bridge, bottom_of_nosepad):
    length = bottom_of_bridge - bottom_of_nosepad

    peak = bottom_of_bridge - 0.4 * length
    delta = 0.05 * length

    return peak + delta, peak - delta


def find_bottom_of_nosepad_region(lens_object, max_x, min_x):
    z_coord = [vertex.co[2] for vertex in lens_object.data.vertices if in_range(max_x, min_x, vertex.co[0])]
    return min(z_coord)


def cache_non_nosepad_vertices(lens_object, range_max_x, range_min_x, range_max_z):
    select_object(lens_object)
    non_nosepad_vertices = {}

    faces = lens_object.data.polygons
    vertices = lens_object.data.vertices

    #cache any vertices above the bottom of the bridge in the nosepad region
    for vertex in vertices:
        x,y,z = vertex.co
        if y <= 0:
            non_nosepad_vertices[vertex.index] = [x,y,z]

    return non_nosepad_vertices


def is_front_facing(face):
    x,y,z = face.normal
    return y < 0


def in_range(max_val, min_val, val):
    return (val <= max_val) and (val >= min_val)


def find_left_nosepad_x_coord_range(lens_object):
    return find_nosepad_x_coord_range(lens_object, left_nosepad=True)


def find_right_nosepad_x_coord_range(lens_object):
    return find_nosepad_x_coord_range(lens_object, left_nosepad=False)


def find_nosepad_x_coord_range(lens_object, left_nosepad=True):
    max_x, min_x = find_max_and_min_x_coord_of_object(lens_object)

    width = max_x - min_x
    #nosepad within ~18% of the entire frame
    nosepad_range_width = 0.18 * width

    if left_nosepad:
        min_x = max_x - nosepad_range_width
    else:
        max_x = min_x + nosepad_range_width

    return max_x, min_x


def find_max_and_min_x_coord_of_object(mesh_object):
    select_object(mesh_object)

    x_coords = [vertex.co[0] for vertex in mesh_object.data.vertices]

    return max(x_coords), min(x_coords)


def find_min_z_coord_of_object(mesh_object):
    select_object(mesh_object)

    z_coords = [vertex.co[2] for vertex in mesh_object.data.vertices]

    return min(z_coords)


def form_bridge(bridge_object, bridge_width, bridge_slant, bridge_protrusion_amount):
    cut_bridge(bridge_object, bridge_width, bridge_slant)
    bisect_bridge_for_resolution(bridge_width, bridge_slant)
    extrude_bridge(bridge_object, bridge_width, bridge_protrusion_amount)


def bend_lens_area(lens_object, bend_degree):
    select_object(lens_object)
    move_object_origin_to_center_of_mass()
    increase_resolution_for_bending(lens_object)
    bend_object(lens_object, bend_degree)


def increase_resolution_for_bending(lens_object):
    select_object(lens_object)
    #we bisect here because loopcuts don't work
    bisect_to_increase_edge_loops(center=lens_object.location[0],
                                  width=lens_object.dimensions[0] * 0.75,
                                  number_of_loops=13)


def bisect_to_increase_edge_loops(center, width, number_of_loops):
    bpy.ops.object.mode_set(mode="EDIT")

    lower_range = int(-1 * number_of_loops/2)
    upper_range = int(number_of_loops/2 + 1)
    spread = range(lower_range, upper_range)

    spacing = width / number_of_loops

    bisection_points = [x * spacing + center for x in spread]

    for x_coord in bisection_points:
        bisect(x_coord)


def separate_left_lens_area(left_lens_object, bridge_width, bridge_slant):
    select_object(left_lens_object)
    left_bridge_boundary_from_bridge = -1.0 * bridge_width / 2.0
    bisect(left_bridge_boundary_from_bridge, clear_outer=True, z_tilt=bridge_slant)


def separate_right_lens_area(right_lens_object, bridge_width, bridge_slant):
    select_object(right_lens_object)
    right_bridge_boundary_from_bridge = bridge_width / 2.0
    bisect(right_bridge_boundary_from_bridge, clear_inner=True, z_tilt=-1*bridge_slant)


def cut_bridge(bridge_object, bridge_width, bridge_slant):

    select_object(bridge_object)
    left_bridge_boundary_from_bridge = -1.0 * bridge_width / 2.0
    bisect(left_bridge_boundary_from_bridge, clear_inner=True, z_tilt=bridge_slant)

    right_bridge_boundary_from_bridge = bridge_width / 2.0
    bisect(right_bridge_boundary_from_bridge, clear_outer=True, z_tilt=-1*bridge_slant)


def align_left_lens_area_and_bridge(left_lens_area_object, bridge_object, gap):
    align_lens_area_and_bridge(left_lens_area_object, bridge_object)

    select_object(bridge_object)
    bpy.ops.transform.translate(value=(gap, 0, 0), constraint_axis=(True, False, False))


def select_second_object(object):
    object.select = True


def merge_objects(object_a, object_b):
    select_object(object_b)
    select_second_object(object_a)
    bpy.ops.object.join()
    combined_bridge_object = object_b
    return combined_bridge_object


def bridge_gap_between_lens_area_and_bridge(frame_object, gap_on_the_right_side=True):
    select_non_manifold_vertices()
    deselect_non_manifold_vertices(frame_object, deselect_left_side=gap_on_the_right_side)
    bridge_gap()


def select_non_manifold_vertices():
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()


def deselect_edge_and_associated_vertices(edge, start_vertex, end_vertex):
    start_vertex.select = False
    end_vertex.select = False
    edge.select = False


def get_start_and_end_vertices_from_edge(edge, mesh_object):
    start_vertex_index, end_vertex_index = edge.vertices

    start_vertex = mesh_object.data.vertices[start_vertex_index]
    end_vertex = mesh_object.data.vertices[end_vertex_index]

    return start_vertex, end_vertex


def on_right_side(vertex):
    x_coord = vertex.co[0]
    if x_coord >= 0:
        return True
    return False


def bridge_gap():
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.bridge_edge_loops(use_merge=True)


def combine_for_frame(lens_object, bridge_object, right_two_pieces=True):
    frame_object = merge_objects(lens_object, bridge_object)
    select_object(frame_object)
    bridge_gap_between_lens_area_and_bridge(frame_object, gap_on_the_right_side=right_two_pieces)

    return frame_object


def on_left_side(vertex):
    x_coord = vertex.co[0]
    if x_coord <= 0:
        return True
    return False


def deselect_non_manifold_vertices(mesh_object, deselect_left_side=True):

    side_check = on_right_side
    if deselect_left_side:
        side_check = on_left_side

    bpy.ops.object.mode_set(mode='EDIT')

    mesh = bmesh.from_edit_mesh(mesh_object.data)

    for edge in mesh.edges:
        start_vertex, end_vertex = edge.verts

        if side_check(start_vertex) or side_check(end_vertex):
            deselect_edge_and_associated_vertices(edge, start_vertex, end_vertex)

        else:
            pass

    for vertex in mesh.verts:
        if side_check(vertex):
            vertex.select = False


def align_right_lens_area_and_bridge(right_lens_area_object, bridge_object, gap):
    align_lens_area_and_bridge(right_lens_area_object, bridge_object)

    select_object(right_lens_area_object)
    bpy.ops.transform.translate(value=(gap*2, 0, 0), constraint_axis=(True, False, False))


def align_lens_area_and_bridge(lens_object, bridge_object):
    select_object(bridge_object)
    select_second_object(lens_object)
    bpy.ops.object.align(bb_quality=True, align_mode='OPT_2', relative_to='OPT_1', align_axis={'Y'})


def align(left_lens_object, right_lens_object, bridge_object, gap):
    align_left_lens_area_and_bridge(left_lens_object, bridge_object, gap)
    align_right_lens_area_and_bridge(right_lens_object, bridge_object, gap)


def get_spread_for_bridge(max_val, number_of_segments=20):
    half = (number_of_segments + 2) / 2

    lower_range = int(-1 * half)
    upper_range = int(half + 1)

    spread = range(lower_range, upper_range)
    spread = spread[1:-1]

    val_spread = [1.0 * x / half * max_val for x in spread]
    return val_spread


def bisect_bridge_for_resolution(bridge_width, max_slant):
    z_translation = compute_convergence_point(bridge_width, max_slant)
    slant_spread = get_spread_for_bridge(max_slant)

    for slant in slant_spread:
        bisect(0.0, z_tilt=slant, z_translation=z_translation)


def extrude_bridge(bridge_object, bridge_width, bridge_protrusion_amount):
    select_object(bridge_object)

    deselect_all_vertices()

    select_mid_bridge_points(bridge_object, bridge_width)

    protrude_bridge(bridge_protrusion_amount)


def select_mid_bridge_points(bridge_object, bridge_width):

    bpy.ops.object.mode_set(mode="OBJECT")

    positive_bridge_region = bridge_width/2
    scaled_positive_bridge_region = positive_bridge_region/1000
    max_region = 0.1 * scaled_positive_bridge_region
    min_region = -1.0 * max_region

    for vertex in bridge_object.data.vertices:
        x_coord = vertex.co[0]
        if in_range(max_region, min_region, x_coord):
            vertex.select = True


def protrude_bridge(protrusion_amount):
    """translate the middle section of the bridge, with propotional selection"""
    bpy.ops.object.mode_set(mode="EDIT")

    bpy.ops.transform.translate(value=(0.0, protrusion_amount, 0.0), proportional="ENABLED", proportional_edit_falloff="SMOOTH", proportional_size=5.0)



def compute_convergence_point(bridge_width, max_slant):
    # equation of plane given
    # the normal is (1, 0, max_slant) and
    # a point on the plane is (-1.0 * bridge_width/2, 0, 0)
    #find z when x is 0

    return (bridge_width / 2.0) / (-1.0 * max_slant)


def create_eyeglasses_from_svg(desired_width=135,
                               desired_thickness=4.5,
                               bridge_width=10,
                               lens_bend=0.2618,
                               frame_bend=0.3491,
                               bridge_slant=0.3,
                               bridge_protrusion_amount=-0.8,
                               nosepad_shrink_amount=0.003):
    """
    Scale is in mm
    :param desired_width: the width of the frame prior to curving the lens area
    :param desired_thickness: thickness of the frame
    :param bridge_width: width of the bridge
    :param bend_degree: the bend of lens areas in radians
    :param frame_bend: the bend of the entire frame in radians
    :param bridge_slant: the z tilt of how the bridge is slanted between the bridge and the lens area (must be >0)
    :param bridge_protrusion_amount: amount to protrude the bridge
    :param nosepad_shrink_amount: amount to shrink the nosepads so that they're thin pieces
    """

    setup_environment()

    selected_object = bpy.context.scene.objects.active

    create_mesh_from_svg(selected_object, desired_width, desired_thickness)

    reorient_for_easier_manipulation(selected_object)

    form_lens_and_bridge(bridge_width,
                         lens_bend,
                         frame_bend,
                         bridge_slant,
                         bridge_protrusion_amount,
                         nosepad_shrink_amount)


create_eyeglasses_from_svg()
