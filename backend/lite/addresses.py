from venture.lite.node import LookupNode, OutputNode

def compute_addresses_old(trace):
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

def compute_addresses(trace):
    """Compute node addresses for all nodes in a trace."""
    ret = {}
    def get_address(node, prefix):
        if node is None or node in ret:
            return
        ret[node] = prefix
        if isinstance(node, LookupNode):
            get_address(node.sourceNode, prefix + ['sourceNode'])
        elif isinstance(node, OutputNode):
            get_address(node.operatorNode, prefix + ['operatorNode'])
            for i, operandNode in enumerate(node.operandNodes):
                get_address(operandNode, prefix + ['operandNodes', i])
            get_address(node.requestNode, prefix + ['requestNode'])
        if node.madeSPFamilies is not None:
            for id, esrParent in node.madeSPFamilies.families.items():
                # TODO: id may be a RequestNode, which should be recursively addressed
                get_address(esrParent, prefix + ['madeSPFamilies', 'families', id])
    for i, root in trace.families.items():
        get_address(root, prefix=[i])
    return ret

def lookup_address(trace, address):
    """Look up a node in a trace by address."""
    ret = trace.families
    for part in address:
        if isinstance(part, int) or isinstance(ret, dict):
            ret = ret[part]
        elif isinstance(part, str):
            ret = getattr(ret, part)
        else:
            raise ValueError("Invalid address")
    return ret

def test_does_it_work():
    from venture.shortcuts import make_lite_church_prime_ripl
    v = make_lite_church_prime_ripl()
    v.assume('is_tricky', '(flip 0.1)')
    v.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
    v.assume('flip_coin', '(lambda () (flip theta))')
    v.predict('(flip_coin)')
    t = v.sivm.core_sivm.engine.getDistinguishedTrace()
    book1 = compute_addresses(t)
    book2 = compute_addresses_old(t)
    assert book1.viewkeys() == book2.viewkeys()
    for node, address in book1.items():
        assert lookup_address(t, address) is node
    return book1, book2

def test_are_addresses_consistent():
    # quick test to check that nodes keep the same address over time

    # compute addresses on the initial program
    from venture.shortcuts import make_lite_church_prime_ripl
    v = make_lite_church_prime_ripl()
    v.assume('is_tricky', '(flip 0.1)')
    v.assume('theta', '(if is_tricky (beta 1.0 1.0) 0.5)')
    v.assume('flip_coin', '(mem (lambda (x) (flip theta)))')
    address_books = [compute_addresses(v.sivm.core_sivm.engine.getDistinguishedTrace())]

    # compute addresses after inference
    v.infer(100)
    address_books += [compute_addresses(v.sivm.core_sivm.engine.getDistinguishedTrace())]

    # compute addresses after new observations are made
    for i in range(10):
        v.observe('(flip_coin {})'.format(i), 'true')
    v.infer(0)
    address_books += [compute_addresses(v.sivm.core_sivm.engine.getDistinguishedTrace())]

    # this doesn't currently work because the code above assumes esrParents are consistent.
    for i in range(10):
        v.predict('(flip_coin (uniform_discrete 10 12))')
    address_books += [compute_addresses(v.sivm.core_sivm.engine.getDistinguishedTrace())]

    # compute addresses after inference on the new observations
    for i in range(10):
        v.infer(10)
        print v.predict('is_tricky')
        address_books += [compute_addresses(v.sivm.core_sivm.engine.getDistinguishedTrace())]

    # check that no node was assigned more than one address
    import itertools
    for book1, book2 in itertools.product(address_books, address_books):
        for node, address in book1.items():
            assert node not in book2 or book2[node] == address

    return address_books

if __name__ == '__main__':
    book1, book2 = test_does_it_work()
    address_books = test_are_addresses_consistent()
