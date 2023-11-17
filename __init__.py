bl_info = {
    "name": "LightLinkingPanel",
    "author": "AIGODLIKE社区,Atticus",
    "blender": (4, 0, 0),
    "version": (0, 1),
    "category": "AIGODLIKE",
    "support": "COMMUNITY",
    "doc_url": "",
    "tracker_url": "",
    "description": "",
    "location": "3D视图右侧控件栏",
}

__ADDON_NAME__ = __name__

from . import panel, props, ops


def register():
    props.register()
    ops.register()
    panel.register()


def unregister():
    panel.unregister()
    props.unregister()
    ops.unregister()


if __name__ == '__main__':
    register()
