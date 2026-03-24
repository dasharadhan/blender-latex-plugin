import glob
import os
import shutil
import threading

import bpy

from .compiler import compile_beamer_storyboard, compile_latex_to_png

# Default Preamble for LaTeX
DEFAULT_PREAMBLE = r"""\usepackage[paperheight=48in,paperwidth=36in,margin=0in]{geometry}
\usepackage{amsmath,amsthm,amssymb,amsfonts}
\usepackage{color}
\setlength{\parindent}{0pt}
"""

# Default Beamer template
DEFAULT_BEAMER_TEMPLATE = r"""\documentclass[aspectratio=169]{beamer}
\usepackage{amsmath,amsthm,amssymb,amsfonts}
\usepackage{color}
\usetheme{default}

% --- Hide navigation bar and slide numbers ---
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{footline}{}

\begin{document}

\begin{frame}{My First Scene}
    Welcome to your new Beamer Storyboard!
\end{frame}

\begin{frame}{Animating Text}
    Here is point one.
    \pause % This creates a second image automatically!
    Here is point two.
\end{frame}

\end{document}
"""


class VSE_OT_add_latex_slide(bpy.types.Operator):
    """Generates a new Image Strip and linked Text Datablock for a LaTeX slide"""

    bl_idname = "sequencer.add_latex_slide"
    bl_label = "Add New LaTeX Slide"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not bpy.data.is_saved:
            self.report({"ERROR"}, "Please save your .blend file first!")
            return {"CANCELLED"}

        if not context.scene.sequence_editor:
            context.scene.sequence_editor_create()
        vse = context.scene.sequence_editor

        if not context.scene.latex_preamble:
            preamble_txt = bpy.data.texts.get("LaTeX_Preamble")
            if not preamble_txt:
                preamble_txt = bpy.data.texts.new("LaTeX_Preamble")
                preamble_txt.write(DEFAULT_PREAMBLE)
            context.scene.latex_preamble = preamble_txt

        start_frame = context.scene.frame_current
        duration = 100
        channel = 1

        if vse.active_strip:
            channel = vse.active_strip.channel + 1

        slide_count = sum(1 for s in vse.sequences if s.name.startswith("LaTeX_Slide"))
        strip_name = f"LaTeX_Slide_{slide_count + 1:03d}"

        blend_dir = os.path.dirname(bpy.data.filepath)
        render_dir = os.path.join(blend_dir, "Render/LaTeX_Renders", strip_name)
        os.makedirs(render_dir, exist_ok=True)

        placeholder_path = os.path.join(render_dir, strip_name + ".png")

        if not os.path.exists(placeholder_path):
            img = bpy.data.images.new(strip_name, width=1, height=1, alpha=True)
            img.filepath_raw = placeholder_path
            img.file_format = "PNG"
            img.save()
            bpy.data.images.remove(img)

        strip = vse.sequences.new_image(
            name=strip_name,
            filepath=placeholder_path,
            channel=channel,
            frame_start=start_frame,
        )
        strip.frame_final_end = start_frame + duration

        txt = bpy.data.texts.new(name=f"{strip_name}_source")

        safe_name = strip_name.replace("_", "\\_")
        txt.write(f"\\textbf{{{safe_name}}}\n\nStart typing your LaTeX here...")
        strip.latex_text_datablock = txt

        bpy.ops.sequencer.select_all(action="DESELECT")
        strip.select = True
        vse.active_strip = strip

        self.report({"INFO"}, f"Added {strip_name}")
        return {"FINISHED"}


