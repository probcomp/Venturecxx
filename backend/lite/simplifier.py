# Initial efforts towards creating a simplifier.

from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.sp_help import deterministic_typed
import venture.lite.types as t
import venture.lite.value as v
# pattern matching rules
def patcher_matching_WNxWN(kernel1, kernel2):
    if kernel1[0]=="WN" and kernel2[0]=="WN":
        return ["WN", kernel1[1] * kernel2[1]]
    else:
        None

def patcher_matching_CxWN(kernel1, kernel2):
    if kernel1[0]=="C" and kernel2[0]=="WN":
        return ["WN", kernel1[1] * kernel2[1]]
    else:
        None

def patcher_matching_CxC(kernel1, kernel2):
    if kernel1[0]=="C" and kernel2[0]=="C":
        return ["C", kernel1[1] * kernel2[1]]
    else:
        None

def get_pattern_matching_rules():
    return [
        patcher_matching_WNxWN,
        patcher_matching_CxWN,
        patcher_matching_CxC
    ]

def flatten_product(product_parse_tree):
    #base case
    if product_parse_tree[0]!="*" and product_parse_tree[0]!="+":
        return [product_parse_tree]
    elif product_parse_tree[0]=="+":
        raise ValueError("""An error occured - at this stage, the program expects
            only products, not sums""")
    else:
        return flatten_product(product_parse_tree[1]) +\
            flatten_product(product_parse_tree[2])

def parse_to_tree(flat_product):
    #base case
    if len(flat_product)==1:
        return flat_product[0]
    else:
        return ["*", flat_product[0], parse_to_tree(flat_product[1:])]

def simplify_product(product_parse_tree):
    flat_product = flatten_product(product_parse_tree)
    return parse_to_tree(simplify_flat_product(flat_product))

def simplify_flat_product(flat_product):
    sorted_product = sorted(flat_product) 
    if len(sorted_product)==1:
        return sorted_product
    i = 0
    while i<len(sorted_product)-1:
        not_modified = True
        for rule in get_pattern_matching_rules():
           outcome = rule(sorted_product[i], sorted_product[i+1])  
           if outcome is not None:
               sorted_product[i] = outcome
               del sorted_product[i+1]
               not_modified = False
               break
        if not_modified:
            i+=1
    return sorted_product

#TODO this is basically doing the same thing as flatten product, but not turning
# the tree into a list. For now, I parse the tree twice, to keep all my tests
# working. All of this will be re-implemented in Venture anyways.
def unpack_venture_values(venture_parse_tree):
    #base case
    if venture_parse_tree.getArray()[0].getString()!="*" and venture_parse_tree.getArray()[0].getString()!="+":
        return [venture_parse_tree.getArray()[0].getString()] +\
            [value.getNumber() for value in  venture_parse_tree.getArray()[1:]]
    else:
        return ["*", unpack_venture_values(venture_parse_tree.getArray()[1]),
             unpack_venture_values(venture_parse_tree.getArray()[2])]

def pack_venture_values(product_parse_tree):
    if product_parse_tree[0]!="*" and product_parse_tree[0]!="+":
        return v.VentureArray([v.VentureString(product_parse_tree[0])] + \
            [v.VentureNumber(value) for value in product_parse_tree[1:]])
    else:
        return v.VentureArray([v.VentureString(product_parse_tree[0]),
            pack_venture_values(product_parse_tree[1]),
            pack_venture_values(product_parse_tree[1])])

# TODO only handles products for now!
def simplify(venture_parse_tree):
    parse_tree = unpack_venture_values(venture_parse_tree)
    return pack_venture_values(simplify_product(parse_tree))

registerBuiltinSP("simplify_product", deterministic_typed(simplify,
    [t.AnyType()],
    t.AnyType(),
    descr="Simplification and compiler optimization for source for GP structure"))
