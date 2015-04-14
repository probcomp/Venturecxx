# Copyright (c) 2014 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from IPython.core.magic import (Magics,register_cell_magic, magics_class,
                                line_magic, cell_magic, line_cell_magic)

found_venture_ripl = 0

try: 
    from venture.shortcuts import make_church_prime_ripl
    ipy_ripl = make_church_prime_ripl()
    found_venture_ripl += 1
except ImportError,TypeError:
    print 'Error in created Venture RIPL via make_church_prime_ripl()'
        

@magics_class
class VentureMagics(Magics):

    def __init__(self, shell):
        super(VentureMagics, self).__init__(shell)

    @line_cell_magic
    def v(self, line, cell=None):
        '''VentureMagics creates a RIPL on IPython startupt called ipy_ripl.
        You can use the RIPL via Python:
           ipy_ripl.assume('coin','(beta 1 1)')
        
        You can also use the RIPL via magic commands. Use %vl for single
        lines:
           %v [ASSUME coin (beta 1 1)]

        This magic can take Python expansions:
           %v [ASSUME coin {np.random.beta(1,1)} ]

        Use the cell magic %%v for multi-line input:
           %%v
           [ASSUME coin (beta 1 1)]
           [ASSUME x (flip coin)]'''

        def directive_summary(directive):
            'returns summary of directive and its current value'
            ins = directive['instruction']
            d=''

            if ins == 'assume':
                if 'symbol' in directive:
                    d = '%s %s   =  %s' % (ins, directive['symbol'], directive['value'])
            elif ins == 'observe':
                if isinstance(directive['expression'],str):  # [observe x value]
                    d = '%s %s   =  %s' % (ins, directive['expressioxn'], directive['value'])
                elif isinstance(directive['expression'],list):  # [observe (+ 1 x) value]
                    d = '%s (%s ... )    =  %s' % (ins, directive['expression'][0], directive['value'])
            elif ins == 'predict':
                if isinstance(directive['expression'],str): # [predict x] = value
                    d = '%s %s  =  %s' % (ins, directive['expression'],directive['value'])
                elif isinstance(directive['expression'],dict):  # [predict 10] = 10
                    d = '%s %s  =  %s' % (ins,directive['value'], directive['value'])
                elif isinstance(directive['expression'],list):
                    d = '%s (%s ... )   =  %s' % (ins, directive['expression'][0], directive['value'])

            return '[directive_id: %s].  %s ' % (directive['directive_id'], d)
            

        ## FIXME:
        # Need to make things work after ipython %reset
        # recreate ipy_ripl in case of %reset
        # try:
        #     ipy_ripl.__doc__
        # except:
        #     try:
        #         from venture.shortcuts import make_church_prime_ripl
        #         ipy_ripl = make_church_prime_ripl()
        #     except:
        #         print 'failed to make venture ripl'

        

        ## LINE MAGIC
        if cell is None:
            
            venture_outs = ipy_ripl.execute_instruction( str(line), params=None )

            directives = ipy_ripl.list_directives()

            if directives: # if non-empty, print last directive added
                print directive_summary( ipy_ripl.list_directives()[-1] )
                value = ipy_ripl.list_directives()[-1]['value']
            else:
                value = None

            return value,venture_outs
            
        ## CELL MAGIC    
        else:
            old_directives = ipy_ripl.list_directives()

            venture_outs = ipy_ripl.execute_program( str(cell), params=None )

            new_directives = ipy_ripl.list_directives()

            diff = [d for d in new_directives if d not in old_directives]

            # diff is slow, speed up by assuming no [CLEAR] directive
            # diff  = ipy_ripl.list_directives()[ len(old_directives) :]

            values = []
            
            for directive in diff:
                print directive_summary(directive)
                values.append(directive['value'])

            return values,venture_outs
    
    
    
def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(VentureMagics)
    if found_venture_ripl==1: 
        print 'Loaded VentureMagics with RIPL named "ipy_ripl"'
    
try:
    ip = get_ipython()
    load_ipython_extension(ip)

except:
    print 'ip=get_ipython() didnt run'   


