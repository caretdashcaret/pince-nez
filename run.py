import bpy

selected_object = bpy.context.scene.objects.active #imported glasses
path = selected_object.data #path data of the glasses

##Create basic glasses extrusion

bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN") #move the object to the center

path.extrude = 0.005 #extrude path to create mesh
#path.bevel_depth = 0.001 #bevel the edges

bpy.ops.object.convert(target='MESH', keep_original=False) #convert from curve to mesh

bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS") #move object origin to center of mass

##Bend

#Since Bend only bends around the Z axis, the glasses have to be rotated. It needs to be rotated in EDIT mode otherwise the Z will be relative to the original mesh.

#Blender uses radians internally

bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all()
bpy.ops.transform.rotate(value=1.570797, constraint_axis=(False, True, True)) #rotate 90 degrees only on the X
bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.object.modifier_add(type="SIMPLE_DEFORM") #add simple deform modifier
simple_deform_modifier = selected_object.modifiers["SimpleDeform"]
simple_deform_modifier.deform_method = "BEND"
simple_deform_modifier.angle = 0.523599 #Bend 30 degrees

bpy.ops.object.modifier_apply(apply_as="DATA", modifier="SimpleDeform") #apply modifier

##Scale
bpy.ops.transform.resize(value=(100.0, 100.0, 100.0)) #scale 100x for easier translations

##Translate the bridge

current_location = selected_object.location
translation_vector = (-1*current_location[0], -1*current_location[1], -1*current_location[2]) #move to global origin
bpy.ops.transform.translate(value=translation_vector)

#Create 
bpy.ops.object.mode_set(mode="EDIT")

midpoint = 0.0 #midpoint of the glasses, to estimate the bridge
bisection_points = [x * 0.025 + midpoint for x in range(-10,11)]

for x_co in bisection_points:
    bpy.ops.mesh.select_all() #toggle select
    bpy.ops.mesh.select_all() #toggle select
    bpy.ops.mesh.bisect(plane_co=(x_co, 0.0, 0.0), plane_no=(1.0, 0.0, 0.0), threshold=0, xstart=0, xend=10, ystart=0, yend=100)

print("Success")