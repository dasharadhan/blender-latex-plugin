import glob
import os
import subprocess


def compile_latex_to_png(latex_source, asset_dir, render_dir, strip_name, result_dict):
    """
    Compiles LaTeX to PDF, crops it, and converts it to a transparent PNG.
    Saves it directly to {strip_name}.png in the render_dir.
    """
    try:
        tex_path = os.path.join(render_dir, strip_name + ".tex")

        # Write the .tex file
        with open(tex_path, "w", encoding="utf-8") as tex_file:
            tex_file.write(latex_source)

        # Setup Environment Variables for Image Assets
        # This tells pdflatex where to look when it sees \includegraphics
        env = os.environ.copy()
        if asset_dir and os.path.isdir(asset_dir):
            # os.pathsep is ':' on Mac/Linux and ';' on Windows
            # The trailing separator tells LaTeX to also search its default system folders
            env["TEXINPUTS"] = (
                f"{asset_dir}{os.pathsep}{env.get('TEXINPUTS', '')}{os.pathsep}"
            )

        # Compile to PDF
        cmd_pdflatex = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            strip_name + ".tex",
        ]
        p1 = subprocess.run(
            cmd_pdflatex, cwd=render_dir, env=env, capture_output=True, text=True
        )
        if p1.returncode != 0:
            result_dict["error"] = f"pdflatex failed:\n{p1.stdout}\n{p1.stderr}"
            return

        # Crop PDF
        cmd_pdfcrop = ["pdfcrop", strip_name + ".pdf", strip_name + "-crop.pdf"]
        p2 = subprocess.run(cmd_pdfcrop, cwd=render_dir, capture_output=True, text=True)
        if p2.returncode != 0:
            result_dict["error"] = f"pdfcrop failed:\n{p2.stdout}\n{p2.stderr}"
            return

        # Convert to PNG

        # cmd_magick = [
        #     "convert",
        #     "-density",
        #     "300",
        #     "-background",
        #     "none",
        #     strip_name + "-crop.pdf",
        #     strip_name + ".png",
        # ]
        # p3 = subprocess.run(cmd_magick, cwd=render_dir, capture_output=True, text=True)
        # if p3.returncode != 0:
        #     result_dict["error"] = f"ImageMagick failed:\n{p3.stdout}\n{p3.stderr}"
        #     return

        cmd_gs = [
            "gs",
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pngalpha",  # Transparent PNG output
            "-r300",  # DPI resolution (increase for sharper text)
            f"-sOutputFile={strip_name}.png",  # Output file
            f"{strip_name}-crop.pdf",  # Input file
        ]
        p3 = subprocess.run(cmd_gs, cwd=render_dir, capture_output=True, text=True)
        if p3.returncode != 0:
            result_dict["error"] = f"Ghostscript failed:\n{p3.stdout}\n{p3.stderr}"
            return

        # Success
        result_dict["png_path"] = os.path.join(render_dir, strip_name + ".png")

    except Exception as e:
        result_dict["error"] = str(e)


def compile_beamer_storyboard(
    latex_source,
    bibtex_source,
    asset_dir,
    render_dir,
    base_name,
    res_x,
    res_y,
    result_dict,
):
    """
    Compiles a full Beamer document into a multi-page PDF,
    then uses Ghostscript to split it into individual PNG frames.
    """
    try:
        tex_path = os.path.join(render_dir, base_name + ".tex")

        # Write the .tex file
        with open(tex_path, "w", encoding="utf-8") as tex_file:
            tex_file.write(latex_source)

        # Write the .bib file (if provided)
        if bibtex_source.strip():
            bib_path = os.path.join(render_dir, base_name + ".bib")
            with open(bib_path, "w", encoding="utf-8") as bib_file:
                bib_file.write(bibtex_source)

        # Setup Environment Variables for Image Assets
        # This tells pdflatex where to look when it sees \includegraphics
        env = os.environ.copy()
        if asset_dir and os.path.isdir(asset_dir):
            # os.pathsep is ':' on Mac/Linux and ';' on Windows
            # The trailing separator tells LaTeX to also search its default system folders
            env["TEXINPUTS"] = (
                f"{asset_dir}{os.pathsep}{env.get('TEXINPUTS', '')}{os.pathsep}"
            )

        # Compile Beamer to PDF
        cmd_pdflatex = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            base_name + ".tex",
        ]

        # First pdflatex pass (Generates the .bcf file that Biber needs)
        p1 = subprocess.run(
            cmd_pdflatex, cwd=render_dir, env=env, capture_output=True, text=True
        )
        if p1.returncode != 0:
            result_dict["error"] = f"Beamer pdflatex failed:\n{p1.stdout}\n{p1.stderr}"
            return

        # Run BibTeX if we have citations, then compile twice more to link them
        if bibtex_source.strip():
            cmd_biber = ["biber", base_name]

            p_biber = subprocess.run(
                cmd_biber, cwd=render_dir, env=env, capture_output=True, text=True
            )
            if p_biber.returncode != 0:
                result_dict["error"] = (
                    f"Biber failed:\n{p_biber.stdout}\n{p_biber.stderr}"
                )
                return

            # Second pdflatex pass (reads the .bbl file generated by biber)
            subprocess.run(
                cmd_pdflatex, cwd=render_dir, env=env, capture_output=True, text=True
            )

            # Third pdflatex pass (Standard Beamer requirement to resolve final page numbers/overlays)
            subprocess.run(
                cmd_pdflatex, cwd=render_dir, env=env, capture_output=True, text=True
            )

        # Cleanup old PNGs from previous compiles to prevent ghost frames
        old_pngs = glob.glob(os.path.join(render_dir, f"{base_name}_*.png"))
        for png in old_pngs:
            os.remove(png)

        # Convert multi-page PDF to individual PNGs using Ghostscript
        output_pattern = f"{base_name}_%03d.png"
        cmd_gs = [
            "gs",
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pngalpha",
            f"-g{res_x}x{res_y}",
            "-dPDFFitPage",
            f"-sOutputFile={output_pattern}",
            f"{base_name}.pdf",
        ]

        p2 = subprocess.run(cmd_gs, cwd=render_dir, capture_output=True, text=True)
        if p2.returncode != 0:
            result_dict["error"] = (
                f"Ghostscript split failed:\n{p2.stdout}\n{p2.stderr}"
            )
            return

        # Return the base path so the operator can find the generated files
        result_dict["success_dir"] = render_dir
        result_dict["base_name"] = base_name

    except Exception as e:
        result_dict["error"] = str(e)
