from node import LookupNode, OutputNode

def compute_addresses(trace):
    """Compute node addresses for all nodes in a trace."""
    ret = {}
    def get_address(node, prefix):
        if node is None or node in ret:
            return
        ret[node] = prefix
        if isinstance(node, LookupNode):
            get_address(node.sourceNode, prefix + ('sourceNode',))
        elif isinstance(node, OutputNode):
            get_address(node.operatorNode, prefix + ('operatorNode',))
            for i, operandNode in enumerate(node.operandNodes):
                get_address(operandNode, prefix + ('operandNodes', i))
            for i, esrParent in enumerate(node.esrParents):
                # TODO: go through the maker node -> requests rather than esrParents.
                get_address(esrParent, prefix + ('esrParents', i))
            get_address(node.requestNode, prefix + ('requestNode',))
    for i, root in trace.families.items():
        get_address(root, prefix=(i,))
    return ret

def lookup_address(trace, address):
    """Look up a node in a trace by address."""
    ret = trace.families
    for part in address:
        if isinstance(part, int):
            ret = ret[part]
        elif isinstance(part, str):
            ret = getattr(ret, part)
        else:
            raise ValueError("Invalid address")
    return ret

def test_are_addresses_consistent():
    # quick test to check that nodes keep the same address over time

    # compute addresses on the initial program
    from venture.shortcuts import make_lite_church_prime_ripl
    v = make_lite_church_prime_ripl()
    v.assume('is_tricky', '(flip 0.1)')
    v.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
    v.assume('flip_coin', '(mem (lambda (x) (flip theta)))')
    addresses = [compute_addresses(v.sivm.core_sivm.engine.getDistinguishedTrace())]

    # compute addresses after inference
    v.infer(100)
    addresses += [compute_addresses(v.sivm.core_sivm.engine.getDistinguishedTrace())]

    # compute addresses after new observations are made
    for i in range(10):
        v.observe('(flip_coin {})'.format(i), 'true')
        # this doesn't currently work because the code above assumes esrParents are consistent.
        # v.observe('(flip_coin (flip))'.format(i), 'true')
    v.infer(0)
    addresses += [compute_addresses(v.sivm.core_sivm.engine.getDistinguishedTrace())]

    # compute addresses after inference on the new observations
    for i in range(10):
        v.infer(10)
        print v.predict('is_tricky')
        addresses += [compute_addresses(v.sivm.core_sivm.engine.getDistinguishedTrace())]

    # check that no node was assigned more than one address
    import itertools
    for book1, book2 in itertools.product(addresses, addresses):
        for node, address in book1.items():
            assert node not in book2 or book2[node] == address

    return addresses

if __name__ == '__main__':
    addresses = test_are_addresses_consistent()
