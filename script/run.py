"""
A simple script to procedurally generate 3D printable eyeglasses frames from an SVG.

The order of operations is in the run method.
In addition to the arguments, run expects a SVG to be loaded and selected in Blender.
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

    mesh = selected_object.data

    change_mesh_color_for_better_visualization(selected_object)

    #clean up by wielding the sides together
    remove_duplicate_vertices()

    return mesh


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


def form_lens_and_bridge(bridge_width, bend_degree):

    bridge_object, left_lens_object, right_lens_object = duplicate_object(2)
    form_left_lens_area(left_lens_object, bridge_width, bend_degree)
    form_right_lens_area(right_lens_object, bridge_width, bend_degree)
    form_bridge(bridge_object, bridge_width)

    #leave a little bit gap to lessen the artifacts when merging
    #gap is 4% of the length of the bridge
    gap = 0.04 * bridge_object.dimensions[0]
    align(left_lens_object, right_lens_object, bridge_object, gap)

    partial_frame = combine_for_frame(left_lens_object, bridge_object, right_two_pieces=False)
    complete_frame = combine_for_frame(right_lens_object, partial_frame, right_two_pieces=True)

    select_object(complete_frame)
    move_object_origin_to_center_of_mass()

    return complete_frame


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


def bisect(x_coord, clear_inner=False, clear_outer=False, z_tilt=0.0):
    """bisect at the x coordinate"""
    deselect_all_vertices()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    bpy.ops.mesh.bisect(plane_co=(x_coord, 0.0, 0.0),
                        plane_no=(1.0, 0.0, z_tilt),
                        threshold=0,
                        xstart=0,
                        xend=10,
                        ystart=0,
                        yend=100,
                        clear_inner=clear_inner,
                        clear_outer=clear_outer)


def form_left_lens_area(left_lens_object, bridge_width, bend_degree):
    separate_left_lens_area(left_lens_object, bridge_width)
    bend_lens_area(left_lens_object, bend_degree)


def form_right_lens_area(right_lens_object, bridge_width, bend_degree):
    separate_right_lens_area(right_lens_object, bridge_width)
    bend_lens_area(right_lens_object, bend_degree)


def form_bridge(bridge_object, bridge_width):
    cut_bridge(bridge_object, bridge_width)
    #bisect origin to reduce artifacts
    bisect(0.0)


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


def separate_left_lens_area(left_lens_object, bridge_width):
    select_object(left_lens_object)
    left_bridge_boundary_from_bridge = -1.0 * bridge_width / 2.0
    bisect(left_bridge_boundary_from_bridge, clear_outer=True, z_tilt=0.3)


def separate_right_lens_area(right_lens_object, bridge_width):
    select_object(right_lens_object)
    right_bridge_boundary_from_bridge = bridge_width / 2.0
    bisect(right_bridge_boundary_from_bridge, clear_inner=True, z_tilt=-0.3)


def cut_bridge(bridge_object, bridge_width):

    select_object(bridge_object)
    left_bridge_boundary_from_bridge = -1.0 * bridge_width / 2.0
    bisect(left_bridge_boundary_from_bridge, clear_inner=True, z_tilt=0.3)

    right_bridge_boundary_from_bridge = bridge_width / 2.0
    bisect(right_bridge_boundary_from_bridge, clear_outer=True, z_tilt=-0.3)


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
    bpy.ops.mesh.bridge_edge_loops(use_merge=True, number_cuts=3, smoothness=3)


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
    bpy.ops.object.align(bb_quality=True, align_mode='OPT_3', relative_to='OPT_1', align_axis={'Y'})


def align(left_lens_object, right_lens_object, bridge_object, gap):
    align_left_lens_area_and_bridge(left_lens_object, bridge_object, gap)
    align_right_lens_area_and_bridge(right_lens_object, bridge_object, gap)


def create_eyeglasses_from_svg(desired_width=135, desired_thickness=4.5, bridge_width=10, bend_degree=0.2618):
    """
    Scale is in mm
    :param desired_width: the width of the frame prior to curving the lens area
    :param desired_thickness: thickness of the frame
    :param bridge_width: width of the bridge
    :param bend_degree: the degree of the bend in radians
    """

    setup_environment()

    selected_object = bpy.context.scene.objects.active

    mesh = create_mesh_from_svg(selected_object, desired_width, desired_thickness)

    reorient_for_easier_manipulation(selected_object)

    frame_object = form_lens_and_bridge(bridge_width, bend_degree)

    #create_nosepads(frame_object)

    #protrude_bridge(frame_object)


create_eyeglasses_from_svg()