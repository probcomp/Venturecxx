from __future__ import division
import colorsys
from itertools import cycle

import numpy as np
import matplotlib as mpl

from six import string_types
from six.moves import range

from . import husl
from .xkcd_rgb import xkcd_rgb




def desaturate(color, prop):
    """Decrease the saturation channel of a color by some percent.

    Parameters
    ----------
    color : matplotlib color
        hex, rgb-tuple, or html color name
    prop : float
        saturation channel of color will be multiplied by this value

    Returns
    -------
    new_color : rgb tuple
        desaturated color code in RGB tuple representation

    """
    # Check inputs
    if not 0 <= prop <= 1:
        raise ValueError("prop must be between 0 and 1")

    # Get rgb tuple rep
    rgb = mplcol.colorConverter.to_rgb(color)

    # Convert to hls
    h, l, s = colorsys.rgb_to_hls(*rgb)

    # Desaturate the saturation channel
    s *= prop

    # Convert back to rgb
    new_color = colorsys.hls_to_rgb(h, l, s)

    return new_color


class _ColorPalette(list):
    """Set the color palette in a with statement, otherwise be a list."""
    def __enter__(self):
        """Open the context."""
        from .rcmod import set_palette
        self._orig_palette = color_palette()
        set_palette(self, len(self))
        return self

    def __exit__(self, *args):
        """Close the context."""
        from .rcmod import set_palette
        set_palette(self._orig_palette, len(self._orig_palette))


def color_palette(name=None, n_colors=6, desat=None):
    """Return a list of colors defining a color palette.

    Availible seaborn palette names:
        deep, muted, bright, pastel, dark, colorblind

    Other options:
        hls, husl, any matplotlib palette

    Matplotlib paletes can be specified as reversed palettes by appending
    "_r" to the name or as dark palettes by appending "_d" to the name.

    This function can also be used in a ``with`` statement to temporarily
    set the color cycle for a plot or set of plots.

    Parameters
    ----------
    name: None, string, or sequence
        Name of palette or None to return current palette. If a
        sequence, input colors are used but possibly cycled and
        desaturated.
    n_colors : int
        Number of colors in the palette. If larger than the number of
        colors in the palette, they will cycle.
    desat : float
        Value to desaturate each color by.

    Returns
    -------
    palette : list of RGB tuples.
        Color palette.

    Examples
    --------
    >>> p = color_palette("muted")

    >>> p = color_palette("Blues_d", 10)

    >>> p = color_palette("Set1", desat=.7)

    >>> import matplotlib.pyplot as plt
    >>> with color_palette("husl", 8):
    ...     f, ax = plt.subplots()
    ...     ax.plot(x, y)                  # doctest: +SKIP

    See Also
    --------
    set_palette : set the default color cycle for all plots.
    axes_style : define parameters to set the style of plots
    plotting_context : define parameters to scale plot elements

    """
    seaborn_palettes = dict(
        deep=["#4C72B0", "#55A868", "#C44E52",
              "#8172B2", "#CCB974", "#64B5CD"],
        muted=["#4878CF", "#6ACC65", "#D65F5F",
               "#B47CC7", "#C4AD66", "#77BEDB"],
        pastel=["#92C6FF", "#97F0AA", "#FF9F9A",
                "#D0BBFF", "#FFFEA3", "#B0E0E6"],
        bright=["#003FFF", "#03ED3A", "#E8000B",
                "#8A2BE2", "#FFC400", "#00D7FF"],
        dark=["#001C7F", "#017517", "#8C0900",
              "#7600A1", "#B8860B", "#006374"],
        colorblind=["#0072B2", "#009E73", "#D55E00",
                    "#CC79A7", "#F0E442", "#56B4E9"],
    )

    if name is None:
        palette = mpl.rcParams["axes.color_cycle"]
    elif not isinstance(name, string_types):
        palette = name
    elif name == "hls":
        palette = hls_palette(n_colors)
    elif name == "husl":
        palette = husl_palette(n_colors)
    elif name in seaborn_palettes:
        palette = seaborn_palettes[name]
    elif name in dir(mpl.cm):
        palette = mpl_palette(name, n_colors)
    elif name[:-2] in dir(mpl.cm):
        palette = mpl_palette(name, n_colors)
    else:
        raise ValueError("%s is not a valid palette name" % name)

    if desat is not None:
        palette = [desaturate(c, desat) for c in palette]

    # Always return as many colors as we asked for
    pal_cycle = cycle(palette)
    palette = [next(pal_cycle) for _ in range(n_colors)]

    # Always return in r, g, b tuple format
    try:
        palette = map(mpl.colors.colorConverter.to_rgb, palette)
        palette = _ColorPalette(palette)
    except ValueError:
        raise ValueError("Could not generate a palette for %s" % str(name))

    return palette


def hls_palette(n_colors=6, h=.01, l=.6, s=.65):
    """Get a set of evenly spaced colors in HLS hue space.

    h, l, and s should be between 0 and 1

    Parameters
    ----------

    n_colors : int
        number of colors in the palette
    h : float
        first hue
    l : float
        lightness
    s : float
        saturation

    Returns
    -------
    palette : list of tuples
        color palette

    """
    hues = np.linspace(0, 1, n_colors + 1)[:-1]
    hues += h
    hues %= 1
    hues -= hues.astype(int)
    palette = [colorsys.hls_to_rgb(h_i, l, s) for h_i in hues]
    return palette


