import bpy
from bpy.app.translations import pgettext_iface as p_

from .ops import get_lights_from_receiver_obj
from .utils import get_all_light_effect_obj_state, CollectionType, StateValue


def get_light_icon(light):
    data = light.data
    if data.type == 'AREA':
        return 'LIGHT_AREA'
    elif data.type == 'POINT':
        return 'LIGHT_POINT'
    elif data.type == 'SPOT':
        return 'LIGHT_SPOT'
    elif data.type == 'SUN':
        return 'LIGHT_SUN'

    return 'LIGHT'


def draw_light_link(object, layout, use_pin=False):
    if object is None: return

    col = layout.column()
    light_linking = object.light_linking

    row = col.row(align=True)

    row.label(text=object.name, icon='LIGHT')
    if use_pin:
        row.prop(bpy.context.scene, 'light_linking_pin', text='', icon='PINNED')

    # col.prop(light_linking, 'receiver_collection', text='')

    if not light_linking.receiver_collection:
        col.operator('object.light_linking_receiver_collection_new', text='', icon='ADD')
        return

    row = col.row(align=True)
    row.prop(object, 'light_linking_state', expand=True)
    row.prop(bpy.context.scene, 'force_light_linking_state', icon='FILE_REFRESH', toggle=True, text='')

    if not object.show_light_linking_collection: return

    col.separator()

    row = col.row(align=True)
    row.template_light_linking_collection(row, light_linking, "receiver_collection")
    row.operator('object.light_linking_unlink_from_collection', text='', icon='REMOVE')


class LLT_PT_panel(bpy.types.Panel):
    bl_label = "Light Linking"
    bl_idname = "LLT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Light Linking"

    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'CYCLES'

    def draw_light(self, context, layout):
        if context.scene.light_linking_pin:
            obj = context.scene.light_linking_pin_object
            if not obj: return
            draw_light_link(obj, layout, use_pin=True)
        else:
            if not context.object:
                layout.label(text="No object selected")
            elif context.object.type != 'LIGHT':
                layout.label(text="Selected object is not a light")
                layout.operator('object.light_linking_receiver_collection_new', text='As light', icon='ADD')
                return

            draw_light_link(context.object, layout, use_pin=True)

    def draw_object(self, context, layout):
        lights = get_lights_from_receiver_obj(context.object)
        layout.label(text='仅显示排除灯光')
        for (light, state) in lights:
            if state != 'EXCLUDE': continue
            row = layout.row(align=True)
            row.label(text=f"'{light.name}'", icon=get_light_icon(light))
            op = row.operator('llp.remove_light_linking', text='', icon="REMOVE")
            op.obj = context.object.name
            op.light = light.name

    def draw_light_objs_control(self, context, layout):
        if context.scene.light_linking_pin:
            light_obj = context.scene.light_linking_pin_object
        else:
            light_obj = context.object
        if not light_obj: return

        col = layout.column()
        row = col.row(align=True)
        row.label(text=f"{light_obj.name}", icon=get_light_icon(light_obj))
        row.separator()
        row.prop(bpy.context.scene, 'light_linking_pin', text='', icon='PINNED')

        toggle_op_id = 'llp.toggle_light_linking'
        add_op_id = 'llp.add_light_linking'

        obj_state_dict = get_all_light_effect_obj_state(light_obj)

        if len(obj_state_dict) == 0:
            col.label(text='No Effect Object')
            return

        for obj in obj_state_dict.keys():
            label = f"'{obj.name}'"
            row = col.row(align=True)

            row.label(text=label, icon='OBJECT_DATA')

            state_info = obj_state_dict[obj]
            # print(state_info)
            if receive_value := state_info.get(CollectionType.RECEIVER):  # exist in receiver collection
                icon = 'OUTLINER_OB_LIGHT' if receive_value == StateValue.INCLUDE else 'OUTLINER_DATA_LIGHT'
                text = 'Include' if receive_value == StateValue.INCLUDE else 'Exclude'
                op = row.operator(toggle_op_id, text=p_(text), icon=icon)
                op.coll_type = CollectionType.RECEIVER.value
                op.obj = obj.name
                op.light = light_obj.name
            else:
                op = row.operator(add_op_id, text='Add', icon='ADD')
                op.coll_type = CollectionType.RECEIVER.value
                op.obj = obj.name
                op.light = light_obj.name

            if block_value := state_info.get(CollectionType.BLOCKER):  # exist in exclude collection
                icon = 'SHADING_SOLID' if block_value == StateValue.INCLUDE else 'SHADING_RENDERED'
                text = 'Include' if block_value == StateValue.INCLUDE else 'Exclude'
                op = row.operator(toggle_op_id, text=p_(text), icon=icon)
                op.coll_type = CollectionType.BLOCKER.value
                op.obj = obj.name
                op.light = light_obj.name
            else:
                op = row.operator(add_op_id, text='Add', icon='ADD')
                op.coll_type = CollectionType.BLOCKER.value
                op.obj = obj.name
                op.light = light_obj.name

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, 'light_linking_ui', expand=True)

        if context.scene.light_linking_ui == 'LIGHT_EX':
            self.draw_light_objs_control(context, layout)

        elif context.scene.light_linking_ui == 'LIGHT':
            self.draw_light(context, layout)

        elif context.scene.light_linking_ui == 'OBJECT':
            self.draw_object(context, layout)


def update_pin_object(self, context):
    if context.scene.light_linking_pin is True:
        if context.object and context.object.select_get():
            context.scene.light_linking_pin_object = context.object
        else:
            context.scene.light_linking_pin = False
    else:
        context.scene.light_linking_pin_object = None


def register():
    bpy.types.Scene.light_linking_ui = bpy.props.EnumProperty(
        items=[
            ('LIGHT', 'Simple', ''),
            ('LIGHT_EX', 'Advanced', ''),
            # ('OBJECT', 'Object', '')
        ]
    )
    bpy.types.Scene.light_linking_pin_object = bpy.props.PointerProperty(
        poll=lambda self, obj: obj.type in {'LIGHT', 'MESH'}, type=bpy.types.Object,
    )

    bpy.types.Scene.light_linking_pin = bpy.props.BoolProperty(name='Pin', update=update_pin_object)

    bpy.utils.register_class(LLT_PT_panel)


def unregister():
    del bpy.types.Scene.light_linking_ui
    del bpy.types.Scene.light_linking_pin_object
    del bpy.types.Scene.light_linking_pin

    bpy.utils.unregister_class(LLT_PT_panel)
