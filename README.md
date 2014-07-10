pince-nez
============

A [Blender](http://www.blender.org/) script to to create 3D printable frames from eyeglasses SVGs.

It expects a symmetrical design, and makes a best guess to place nosepads and to protrude the bridge, but does not create temples.

To Run
-------------

In [Blender](http://www.blender.org/), import and select the eyeglasses SVG, and then run the script.

Try it with an [example SVG](http://sethtaylor.com/b2/2013/09/02/free-vector-glasses-icon/)!

Note: I haven't tested Spectacle Creator against a lot of frames, so the parameters might be off for some designs.
Try toggling `bevel` and `make_thin` in the `run` parameters, as well as adjust any of the internal values.
In general, thinner frame designs like the example work better than super thick ones, due to nosepad scaling issues.
Sometimes there are minor issues like a few inverted orientations, so it's always a good idea to pass it through a mesh repair program before printing.
Also, exporting to an STL generally produces better results than to an OBJ.

The lens area may need to be manually altered to fit lenses, depending on the lens.

License
-------------

pince-nez is under [GPLv3](http://opensource.org/licenses/gpl-3.0.html).

A copy of GPLv3 can be found at [http://opensource.org/licenses/gpl-3.0.html](http://opensource.org/licenses/gpl-3.0.html).

Credits
-------------

Created by Jenny - [CaretDashCaret](http://caretdashcaret.wordpress.com/)

[![Jenny](http://i1115.photobucket.com/albums/k552/caretdashcaret/2014-03/About5_zps7f79c497.jpg)](http://caretdashcaret.wordpress.com/)