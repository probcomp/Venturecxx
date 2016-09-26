"""provide element targets, that is the elements that are targeted for themeing.


From the ggplot2 documentation the axis.title inherits from text.
What this means is that axis.title and text have the same elements
that may be themed, but the scope of what they apply to is different.
The scope of text covers all text in the plot, axis.title applies
only to the axis.title. In matplotlib terms this means that a theme
that covers text also has to cover axis.title.

"""

from six import with_metaclass

element_target_map = {}


class RegisterElementTarget(type):
    """Register all public element targets so they can be created by name."""
    def __init__(klass, name, bases, class_dict):
        if not name.startswith("_"):
            element_target_map[name] = klass

        super(RegisterElementTarget, klass).__init__(name, bases, class_dict)


def element_target_factory(element_target, element_theme):
    """Create an element target by name."""
    klass = element_target_map.get(element_target)
    if klass:
        return klass(element_theme)
    else:
        raise Exception("no such element target %s" % element_target)


def merge_element_targets(et_list1, et_list2):
    """Merge two lists of element_targets by first sorting them according to
    precedence, then retaining the last instance of a target in case of
    instances.

    """
    return unique_element_targets(sorted_element_targets(et_list1 + et_list2))


def unique_element_targets(element_targets):
    """From a list of element targets, save the last element target for targets
    of the same type.

    This is not strictly necessary, but is an optimaztion when combining themes
    to prevent carrying around themes that will be completely overridden.

    @todo: should merge boy overriding the old properties with the newer
    properties.
    """
    target_seen = set()
    reversed_targets = []
    for element_target in reversed(element_targets):
        if element_target.__class__ not in target_seen:
            target_seen.add(element_target.__class__)
            reversed_targets.append(element_target)

    return [i for i in reversed(reversed_targets)]


def sorted_element_targets(element_target_list):
    """Sort element_targets in reverse based on the their depth in the
    inheritance hierarchy.

    This will make sure any general target, like text will be applied by
    a specific target like axis_text_x.

    """
    def key(element_target_):
        return len(element_target_.__class__.__mro__)

    return sorted(element_target_list, key=key, reverse=True)


class __element_target(with_metaclass(RegisterElementTarget, object)):
    """__element_target is an abstract class of things that can be themed.

    It is the base of a class hierarchy that uses inheritance in a
    non-traditional manner. In the textbook use of class inheritance,
    superclasses are general and subclasses are specializations. In some
    since the hierarchy used here is the opposite in that superclasses
    are more specific than subclasses.

    It is probably better to think if this hierarchy of leveraging
    Python's multiple inheritance to implement composition. For example
    the axis_title target is *composed of* the x_axis_title and the
    y_axis_title. We are just using multiple inheritance to specify
    this composition.

    When implementing a new target based on the ggplot2 documentation, it is
    important to keep this in mind and reverse the order of the "inherits from"
    in the documentation.

    For example, to implement,

    axis.title.x x axis label (element_text; inherits from axis.title)
    axis.title.y y axis label (element_text; inherits from axis.title)

    You would have this implementation:

    class axis_title_x(__element_target):
        ...

    class axis_title_y(__element_target):
        ...

    class axis_title(axis_title_x, axis_title_y):
       ...


    If the superclasses fully implement the subclass, the body of the
    subclass should be "pass". Python will do the right thing.

    When a method does require implementation, call super() then add
    the target's implementation to the axes.

    """
    __metaclass__ = RegisterElementTarget

    def __init__(self, element_theme=None):
        # @todo: fix unittests in test_element_target or leave this as is?
        if element_theme:
            self.properties = element_theme.properties
        else:
            self.properites = {}

    def __eq__(self, other):
        "Mostly for unittesting."
        return ((self.__class__ == other.__class__) and
                (self.properties == other.properties))

    def get_rcParams(self):
        """Add targets rcparams to an rcparam dict before plotting.

        Returns
        -------
        dict
            Dictionary of legal matplotlib parameters.

        This method should always call super(...).get_rcParams and
        update the dictionary that it returns with its own value, and
        return that dictionary.

        This method is called before plotting. It tends to be more useful
        for general targets. Very specific targets often cannot be themed
        until they are created as a result of the plotting process.

        """
        return {}

    def post_plot_callback(self, ax):
        """Called after a chart has been plotted.

        Subclasses should override this method to customize the plot according to
        the theme.

        Parameters
        ----------
        ax : matplotlib.axes.Axes

        This method should be implemented as super(...).post_plot_callback()
        followed by extracting the portion of the axes specific to this
        target then applying the properties to the target.

        """
        pass


class axis_title_x(__element_target):
    def post_plot_callback(self, ax):
        super(axis_title_x, self).post_plot_callback(ax)

        x_axis_label = ax.get_xaxis().get_label()
        x_axis_label.set(**self.properties)


class axis_title_y(__element_target):
    def post_plot_callback(self, ax):
        super(axis_title_y, self).post_plot_callback(ax)
        y_axis_label = ax.get_yaxis().get_label()
        y_axis_label.set(**self.properties)


class axis_title(axis_title_x, axis_title_y):
    pass


class legend_title(__element_target):
    def post_plot_callback(self, ax):
        super(legend_title, self).post_plot_callback(ax)
        legend = ax.get_legend()
        if legend:
            legend.set(**self.properties)


class legend_text(legend_title):
    #@todo: implement me
    pass


class plot_title(__element_target):
    def post_plot_callback(self, ax):
        super(plot_title, self).post_plot_callback(ax)
        ax.title.set(**self.properties)


class strip_text_x(__element_target):
    #@todo implement me
    pass


class strip_text_y(__element_target):
    #@todo implement me
    pass


class strip_text(strip_text_x, strip_text_y):
    pass


class title(axis_title, legend_title, plot_title):
    #@todo: also need to inherit from plot_title and legend_title
    pass


class axis_text_x(__element_target):

    def post_plot_callback(self, ax):
        super(axis_text_x, self).post_plot_callback(ax)
        labels = ax.get_xticklabels()
        for l in labels:
            l.set(**self.properties)


class axis_text_y(__element_target):

    def post_plot_callback(self, ax):
        super(axis_text_y, self).post_plot_callback(ax)
        labels = ax.get_yticklabels()
        for l in labels:
            l.set(**self.properties)


class axis_text(title, axis_text_x, axis_text_y):
    """Set theme the text on x and y axis."""
    pass


class text(axis_text, legend_text, strip_text, title):
    """
    Scope of theme that applies to all text in plot
    """

    def get_rcParams(self):
        rcParams = super(text, self).get_rcParams()
        family = self.properties.get("family")
        if family:
            rcParams["font.family"] = family
        style = self.properties.get("style")
        if style:
            rcParams["font.style"] = style
        weight = self.properties.get("weight")
        if weight:
            rcParams["font.weight"] = weight
        size = self.properties.get("size")
        if size:
            rcParams["font.size"] = size
            rcParams["xtick.labelsize"] = size
            rcParams["ytick.labelsize"] = size
            rcParams["legend.fontsize"] = size
        color = self.properties.get("color")
        if color:
            rcParams["text.color"] = color

        return rcParams