class VSE_OT_compile_latex_modal(bpy.types.Operator):
    """Compiles the linked LaTeX Text Datablock and updates the strip in-place"""

    bl_idname = "sequencer.compile_latex_modal"
    bl_label = "Compile & Update In-Place"

    _timer = None
    _thread = None
    _render_dir = None
    _result_dict = {}

    def modal(self, context, event):
        if event.type == "TIMER":
            if not self._thread.is_alive():
                wm = context.window_manager
                wm.event_timer_remove(self._timer)

                if "error" in self._result_dict:
                    self.report({"ERROR"}, "Compilation Failed! Check Console.")
                    print(
                        "\n--- LaTeX Error ---\n",
                        self._result_dict["error"],
                        "\n-------------------\n",
                    )

                elif "png_path" in self._result_dict:
                    png_path = self._result_dict["png_path"]
                    self.report({"INFO"}, "Success! Updating strip...")

                    strip = context.scene.sequence_editor.active_strip
                    if strip and strip.type == "IMAGE":
                        strip.directory = os.path.dirname(png_path) + os.sep
                        strip.elements[0].filename = os.path.basename(png_path)

                        for img in bpy.data.images:
                            if (
                                img.filepath == png_path
                                or img.filepath == bpy.path.relpath(png_path)
                            ):
                                img.reload()

                        bpy.ops.sequencer.refresh_all()
                    else:
                        self.report(
                            {"WARNING"},
                            "Active strip is not an Image Strip! Cannot update in-place.",
                        )

                return {"FINISHED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        strip = context.scene.sequence_editor.active_strip

        if not strip or not getattr(strip, "latex_text_datablock", None):
            self.report({"WARNING"}, "No active strip or Text datablock linked.")
            return {"CANCELLED"}

        if strip.type != "IMAGE":
            self.report({"WARNING"}, "Please select an Image Strip to overwrite.")
            return {"CANCELLED"}

        if not bpy.data.is_saved:
            self.report({"ERROR"}, "Please save your .blend file first!")
            return {"CANCELLED"}

        blend_dir = os.path.dirname(bpy.data.filepath)
        self._render_dir = os.path.join(blend_dir, "Render/LaTeX_Renders", strip.name)
        os.makedirs(self._render_dir, exist_ok=True)

        text_lines = [line.body for line in strip.latex_text_datablock.lines]
        latex_text = "\n".join(text_lines)

        if hasattr(strip, "latex_strip_preamble") and strip.latex_strip_preamble:
            preamble_txt = strip.latex_strip_preamble
        else:
            preamble_txt = context.scene.latex_preamble

        if preamble_txt:
            preamble = "\n".join([line.body for line in preamble_txt.lines])
        else:
            preamble = DEFAULT_PREAMBLE

        full_latex_source = f"\\documentclass{{article}}\n{preamble}\n\\pagestyle{{empty}}\n\\begin{{document}}\n{latex_text}\n\\end{{document}}"

        self._result_dict = {}

        self._thread = threading.Thread(
            target=compile_latex_to_png,
            args=(full_latex_source, self._render_dir, strip.name, self._result_dict),
        )
        self._thread.start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)

        self.report({"INFO"}, "Compiling LaTeX in background...")
        return {"RUNNING_MODAL"}


class VSE_OT_delete_latex_slide(bpy.types.Operator):
    """Deletes the strip, its linked Text datablock, and the folder on your hard drive"""

    bl_idname = "sequencer.delete_latex_slide"
    bl_label = "Delete Slide & Files"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        vse = context.scene.sequence_editor
        strip = vse.active_strip

        if not strip:
            self.report({"WARNING"}, "No active strip selected.")
            return {"CANCELLED"}

        strip_name = strip.name
        txt = strip.latex_text_datablock

        # Delete the specific folder from your hard drive
        if bpy.data.is_saved:
            blend_dir = os.path.dirname(bpy.data.filepath)
            strip_dir = os.path.join(blend_dir, "Render/LaTeX_Renders", strip_name)

            if os.path.exists(strip_dir):
                # This deletes the folder and everything inside it
                shutil.rmtree(strip_dir)

        # Delete the Text Datablock from Blender's memory
        if txt:
            bpy.data.texts.remove(txt)

        # Delete the Image Datablock from Blender's memory (so it doesn't linger)
        # Usually, the image datablock has the same name as the strip
        img = bpy.data.images.get(strip_name)
        if img:
            bpy.data.images.remove(img)

        # Finally, remove the strip from the timeline
        vse.sequences.remove(strip)

        self.report({"INFO"}, f"Deleted {strip_name} and all its files.")
        return {"FINISHED"}