def husl_palette(n_colors=6, h=.01, s=.9, l=.65):
    """Get a set of evenly spaced colors in HUSL hue space.

    h, s, and l should be between 0 and 1

    Parameters
    ----------

    n_colors : int
        number of colors in the palette
    h : float
        first hue
    s : float
        saturation
    l : float
        lightness

    Returns
    -------
    palette : list of tuples
        color palette

    """
    hues = np.linspace(0, 1, n_colors + 1)[:-1]
    hues += h
    hues %= 1
    hues *= 359
    s *= 99
    l *= 99
    palette = [husl.husl_to_rgb(h_i, s, l) for h_i in hues]
    return palette


def mpl_palette(name, n_colors=6):
    """Return discrete colors from a matplotlib palette.

    Note that this handles the qualitative colorbrewer palettes
    properly, although if you ask for more colors than a particular
    qualitative palette can provide you will fewer than you are
    expecting.

    Parameters
    ----------
    name : string
        name of the palette
    n_colors : int
        number of colors in the palette

    Returns
    -------
    palette : list of tuples
        palette colors in r, g, b format

    """
    brewer_qual_pals = {"Accent": 8, "Dark2": 8, "Paired": 12,
                        "Pastel1": 9, "Pastel2": 8,
                        "Set1": 9, "Set2": 8, "Set3": 12}

    if name.endswith("_d"):
        pal = ["#333333"]
        pal.extend(color_palette(name.replace("_d", "_r"), 2))
        cmap = blend_palette(pal, n_colors, as_cmap=True)
    else:
        cmap = getattr(mpl.cm, name)
    if name in brewer_qual_pals:
        bins = np.linspace(0, 1, brewer_qual_pals[name])[:n_colors]
    else:
        bins = np.linspace(0, 1, n_colors + 2)[1:-1]
    palette = list(map(tuple, cmap(bins)[:, :3]))

    return palette


def dark_palette(color, n_colors=6, reverse=False, as_cmap=False):
    """Make a palette that blends from a deep gray to `color`.

    Parameters
    ----------
    color : matplotlib color
        hex, rgb-tuple, or html color name
    n_colors : int, optional
        number of colors in the palette
    reverse : bool, optional
        if True, reverse the direction of the blend
    as_cmap : bool, optional
        if True, return as a matplotlib colormap instead of list

    Returns
    -------
    palette : list or colormap

    """
    gray = "#222222"
    colors = [color, gray] if reverse else [gray, color]
    return blend_palette(colors, n_colors, as_cmap)


def blend_palette(colors, n_colors=6, as_cmap=False):
    """Make a palette that blends between a list of colors.

    Parameters
    ----------
    colors : sequence of matplotlib colors
        hex, rgb-tuple, or html color name
    n_colors : int, optional
        number of colors in the palette
    as_cmap : bool, optional
        if True, return as a matplotlib colormap instead of list

    Returns
    -------
    palette : list or colormap

    """
    name = "-".join(map(str, colors))
    pal = mpl.colors.LinearSegmentedColormap.from_list(name, colors)
    if not as_cmap:
        pal = pal(np.linspace(0, 1, n_colors))
    return pal


def xkcd_palette(colors):
    """Make a palette with color names from the xkcd color survey.

    This is just a simple wrapper around the seaborn.xkcd_rbg dictionary.

    See xkcd for the full list of colors: http://xkcd.com/color/rgb/

    """
    palette = [xkcd_rgb[name] for name in colors]
    return color_palette(palette, len(palette))


def cubehelix_palette(n_colors=6, start=0, rot=.4, gamma=1.0, hue=0.8,
                      light=.85, dark=.15, reverse=False, as_cmap=False):
    """Make a sequential palette from the cubehelix system.

    This produces a colormap with linearly-decreasing (or increasing)
    brightness. That means that information will be preserved if printed to
    black and white or viewed by someone who is colorblind.  "cubehelix" is
    also availible as a matplotlib-based palette, but this function gives the
    user more control over the look of the palette and has a different set of
    defaults.

    Parameters
    ----------
    n_colors : int
        Number of colors in the palette.
    start : float, 0 <= start <= 3
        The hue at the start of the helix.
    rot : float
        Rotations around the hue wheel over the range of the palette.
    gamma : float 0 <= gamma
        Gamma factor to emphasize darker (gamma < 1) or lighter (gamma > 1)
        colors.
    hue : float, 0 <= hue <= 1
        Saturation of the colors.
    dark : float 0 <= dark <= 1
        Intensity of the darkest color in the palette.
    light : float 0 <= light <= 1
        Intensity of the lightest color in the palette.
    reverse : bool
        If True, the palette will go from dark to light.
    as_cmap : bool
        If True, return a matplotlib colormap instead of a list of colors.

    Returns
    -------
    palette : list or colormap

    References
    ----------
    Green, D. A. (2011). "A colour scheme for the display of astronomical
    intensity images". Bulletin of the Astromical Society of India, Vol. 39,
    p. 289-295.

    """
    cdict = mpl._cm.cubehelix(gamma, start, rot, hue)
    cmap = mpl.colors.LinearSegmentedColormap("cubehelix", cdict)

    x = np.linspace(light, dark, n_colors)
    pal = cmap(x)[:, :3].tolist()
    if reverse:
        pal = pal[::-1]

    if as_cmap:
        x_256 = np.linspace(light, dark, 256)
        if reverse:
            x_256 = x_256[::-1]
        pal_256 = cmap(x_256)
        cmap = mpl.colors.ListedColormap(pal_256)
        return cmap
    else:
        return pal
