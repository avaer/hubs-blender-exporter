import re
import bpy
from bpy.types import Panel
from bpy.props import StringProperty
from . import components

class HubsScenePanel(Panel):
    bl_label = 'Hubs'
    bl_idname = "SCENE_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(context.scene.hubs_settings,
                 "config_path", text="Config File")
        row.operator("wm.reload_hubs_config", text="", icon="FILE_REFRESH")

        row = layout.row()
        row.operator("wm.export_hubs_gltf", text="Export Scene")
        row.operator("wm.export_hubs_gltf",
                     text="Export Selected").selected = True

        draw_components_list(self, context)

class HubsObjectPanel(Panel):
    bl_label = "Hubs"
    bl_idname = "OBJECT_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        draw_components_list(self, context)

class HubsMaterialPanel(Panel):
    bl_label = 'Hubs'
    bl_idname = "MATERIAL_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        draw_components_list(self, context)

def draw_components_list(panel, context):
    layout = panel.layout

    obj = components.get_object_source(context, panel.bl_context)

    if obj is None:
        layout.label(text="No object selected")
        return

    hubs_settings = context.scene.hubs_settings

    if hubs_settings.hubs_config is None:
        layout.label(text="No hubs config loaded")
        return

    for component_item in obj.hubs_component_list.items:
        row = layout.row()
        draw_component(panel, context, obj, row, component_item)

    layout.separator()

    add_component_operator = layout.operator(
        "wm.add_hubs_component",
        text="Add Component"
    )
    add_component_operator.object_source = panel.bl_context

def draw_component(panel, context, obj, row, component_item):
    hubs_settings = context.scene.hubs_settings

    component_name = component_item.name
    component_definition = hubs_settings.hubs_config['components'][component_name]
    component_class = hubs_settings.registered_hubs_components[component_name]
    component_class_name = component_class.__name__
    component = getattr(obj, component_class_name)

    col = row.column()
    top_row = col.row()
    top_row.label(text=component_name)

    remove_component_operator = top_row.operator(
        "wm.remove_hubs_component",
        text="",
        icon="X"
    )
    remove_component_operator.component_name = component_name
    remove_component_operator.object_source = panel.bl_context

    content_col = col.column()

    path = panel.bl_context + "." + component_class_name

    draw_type(context, content_col, obj, component, path, component_definition)

def draw_type(context, col, obj, target, path, type_definition):
    for property_name, property_definition in type_definition['properties'].items():
        draw_property(context, col, obj, target, path, property_name, property_definition)

def draw_property(context, col, obj, target, path, property_name, property_definition):
    property_type = property_definition['type']
    hubs_settings = context.scene.hubs_settings
    registered_types = hubs_settings.hubs_config['types']
    is_custom_type = property_type in registered_types

    if property_type == 'collections':
        draw_collections_property(context, col, obj, target, path, property_name, property_definition)
    elif property_type == 'array':
        draw_array_property(context, col, obj, target, path, property_name, property_definition)
    elif is_custom_type:
        draw_type(context, col, obj, target, path, registered_types[property_type])
    else:
        col.prop(data=target, property=property_name)

def draw_collections_property(_context, col, obj, _target, _path, property_name, property_definition):
    collections_row = col.row()
    collections_row.label(text=property_name)

    filtered_collection_names = []
    collection_prefix_regex = None

    if 'collectionPrefix' in property_definition:
        collection_prefix = property_definition['collectionPrefix']
        collection_prefix_regex = re.compile(
            r'^' + collection_prefix)

    for collection in obj.users_collection:
        if collection_prefix_regex and collection_prefix_regex.match(collection.name):
            new_name = collection_prefix_regex.sub(
                "", collection.name)
            filtered_collection_names.append(new_name)
        elif not collection_prefix_regex:
            filtered_collection_names.append(collection.name)

    collections_row.box().label(text=", ".join(filtered_collection_names))

def draw_array_property(context, col, obj, target, path, property_name, property_definition):
    hubs_settings = context.scene.hubs_settings
    registered_types = hubs_settings.hubs_config['types']
    array_type = property_definition['arrayType']
    item_definition = registered_types[array_type]

    array_value = getattr(target, property_name)

    property_path = path + "." + property_name

    if property_name != 'value':
        col.label(text=property_name)

    for i, item in enumerate(array_value):
        box_row = col.box().row()
        box_col = box_row.column()
        item_path = property_path + "." + str(i)

        draw_type(context, box_col, obj, item, item_path, item_definition)

        remove_operator = box_row.column().operator(
            "wm.remove_hubs_component_item",
            text="",
            icon="X"
        )
        remove_operator.path = item_path

    add_operator = col.operator(
        "wm.add_hubs_component_item",
        text="Add Item"
    )
    add_operator.path = property_path

def register():
    bpy.utils.register_class(HubsScenePanel)
    bpy.utils.register_class(HubsObjectPanel)
    bpy.utils.register_class(HubsMaterialPanel)

def unregister():
    bpy.utils.unregister_class(HubsScenePanel)
    bpy.utils.unregister_class(HubsObjectPanel)
    bpy.utils.unregister_class(HubsMaterialPanel)
