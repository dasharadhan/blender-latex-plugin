import bpy


class VSE_PT_latex_panel(bpy.types.Panel):
    bl_label = "LaTeX Editor"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "LaTeX"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Beamer Storyboard
        box_beamer = layout.box()
        box_beamer.label(text="Beamer Storyboard:", icon="TEXT")

        row = box_beamer.row(align=True)
        row.prop(scene, "latex_master_doc", text="Source")

        # If no text block is selected, show the template generator button
        if not scene.latex_master_doc:
            row.operator("sequencer.create_beamer_template", icon="ADD", text="")
        else:
            box_beamer.separator()
            res_row = box_beamer.row(align=True)
            res_row.prop(scene, "beamer_res_x", text="X")
            res_row.prop(scene, "beamer_res_y", text="Y")

            box_beamer.separator()
            box_beamer.operator(
                "sequencer.build_beamer_storyboard",
                icon="SEQ_SEQUENCER",
                text="Build Storyboard",
            )

            box_beamer.separator()
            row_del = box_beamer.row()
            row_del.alert = True
            row_del.operator(
                "sequencer.remove_beamer_storyboard",
                icon="TRASH",
                text="Remove Storyboard",
            )

        layout.separator()

        # Invividual Slides
        box_single = layout.box()
        box_single.label(text="Individual Slides:", icon="IMAGE_DATA")

        # box_single.prop(context.scene, "latex_preamble", text="")

        box_single.operator(
            "sequencer.add_latex_slide", icon="ADD", text="New LaTeX Slide"
        )

        layout.separator()

        if not context.scene.sequence_editor:
            return

        strip = context.scene.sequence_editor.active_strip
        if strip and hasattr(strip, "latex_text_datablock"):
            layout.separator()
            box_strip = layout.box()
            box_strip.label(text=f"Active: {strip.name}", icon="SEQ_STRIP_META")

            box_strip.prop(strip, "latex_strip_preamble", text="Preamble")

            box_strip.prop(strip, "latex_text_datablock", text="")

            if strip.latex_text_datablock:
                box_strip.separator()
                box_strip.operator(
                    "sequencer.compile_latex_modal",
                    icon="FILE_IMAGE",
                    text="Compile In-Place",
                )

                box_strip.separator()
                row = box_strip.row()
                row.alert = True
                row.operator(
                    "sequencer.delete_latex_slide",
                    icon="TRASH",
                    text="Delete Slide & Files",
                )
        else:
            layout.separator()
            layout.label(text="Select a LaTeX strip to edit.", icon="INFO")


def register():
    bpy.utils.register_class(VSE_PT_latex_panel)


def unregister():
    bpy.utils.unregister_class(VSE_PT_latex_panel)
