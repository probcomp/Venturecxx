from venture import shortcuts


def makeAssumes(my_ripl, parameters):
    my_ripl.assume("topics", str(parameters['topics']))
    my_ripl.assume("vocab", str(parameters['vocab']))
    my_ripl.assume("alpha_document_topic", "(gamma 1.0 1.0)")
    my_ripl.assume("alpha_topic_word", "(gamma 1.0 1.0)")
    my_ripl.assume("get_document_topic_sampler", "(mem (lambda (doc) (make_sym_dir_mult alpha_document_topic topics)))")
    my_ripl.assume("get_topic_word_sampler", "(mem (lambda (topic) (make_sym_dir_mult alpha_topic_word vocab)))")
    my_ripl.assume("get_word", "(mem (lambda (doc pos) ((get_topic_word_sampler ((get_document_topic_sampler doc))))))")


def makeObserves(my_ripl, parameters):
    D = parameters['documents']
    N = parameters['words_per_document']
    for doc in xrange(D):
        for pos in xrange(N):
            my_ripl.observe("(get_word %d %d)" % (doc, pos), "atom<%d>" % 0)
    return


def main():
    my_ripl = shortcuts.make_church_prime_ripl() 
    parameters = {'topics' : 4, 'vocab' : 10, 'documents' : 8, 'words_per_document': 8}
    makeAssumes(my_ripl, parameters)
    makeObserves(my_ripl, parameters)
    return my_ripl, parameters


if __name__ == '__main__':
    my_ripl, parameters = main()