class VSE_OT_build_beamer_storyboard(bpy.types.Operator):
    """Compiles a full Beamer document and generates a storyboard timeline"""

    bl_idname = "sequencer.build_beamer_storyboard"
    bl_label = "Build Beamer Storyboard"

    _timer = None
    _thread = None
    _result_dict = {}

    def modal(self, context, event):
        if event.type == "TIMER":
            if not self._thread.is_alive():
                wm = context.window_manager
                wm.event_timer_remove(self._timer)

                if "error" in self._result_dict:
                    self.report({"ERROR"}, "Beamer Compilation Failed! Check Console.")
                    print(
                        "\n--- Beamer Error ---\n",
                        self._result_dict["error"],
                        "\n-------------------\n",
                    )

                elif "success_dir" in self._result_dict:
                    self.report({"INFO"}, "Success! Building timeline...")

                    vse = context.scene.sequence_editor
                    render_dir = self._result_dict["success_dir"]
                    base_name = self._result_dict["base_name"]

                    seq_editor = context.scene.sequence_editor

                    for strip in list(seq_editor.sequences_all):
                        # If the strip name starts with "Beamer_Slide", delete it
                        if strip.name.startswith(base_name):
                            seq_editor.sequences.remove(strip)

                    # Find all generated PNGs and sort them alphabetically (001, 002, 003...)
                    png_files = sorted(
                        glob.glob(os.path.join(render_dir, f"{base_name}_*.png"))
                    )

                    start_frame = context.scene.frame_current
                    duration = 100  # Frames per slide
                    channel = (
                        1 if not vse.active_strip else vse.active_strip.channel + 1
                    )

                    # Drop each slide onto the timeline sequentially
                    for png_path in png_files:
                        strip_name = os.path.basename(png_path).replace(".png", "")

                        strip = vse.sequences.new_image(
                            name=strip_name,
                            filepath=png_path,
                            channel=channel,
                            frame_start=start_frame,
                        )
                        strip.frame_final_end = start_frame + duration
                        start_frame += duration

                    bpy.ops.sequencer.refresh_all()

                return {"FINISHED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        if not bpy.data.is_saved:
            self.report({"ERROR"}, "Please save your .blend file first!")
            return {"CANCELLED"}

        master_txt = context.scene.latex_master_doc
        if not master_txt:
            self.report({"ERROR"}, "Please link a Master Document in the UI first!")
            return {"CANCELLED"}

        if not context.scene.sequence_editor:
            context.scene.sequence_editor_create()

        # Create a dedicated Storyboard folder
        blend_dir = os.path.dirname(bpy.data.filepath)
        render_dir = os.path.join(blend_dir, "Render/LaTeX_Renders", "Storyboard")
        os.makedirs(render_dir, exist_ok=True)

        full_latex_source = master_txt.as_string()

        # Grab resolution from the Scene
        res_x = context.scene.beamer_res_x
        res_y = context.scene.beamer_res_y

        base_name = "Beamer_Slide"

        self._result_dict = {}
        self._thread = threading.Thread(
            target=compile_beamer_storyboard,
            args=(
                full_latex_source,
                render_dir,
                base_name,
                res_x,
                res_y,
                self._result_dict,
            ),
        )
        self._thread.start()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)

        self.report({"INFO"}, "Compiling Beamer Storyboard...")
        return {"RUNNING_MODAL"}


