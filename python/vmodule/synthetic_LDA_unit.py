from venture import shortcuts
from venture.vmodule.venture_unit import *


class LDA(VentureUnit):
    def makeAssumes(self):
        self.assume("topics", self.parameters['topics'])
        self.assume("vocab", self.parameters['vocab'])
        self.assume("alpha_document_topic", "(gamma 1.0 1.0)")
        self.assume("alpha_topic_word", "(gamma 1.0 1.0)")
        self.assume("get_document_topic_sampler", "(mem (lambda (doc) (make_sym_dir_mult alpha_document_topic topics)))")
        self.assume("get_topic_word_sampler", "(mem (lambda (topic) (make_sym_dir_mult alpha_topic_word vocab)))")
        self.assume("get_word", "(mem (lambda (doc pos) ((get_topic_word_sampler ((get_document_topic_sampler doc))))))")
        return


    def makeObserves(self):
        D = self.parameters['documents']
        N = self.parameters['words_per_document']
        for doc in range(D):
            for pos in range(N):
                self.observe("(get_word %d %d)" % (doc, pos), "atom<%d>" % 0)
        return


if __name__ == '__main__':
    ripl = shortcuts.make_church_prime_ripl()
    parameters = {'topics' : 4, 'vocab' : 10, 'documents' : 8, 'words_per_document' : 12}

    #model = LDA(ripl, parameters)
    #history = model.runConditionedFromPrior(50, verbose=True)
    #history = model.runFromJoint(50, verbose=True)
    #history = model.sampleFromJoint(20, verbose=True)
    #history = model.computeJointKL(200, 200, verbose=True)[2]
    #history = model.runFromConditional(50)
    #history.plot(fmt='png')
    
    parameters = {'topics' : [4, 8], 'vocab' : 10, 'documents' : [8, 12], 'words_per_document' : [10, 100]}
    def runner(params):
        return LDA(ripl, params).computeJointKL(20, 20, verbose=True)
    histories = produceHistories(parameters, runner)
    separate_histories = lambda (key, value): [(key, value_i) for value_i in value]
    sampledHistory, inferredHistory, klHistory = map(dict, zip(*map(separate_histories, histories.iteritems())))
    for history_type in [sampledHistory, inferredHistory, klHistory]:
        for key, history in history_type.iteritems():
            history.plot(fmt='png')
    
    # plotAsymptotics(parameters, histories, 'sweep_time', fmt='png', aggregate=True)
