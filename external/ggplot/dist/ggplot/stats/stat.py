from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import sys
from copy import deepcopy

from ..utils.exceptions import GgplotError

__all__ = ['stat']
__all__ = [str(u) for u in __all__]


class stat(object):
    """Base class of all stats"""
    REQUIRED_AES = set()
    DEFAULT_PARAMS = dict()

    # Stats may modify existing columns or create extra
    # columns.
    #
    # Any extra columns that may be created by the stat
    # should be specified in this set
    # see: stat_bin
    CREATES = set()

    # used by _print_warning to keep track of the
    # warning messages printed to the standard error
    _warnings_printed = set()

    def __init__(self, *args, **kwargs):
        _params, kwargs = self._find_stat_params(kwargs)
        self.params = deepcopy(self.DEFAULT_PARAMS)
        self.params.update(_params)

        self._cache = {}
        # Whatever arguments cannot be recognised as
        # parameters, will be used to create a geom
        self._cache['args'] = args
        self._cache['kwargs'] = kwargs

    def _print_warning(self, message):
        """
        Prints message to the standard error.
        """
        if message not in self._warnings_printed:
            sys.stderr.write(message)
            self._warnings_printed.add(message)

    # For some stats we need to calculate something from the entire set of data
    # before we work with the groups. An example is stat_bin, where we need to
    # know the max and min of the x-axis globally. If we don't we end up with
    # groups that are binned based on only the group x-axis leading to
    # different bin-sizes.
    def _calculate_global(self, data):
        pass

    def _calculate(self, data):
        msg = "{} should implement this method."
        raise NotImplementedError(
            msg.format(self.__class__.__name__))

    def __radd__(self, gg):
        # Create and add a geom to ggplot object
        import venture.ggplot.geoms as geoms
        _g = getattr(geoms, 'geom_' + self.params['geom'])
        _geom = _g(*self._cache['args'], **self._cache['kwargs'])
        _geom.params['stat'] = self.__class__.__name__
        _geom.params['position'] = self.params['position']
        _geom._stat = self
        return gg + _geom

    def _find_stat_params(self, kwargs):
        """
        Identity and return the stat parameters.

        The identified parameters are removed from kwargs

        Parameters
        ----------
        kwargs : dict
            keyword arguments passed to stat.__init__

        Returns
        -------
        d : dict
            stat parameters
        kwargs : dict
            rest of the kwargs
        """
        d = {}
        for k in list(kwargs.keys()):
            if k in self.DEFAULT_PARAMS:
                d[k] = kwargs.pop(k)
        return d, kwargs

    def _verify_aesthetics(self, data):
        """
        Check if all the required aesthetics have been specified

        Raise an Exception if an aesthetic is missing
        """
        missing_aes = self.REQUIRED_AES - set(data.columns)
        if missing_aes:
            msg = '{} requires the following missing aesthetics: {}'
            raise GgplotError(msg.format(
                self.__class__.__name__, ', '.join(missing_aes)))