class VSE_OT_create_beamer_template(bpy.types.Operator):
    """Generates a default Beamer document and assigns it as the Master Document"""

    bl_idname = "sequencer.create_beamer_template"
    bl_label = "Create Beamer Template"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Create a new text block
        txt = bpy.data.texts.new(name="Beamer_Storyboard.tex")
        txt.write(DEFAULT_BEAMER_TEMPLATE)

        # Assign it to the UI property
        context.scene.latex_master_doc = txt

        self.report({"INFO"}, "Created Beamer Template!")
        return {"FINISHED"}


class VSE_OT_remove_beamer_storyboard(bpy.types.Operator):
    """Remove Storyboard strips from the timeline and delete rendered files"""

    bl_idname = "sequencer.remove_beamer_storyboard"
    bl_label = "Remove Storyboard"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        seq_editor = context.scene.sequence_editor
        if not seq_editor:
            return {"CANCELLED"}

        base_name = "Beamer_Slide"
        removed_count = 0

        # Sweep the timeline and delete the strips
        for strip in list(seq_editor.sequences_all):
            if strip.name.startswith(base_name):
                seq_editor.sequences.remove(strip)
                removed_count += 1

        # Sweep the hard drive and delete the PNG files
        if bpy.data.is_saved:
            blend_dir = os.path.dirname(bpy.data.filepath)
            render_dir = os.path.join(blend_dir, "Render/LaTeX_Renders", "Storyboard")

            if os.path.exists(render_dir):
                import glob

                old_pngs = glob.glob(os.path.join(render_dir, f"{base_name}_*.png"))
                for png in old_pngs:
                    try:
                        os.remove(png)
                    except Exception:
                        pass  # If Windows is locking a file, just skip it

        self.report(
            {"INFO"},
            f"Removed {removed_count} Storyboard slide(s) and cleaned up files!",
        )
        return {"FINISHED"}


def register():
    bpy.utils.register_class(VSE_OT_add_latex_slide)
    bpy.utils.register_class(VSE_OT_compile_latex_modal)
    bpy.utils.register_class(VSE_OT_delete_latex_slide)
    bpy.utils.register_class(VSE_OT_create_beamer_template)
    bpy.utils.register_class(VSE_OT_build_beamer_storyboard)
    bpy.utils.register_class(VSE_OT_remove_beamer_storyboard)

    bpy.types.Scene.beamer_res_x = bpy.props.IntProperty(
        name="Resolution X", default=1920, min=100
    )

    bpy.types.Scene.beamer_res_y = bpy.props.IntProperty(
        name="Resolution Y", default=1080, min=100
    )

    bpy.types.Scene.latex_master_doc = bpy.props.PointerProperty(
        type=bpy.types.Text, name="Master Document"
    )

    bpy.types.Scene.latex_preamble = bpy.props.PointerProperty(
        type=bpy.types.Text,
        name="Global Preamble",
        description="Link a Text datablock for your document preamble",
    )

    bpy.types.Sequence.latex_strip_preamble = bpy.props.PointerProperty(
        type=bpy.types.Text, name="Slide Preamble"
    )

    bpy.types.Sequence.latex_text_datablock = bpy.props.PointerProperty(
        type=bpy.types.Text,
        name="LaTeX Script",
        description="Link a Text datablock for multi-line LaTeX editing",
    )


def unregister():
    bpy.utils.unregister_class(VSE_OT_add_latex_slide)
    bpy.utils.unregister_class(VSE_OT_compile_latex_modal)
    bpy.utils.unregister_class(VSE_OT_delete_latex_slide)
    bpy.utils.unregister_class(VSE_OT_build_beamer_storyboard)
    bpy.utils.unregister_class(VSE_OT_create_beamer_template)
    bpy.utils.unregister_class(VSE_OT_remove_beamer_storyboard)

    del bpy.types.Scene.beamer_res_x
    del bpy.types.Scene.beamer_res_y
    del bpy.types.Scene.latex_master_doc
    del bpy.types.Scene.latex_preamble

    del bpy.types.Sequence.latex_text_datablock
    del bpy.types.Sequence.latex_strip_preamble
