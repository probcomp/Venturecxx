from venture import shortcuts
from venture.unit import VentureUnit

class LDA(VentureUnit):
    # def makeAssumes(self):
        # self.assume("no_topics", self.parameters['no_topics'])
        # self.assume("size_vocab", self.parameters['size_vocab'])
        # self.assume("alpha_document_topic", "(gamma 1.0 2.0)")
        # self.assume("alpha_topic_word", "(gamma 1.0 2.0)")
        # self.assume("get_document", "(mem (lambda (doc_ind) (make_sym_dir_mult alpha_document_topic no_topics)))")
        # self.assume("get_topic", "(mem (lambda (topic_ind) (make_sym_dir_mult alpha_topic_word size_vocab)))")
        # self.assume("topic0","(get_topic atom<0>)")
        # self.assume("topic1","(+ ((get_topic atom<0>)) )")
        # self.assume("document0","(get_document 0)")

        # self.assume("get_word", "(mem (lambda (doc_ind word_ind) ((get_topic ((get_document doc_ind))))))")
        # return

    def makeAssumes(self):
        self.assume("no_topics", self.parameters['no_topics'])
        self.assume("size_vocab", self.parameters['size_vocab'])
        self.assume("alpha_document_topic", "(gamma 1.0 2.0)")
        self.assume("alpha_topic_word", "(gamma 1.0 2.0)")
        self.assume("new_doc","(lambda () (make_sym_dir_mult alpha_document_topic no_topics))")
        self.assume("documents","(array (new_doc) (new_doc) (new_doc) (new_doc) (new_doc) )" )

        self.assume("new_topic","(lambda () (make_sym_dir_mult alpha_topic_word size_vocab))")
        self.assume("topics","(array (new_topic) (new_topic) (new_topic) (new_topic) )" )
        self.assume("get_word", "(mem (lambda (doc_ind word_ind) ((lookup topics ((lookup documents doc_ind) ))) ))")


    def makeObserves(self):
        D = self.parameters['no_documents']
        N = self.parameters['no_words']

        
        for doc_ind in range(D):
            for word_ind in range(N):
                self.observe("(get_word %d %d)" % (doc_ind,word_ind), "atom<%d>" % 0)
        return

if __name__ == '__main__':
    ripl = shortcuts.make_puma_church_prime_ripl()

    parameters = {'size_vocab': 30, 'doc_length': 50, 'no_documentss': 8, 'no_topics': 4}    
    #'alpha_w_prior': '.4', 'alpha_t_prior': '.4'
    #parameters = {'no_topics' : 4, 'size_vocab' : 10, 'no_documents' : 5, 'no_words' : 20}
    #data = [0] * ( parameters['no_documents'] * parameters['no_words'])
                        #(int( .5 *parameters['no_documents'] * parameters['no_words']) )

    all_docs=[[22, 7, 29, 11, 25, 0, 4, 11, 5, 11, 2, 11, 11, 2, 29, 28, 11, 23, 26, 5, 11, 23, 2, 29, 12, 0, 29, 11, 11, 2, 3, 11, 29, 4, 12, 1, 21, 11, 2, 29, 11, 29, 29, 5, 4, 0, 11, 2, 21, 23], [18, 23, 0, 13, 27, 8, 29, 26, 24, 16, 26, 17, 8, 4, 7, 22, 0, 21, 26, 2, 7, 7, 7, 18, 13, 27, 12, 29, 2, 26, 2, 26, 29, 15, 23, 23, 7, 17, 18, 26, 17, 24, 22, 2, 26, 18, 20, 23, 17, 3], [23, 22, 23, 28, 7, 6, 26, 4, 23, 28, 27, 14, 18, 18, 28, 23, 2, 23, 26, 2, 28, 7, 0, 19, 26, 18, 22, 16, 18, 16, 2, 2, 8, 22, 4, 21, 8, 15, 26, 23, 8, 17, 6, 16, 29, 26, 8, 15, 22, 18], [29, 17, 16, 12, 19, 29, 26, 26, 17, 16, 0, 29, 28, 7, 26, 23, 6, 17, 13, 0, 2, 5, 7, 17, 12, 23, 14, 11, 21, 0, 2, 23, 23, 2, 28, 4, 21, 21, 2, 23, 11, 24, 29, 26, 18, 27, 12, 18, 23, 22], [26, 0, 18, 0, 5, 2, 2, 11, 7, 11, 0, 3, 11, 11, 11, 11, 6, 0, 25, 29, 0, 2, 29, 29, 5, 23, 7, 23, 11, 11, 11, 22, 25, 23, 5, 7, 7, 18, 17, 11, 2, 28, 12, 28, 28, 2, 2, 0, 11, 23], [29, 11, 11, 12, 8, 11, 11, 28, 11, 8, 18, 3, 11, 3, 29, 5, 11, 23, 2, 2, 11, 2, 11, 3, 2, 23, 17, 2, 12, 2, 11, 11, 2, 11, 29, 14, 5, 2, 23, 5, 11, 11, 16, 28, 12, 28, 11, 11, 11, 11], [28, 11, 11, 28, 2, 22, 7, 7, 7, 28, 5, 22, 7, 6, 2, 22, 23, 28, 0, 26, 7, 7, 7, 28, 22, 18, 23, 23, 23, 28, 0, 23, 21, 17, 22, 23, 17, 22, 24, 11, 0, 22, 28, 5, 18, 25, 23, 5, 11, 29], [22, 8, 23, 27, 26, 6, 5, 17, 17, 18, 8, 26, 28, 22, 16, 23, 18, 2, 7, 8, 26, 23, 28, 7, 18, 11, 7, 2, 4, 17, 24, 22, 27, 7, 23, 17, 12, 26, 8, 8, 7, 16, 23, 26, 0, 17, 16, 27, 7, 7]];

    data = [ el  for doc in all_docs for el in doc]
    model = LDA(ripl, parameters)
    
    #history = model.runFromJoint(50, verbose=True)
    #history = model.sampleFromJoint(20, verbose=True)
    #sample_hist, infer_hist, klHistory = model.computeJointKL(200, 50, verbose=True)
    
    #history = model.runConditionedFromPrior(10,runs=3, verbose=True)
    history = model.runFromConditional(10,verbose=True,data=data)


    no_topics = history.nameToSeries['no_topics'][0].values[0]
    #no_docs = history.nameToSeries['no_documents'][0].values[0]
    

    topics = history.nameToSeries['topics'][0].values[-1]
    
    
    #topic0_out = history.nameToSeries['topic0']
    #doc0_out = history.nameToSeries['document0']















    #klHistory.plot(fmt='png')
    
    #parameters = {'topics' : [4, 8], 'vocab' : 10, 'documents' : [8, 12], 'words_per_document' : [10, 100]}
    #run_count = 0
    #def runner(params):
    #    print "Running setting " + str(run_count) + " of 8"
    #    print params
    #    return LDA(ripl, params).computeJointKL(20, 20, verbose=True)
    #histories = productMap(parameters, runner)
    #
    #plotAsymptotics(parameters, histories, 'sweep_time', fmt='png', aggregate=True)




