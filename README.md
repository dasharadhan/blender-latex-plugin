# Blender LaTeX Plugin

A Blender add-on to typset LaTeX directly into the Video Sequence Editor. Whether you are rendering mathematical formulas for a video or generating full presentation storyboards using Beamer, this add-on allows you to write, compile, and place LaTeX-generated images onto your timeline without ever leaving Blender.

**Tested On:** Ubuntu 20.04 | Blender 4.2.2

## Features

- **Two Distinct Workflows:**
  - **Beamer Storyboard:** Write a complete `\documentclass{beamer}` document and automatically split it into a sequence of image strips
  - **Individual Slides:** Generate quick math snippets or text cards on the fly
- **Exact Pixel Resolutions**: Force Ghostscript to render your Beamer slides at the exact resolution of your Blender project (e.g., 1920x1080 or 4K)
- **Non-Blocking Compilation:** Compiles `.tex` files in background threads so Blender's UI does not freeze
- **Auto-Cleanup**: Dedicated buttons to delete strips and instantly wipe the generated PNGs from your hard drive to keep your project folder clean

## Prerequisites

Because this add-on uses your computer's native compilers, you **must** have the following installed and accessible in your system's PATH:

1. **A LaTeX Distribution**: (e.g., [TeX Live](https://tug.org/texlive/), [MiKTeX](https://miktex.org/), or [MacTeX](https://tug.org/mactex/)). The add-on specifically calls `pdflatex`.
2. **Biber**: The modern bibliography processing tool. This is usually bundled automatically with TeX Live and MiKTeX, but the add-on relies on the `biber` command to compile references.
3. **Ghostscript**: (Available at [ghostscript.com](https://ghostscript.com/)). The add-on uses `gs` to convert the compiled PDFs into high-quality, transparent PNGs with exact pixel dimensions.

## Installation

1. Download/Clone this repository
2. Run the [`build.py`](build.py) script to generate the `.zip` archive for the add-on
3. Open Blender and go to `Edit > Preferences > Add-ons`
4. Select the `Install From Disk` menu item
5. Browse for the generated `.zip` archive and select it

## Usage Guide

### Workflow 1: Beamer Storyboard

_Best for long, multi-slide presentations or animations._

1. In the LaTeX panel under **Beamer Storyboard**, click the **+** button. This auto-generates a ready-to-edit Beamer template and links it to the `Source` slot.
2. Open Blender's **Text Editor** Editor to edit `Beamer_Storyboard.tex`.
3. Back in the VSE, set your desired output resolution (e.g., X: 1920, Y: 1080).
4. Click **Build Storyboard**. The add-on will compile the document, split it into PNGs, delete any old storyboard strips, and lay the new slides out sequentially on the timeline.
5. _Note: You can easily clear the storyboard and delete the source files by clicking the red **Remove Storyboard** button._

### Workflow 2: Individual Slides

_Best for quick formulas, lower-thirds, or isolated text graphics._

1. In the Video Sequencer's Add Menu select **Add>LaTeX>LaTeX Strip**. This drops a LaTeX strip onto the timeline.
2. With the strip selected, in the strip's properties panel, **Sidebar>Strip>LaTeX Strip Settings** assig a text block to the **Source** property and select **Edit LaTeX Source**.
3. The LaTeX Editor workspace opens up with the the LaTeX source of the current strip loaded in the Text Editor. Edit the LaTeX source as required (e.g., `\Huge $E=mc^2$`).
4. _(Optional)_ If this specific slide needs a unique package, assign a separate text block to the **Preamble** property. This overrides the default preamble.
5. Click **Compile In-Place** in **Sidebar>Strip>LaTeX Strip Settings**.

## Troubleshooting

**"pdflatex/gs command not found"**
Blender cannot find your LaTeX or Ghostscript installation. Ensure that both `pdflatex` and `gs` are added to your operating system's system `PATH` variables and restart Blender.
