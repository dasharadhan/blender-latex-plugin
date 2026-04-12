import bpy


class VSE_PT_latex_panel(bpy.types.Panel):
    bl_label = "LaTeX Editor"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "LaTeX"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Global Settings
        box_global = layout.box()
        box_global.label(text="Global Settings:", icon="WORLD")
        box_global.prop(scene, "latex_asset_dir", text="Asset Directory")

        box_global.separator()
        box_global.label(text="Editor Settings:", icon="PREFERENCES")
        box_global.prop(scene, "latex_editor_behavior", text="Editor Behavior")
        box_global.prop(scene, "latex_editor_scroll_behavior", text="Cursor Behavior")

        layout.separator()

        # Beamer Storyboard
        box_beamer = layout.box()
        box_beamer.label(text="Beamer Storyboard:", icon="TEXT")

        row = box_beamer.row(align=True)
        row.prop(scene, "latex_master_doc", text="Source")

        # If no text block is selected, show the template generator button
        if not scene.latex_master_doc:
            row.operator("sequencer.create_beamer_template", icon="ADD", text="")
        else:
            box_beamer.prop(scene, "beamer_bibtex", text="BibTeX Source")

            box_beamer.separator()
            res_row = box_beamer.row(align=True)
            res_row.prop(scene, "beamer_res_x", text="X")
            res_row.prop(scene, "beamer_res_y", text="Y")

            box_beamer.operator(
                "sequencer.build_beamer_storyboard",
                icon="SEQ_SEQUENCER",
                text="Build Storyboard",
            )

            row_del = box_beamer.row()
            row_del.alert = True
            row_del.operator(
                "sequencer.remove_beamer_storyboard",
                icon="TRASH",
                text="Remove Storyboard",
            )


class SEQUENCER_MT_add_latex(bpy.types.Menu):
    bl_label = "LaTeX"
    bl_idname = "SEQUENCER_MT_add_latex"

    def draw(self, context):
        layout = self.layout

        layout.operator("sequencer.add_latex_slide", text="LaTeX Strip", icon="TEXT")


class SEQUENCER_PT_latex_strip_settings(bpy.types.Panel):
    bl_label = "LaTeX Strip Settings"
    bl_idname = "SEQUENCER_PT_latex_strip_settings"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"

    bl_category = "Strip"

    @classmethod
    def poll(cls, context):
        strip = context.scene.sequence_editor.active_strip
        return strip is not None and getattr(strip, "is_latex_slide", False)

    def draw(self, context):
        layout = self.layout
        strip = context.scene.sequence_editor.active_strip

        layout.prop(strip, "latex_strip_preamble", text="Preamble")
        # layout.prop(strip, "latex_text_datablock", text="Source Text")

        layout.label(text="LaTeX Source:")
        layout.template_ID(
            strip, "latex_text_datablock", new="text.new", open="text.open"
        )

        if strip.latex_text_datablock:
            layout.operator(
                "sequencer.edit_latex_source", icon="TEXT", text="Edit LaTeX Source"
            )

        layout.separator()

        if getattr(strip, "latex_text_datablock", None):
            layout.operator(
                "sequencer.compile_latex_modal",
                icon="FILE_IMAGE",
                text="Compile In-Place",
            )

        row = layout.row()
        row.alert = True
        row.operator(
            "sequencer.delete_latex_slide", icon="TRASH", text="Delete Strip & Files"
        )


def menu_func_add_latex(self, context):
    self.layout.menu(SEQUENCER_MT_add_latex.bl_idname, icon="TEXT")


def register():
    bpy.utils.register_class(VSE_PT_latex_panel)

    bpy.utils.register_class(SEQUENCER_MT_add_latex)
    bpy.utils.register_class(SEQUENCER_PT_latex_strip_settings)

    bpy.types.SEQUENCER_MT_add.append(menu_func_add_latex)


def unregister():
    bpy.utils.unregister_class(VSE_PT_latex_panel)

    bpy.types.SEQUENCER_MT_add.remove(menu_func_add_latex)

    bpy.utils.unregister_class(SEQUENCER_MT_add_latex)
    bpy.utils.unregister_class(SEQUENCER_PT_latex_strip_settings)
