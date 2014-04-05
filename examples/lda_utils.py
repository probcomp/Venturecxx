from venture.venturemagics.ip_parallel import *
from venture.venturemagics.reg_demo_utils import *
import time

def basic_mk_lda(clda=True,no_topics=5,size_vocab=20,
           alpha_t_prior='(gamma 1 1)',alpha_w_prior='(gamma 1 1)'):
    lda='''
    [assume no_topics %i]
    [assume size_vocab %i]
    [assume alpha_t %s ]
    [assume alpha_w %s ]
    [assume doc (mem (lambda (doc_ind) (make_sym_dir_mult alpha_t no_topics) ) )]
    [assume topic (mem (lambda (topic_ind) (make_sym_dir_mult alpha_w size_vocab) ) )]
    [assume word (mem (lambda (doc_ind word_ind) ( (topic ((doc doc_ind)) ) )  ) ) ]
    ''' % (no_topics,size_vocab,alpha_t_prior,alpha_w_prior)

    ulda='''
    [assume no_topics %i]
    [assume size_vocab %i]
    [assume alpha_t %s ]
    [assume alpha_w %s ]
    [assume doc (mem (lambda (doc_ind) (symmetric_dirichlet alpha_t no_topics)))]
    [assume topic (mem (lambda (topic_ind) (symmetric_dirichlet alpha_w size_vocab) ) )]
    [assume z (mem (lambda (doc_ind word_ind) (categorical (doc doc_ind)) ) ) ]
    [assume w_th (lambda (doc_ind word_ind) (categorical (topic (z doc_ind word_ind) ) ) ) ]
    
    [assume word (mem (lambda (doc_ind word_ind)
      (categorical (topic (z doc_ind word_ind) ) ) ) ) ] 
    ''' % (no_topics,size_vocab,alpha_t_prior,alpha_w_prior)
    return lda if clda else ulda


#############
def mk_lda(gen_params,collapse=False):
    '''Given "collapse" and LDA params "gen_params", generate string
       for LDA program. Does type checking for atoms and word indices checked
       to be integers. Type errors result in string outputs.'''
    no_topics=gen_params['true_no_topics']
    size_vocab=gen_params['size_vocab']
    no_docs=gen_params['no_docs']
    doc_length=gen_params['doc_length']
    alpha_t_prior=gen_params['alpha_t_prior']; alpha_w_prior=gen_params['alpha_t_prior']
    
    lda='''
    [assume no_topics %i]
    [assume size_vocab %i]
    [assume alpha_t %s ]
    [assume alpha_w %s ]
    [assume doc (mem (lambda (doc_ind) (if (is_atom doc_ind) (make_sym_dir_mult alpha_t no_topics) 
                                                              (quote not_atom) ) ))]
    [assume topic (mem (lambda (topic_ind) (if (is_atom topic_ind) (make_sym_dir_mult alpha_w size_vocab)
                                                                     (quote not_atom)) ))]
    [assume word (mem (lambda (doc_ind word_ind) (if (and (is_atom doc_ind) (not (is_atom word_ind)))
                                                       ( (topic (  (doc doc_ind) )) ) 
                                                       (quote type_error) ) ) ) ]
    ''' % (no_topics,size_vocab,alpha_t_prior,alpha_w_prior)

    ulda='''
    [assume no_topics %i]
    [assume size_vocab %i]
    [assume alpha_t %s ]
    [assume alpha_w %s ]
    [assume doc (mem (lambda (doc_ind) (if (is_atom doc_ind)
                                            (symmetric_dirichlet alpha_t no_topics)
                                            (quote not_atom))))]
    [assume topic (mem (lambda (topic_ind) (if (is_atom topic_ind) 
                                                (symmetric_dirichlet alpha_w size_vocab)
                                                (quote not_atom)) ))]
    [assume z (mem (lambda (doc_ind word_ind) (if (and (is_atom doc_ind) (not (is_atom word_ind)))
                                                    (categorical (doc doc_ind))
                                                    (quote type_error) )) ) ]
    [assume w_th (lambda (doc_ind word_ind) (if (and (is_atom doc_ind) (not (is_atom word_ind)))
                                                (categorical (topic (z doc_ind word_ind)) )
                                                (quote type_error) )) ]
    
    [assume word (mem (lambda (doc_ind word_ind) (if (and (is_atom doc_ind) (not (is_atom word_ind)))
                                                  (categorical (topic (z doc_ind word_ind)) )
                                                  (quote type_error) ) ) ) ] 
    ''' % (no_topics,size_vocab,alpha_t_prior,alpha_w_prior)
    return lda if collapse else ulda


def plot_disc(xs,clist=[],title=None):
    fig, ax = plt.subplots(len(clist),1,figsize=(15,3*len(clist)))
    width=0.3
    for i,c in enumerate(clist):
        xs=range(len(c))
        ax[i].bar(xs,c, width,label=str(i))
        ax[i].set_xticks(xs)
        ax[i].set_xticklabels( map(str,xs) )
        ax[i].legend()
        if title: ax[i].set_title(title)
    fig.tight_layout()
    return fig

def plot_docs(dlst,no_bins=20):
    fig,ax = plt.subplots(1,2,figsize=(14,4))
    xr=range(min(if_lst_flatten(dlst)),max(if_lst_flatten(dlst)))
    counts = [np.histogram(d,bins=xr,density=True) for d in dlst]
    [ax[0].hist(d,bins=no_bins,alpha=0.3,label=str(i)) for i,d in enumerate(dlst)]
    [ax[1].bar(xr,counts[i],width,label=str(i)) for i,d in enumerate(dlst)]
    [ax[i].legend() for i in [0,1]]
    return fig







####### Utility functions for LDA
def multi(dist): return np.argmax(np.random.multinomial(1,dist))
def normalize(lst):
    s=float(sum(lst))
    return [el/s for el in lst] if s>0 else 'negative sum'
ro = lambda ar: np.round(ar,2)
def mk_hist(doc,size_vocab):
    return np.array( normalize(np.bincount(doc,minlength=size_vocab)) )

is_prob_vec = lambda ar: .01 > (abs(sum(ar) - 1))

def kl(p, q):
    """KL: Sets 0 values in q to small number
    p, q : array-like, dtype=float, shape=n
        Discrete probability distributions.
    """
    p = np.asarray(p, dtype=np.float)
    q = np.asarray(q, dtype=np.float)
    if any(q==0): return '0 in q'
    return np.sum(np.where(p != 0, p * np.log(p / q), 0))

def sym_dir_mult_hist(sym_dir_mult_value):
    alpha = sym_dir_mult_value['alpha']
    counts = sym_dir_mult_value['counts']
    p_counts = np.array(counts) + alpha
    return normalize(p_counts)

def sym_dir_mult_emp_hist(v,n,sym_dir_mult_name):
    out=[v.sample('(%s)'%sym_dir_mult_name) for i in range(500)]
    return mk_hist(out,n)



def generate_docs( gen_params ):
    '''Generate a set of docs based on params. Uses Puma and uncollapsed lda
    model. Compute analytical and empirical doc_word_hists and compare
    them as a sanity check.'''
                  
    true_no_topics=gen_params['true_no_topics']
    size_vocab=gen_params['size_vocab']
    no_docs=gen_params['no_docs']
    doc_length=gen_params['doc_length']
    alpha_t_prior=gen_params['alpha_t_prior']; alpha_w_prior=gen_params['alpha_t_prior']
    
    v=mk_p_ripl()
    v.execute_program(mk_lda(gen_params,collapse=False))
                      
    alphas = [v.predict('alpha_t'),v.predict('alpha_w')]
    topics = [np.array( v.predict('(topic atom<%i>)'%topic_ind ) ) for topic_ind in range(true_no_topics) ]
    assert all([is_prob_vec(topic_simplex) for topic_simplex in topics])
    
    data_docs = [] # each entry is words for the ith doc
    ana_doc_word_hists = [] # entries are word_hists (analytical) for ith doc
    emp_doc_word_hists = [] # entires are word_hists computed from words in ith doc
    
    for doc_ind in range(no_docs):
        doc_words=[v.predict('(word atom<%i> %i)'%(doc_ind,word_ind)) for word_ind in range(doc_length)]
        data_docs.append( doc_words )
        
        doc_topics_simplex = v.predict('(doc atom<%i>)'%doc_ind)
        assert is_prob_vec(doc_topics_simplex)
        
        doc_word_hist_lst = [doc_topics_simplex[topic_ind] * topics[topic_ind] for topic_ind in range(true_no_topics) ]
        doc_word_hist = np.sum( doc_word_hist_lst , axis=0)  # CRUCIAL TO INCLUDE AXIS!!
        ana_doc_word_hists.append( doc_word_hist)
        assert is_prob_vec(doc_word_hist)
        
        # test: doc_word_hist, computed analytically, should be close to emp_doc_word_hist
        emp_doc_word_hist = mk_hist(doc_words,size_vocab)
        emp_doc_word_hists.append( emp_doc_word_hist )
        assert .1 > np.mean(abs(doc_word_hist - emp_doc_word_hist))
    
    return {'true_v':v, 'true_topics':topics, 'data_docs':data_docs, 
            'true_ana_doc_word_hists':ana_doc_word_hists, 'true_emp_doc_word_hists':emp_doc_word_hists,
            'true_alphas':alphas, 'gen_params':gen_params}

def print_summary(generate_docs_out):
    d = generate_docs_out
    print 'Summary of Data generated from LDA Prior:\n ----'
    print 'Parameters for data ', d['gen_params']; print 'true alphas: ',d['true_alphas']
    print 'First 10 probabilities of first topic',ro(d['true_topics'][0][:10])
    print 'First 10 words of each document:'
    for doc_ind,doc in enumerate( d['data_docs'] ): print 'doc %i'%doc_ind, doc[:10]



def cf_doc_hists(hist1,hist2,label1='hist1',label2='hist2'):
    fig, ax = plt.subplots(figsize=(8,3))
    width=0.27
    ax.bar(np.arange(len(hist1)), hist1, width, color='r',label=label1)
    ax.bar(np.arange(len(hist1))+width, hist2, width, color='y',label=label2)
    ax.set_title('Compare word_doc_hists:  %s and %s'%(label1,label2))
    ax.set_xticks(np.arange(len(hist1))+width)
    ax.set_xticklabels( map(str,range(len(hist1))) )
    ax.set_xlabel('Word #')
    ax.set_ylabel('Probability')
    #ax.set_ylim(0,max(doc1_counts)+10)
    ax.legend()
    
def cf_all_doc_hists(dhists1,dhists2,title1='emp',title2='ana',bar=True):
    'Convert lists of doc_word_hists to matrices, plot them with imshow and output their mean(abs(diff))'
    d1,d2 = np.array(dhists1).T, np.array(dhists2).T
    no_words = max(d1.shape); no_docs = min(d1.shape)
    fig,ax = plt.subplots( 1,2,figsize=(6,.2*no_words))
    ax[0].imshow(d1,cmap=plt.cm.gray,interpolation='nearest')
    ax[1].imshow(d2,cmap=plt.cm.gray,interpolation='nearest')
 
    [ax[i].set_xlabel('Document #') for i in [0,1] ]
    [ax[i].set_ylabel('Word #') for i in [0,1] ]
    
    [ax[i].set_xticks(np.arange(no_docs)) for i in [0,1] ]
    [ax[i].set_xticklabels( map(str,range(no_docs)) ) for i in [0,1]]
    
    ax[0].set_title(title1)
    ax[1].set_title(title2)
    
    fig.tight_layout()
     
    if bar:
        for doc_ind in range(len(dhists1)):
            cf_doc_hists(dhists1[doc_ind],dhists2[doc_ind],label1='(Doc %i, %s)'%(doc_ind,title1),
                         label2='(Doc %i, %s)'%(doc_ind,title2))


def sym_dir_mult_hist(sym_dir_mult_value):
    alpha = sym_dir_mult_value['alpha']
    counts = sym_dir_mult_value['counts']
    p_counts = np.array(counts) + alpha
    return np.array(normalize(p_counts))


def compare_inf(ripl_mripl,generate_docs_out,inf_no_topics,collapse=False,
                vunit=1, unit_topics=[], unit_docs=[]):
    '''Test input ripl against true model (given by "generate_docs_out").
       Outputs: logscore, mean/max diff of true_emp_doc_word_hist and 
       the analytical doc_word_hist of the ripl.'''
    
    # boilerplate to give shorter names to model params
    v=ripl_mripl
    true_emp_doc_word_hists = generate_docs_out['true_emp_doc_word_hists']
    true_alphas = generate_docs_out['true_alphas']
    
    gen_params = generate_docs_out['gen_params']
    true_no_topics = gen_params['true_no_topics']
    size_vocab = gen_params['size_vocab']
    no_docs = gen_params['no_docs']
    doc_length = gen_params['doc_length']
    
    # utility function for getting hist from sym_dir_mult
    def get_topic(ind):
        s = v.sample('(topic atom<%i>)'%ind )
        return sym_dir_mult_hist(s) if collapse else s
    
    def get_doc(ind):
        s = v.sample('(doc atom<%i>)'%ind )
        return sym_dir_mult_hist(s) if collapse else s
    
    # pull alphas and topics from ripl
    if not vunit: inf_alphas = np.array([v.sample('alpha_t'),v.sample('alpha_w')])
    if vunit:
        topics = [sym_dir_mult_hist(val) for val in unit_topics]
    else: 
        topics = [np.array( get_topic(topic_ind) ) for topic_ind in range(inf_no_topics) ]
    assert all([is_prob_vec(topic_simplex) for topic_simplex in topics])
    
    
    # pull analytical and empirical doc_word_hists from ripl
    
    inf_ana_doc_word_hists = [] # entries are word_hists (analytical) for ith doc
    inf_emp_doc_word_hists = [] # entires are word_hists computed from words in ith doc
    
    for doc_ind in range(no_docs):
        
        if vunit:
            doc_topics_simplex = sym_dir_mult_hist(unit_docs[doc_ind])
        else:
            doc_topics_simplex = get_doc(doc_ind)
        assert is_prob_vec(doc_topics_simplex)
        
        #print 'topic: ',[topics[topic_ind] for topic_ind in range(inf_no_topics)]
        doc_word_hist_lst = [doc_topics_simplex[topic_ind] * topics[topic_ind] for topic_ind in range(inf_no_topics) ]
        doc_word_hist = np.sum( doc_word_hist_lst , axis=0)  # CRUCIAL TO INCLUDE AXIS!!
        inf_ana_doc_word_hists.append(doc_word_hist)
        assert is_prob_vec(doc_word_hist)
        
        # sanity check that our pulling params from inference is correct (can be skipped)
        # FIXME we will have to change doc_length+1 to max(doc_length)+1 if doc_lenght varies
        # SKIPPING FOR SPEED
        
        #emp_doc_word_hist_words =[v.sample('(word atom<%i> %i)'%(doc_ind,doc_length+1)) for rep in range(100)]
        #emp_doc_word_hist = mk_hist(emp_doc_word_hist_words,size_vocab)
        #inf_emp_doc_word_hists.append( emp_doc_word_hist )
        #assert .1 > np.mean(abs(doc_word_hist - emp_doc_word_hist))
        
        
    # diagnostics for inference ripl vs. true data statistics
    if not vunit: logscore = v.get_global_logscore()
    diff_doc_word_hist = np.abs(np.array(true_emp_doc_word_hists) - np.array(inf_ana_doc_word_hists))
    mean_diff_doc_word_hist = np.mean(diff_doc_word_hist)
    max_diff_doc_word_hist = np.max(diff_doc_word_hist)
    
    mean_diff_hist_lst=lambda lst1,lst2: np.mean(np.abs(np.array(lst1)-np.array(lst2)))
    mean_kl_hist_lst=lambda lst1,lst2: np.mean( [kl(h1,h2) for h1,h2 in zip(lst1,lst2) ] )
                                          
    uni_hist_lst=[np.array( [1./size_vocab]*size_vocab ) for doc_ind in range(no_docs) ]
    rand_hist_lst = [np.random.dirichlet(np.ones(size_vocab)) for doc_ind in range(no_docs) ]
    
    mean_diff_doc_word_hist = mean_diff_hist_lst(true_emp_doc_word_hists,inf_ana_doc_word_hists)
    true_uni_diff = mean_diff_hist_lst(true_emp_doc_word_hists,uni_hist_lst)
    true_rand_diff = mean_diff_hist_lst(true_emp_doc_word_hists,rand_hist_lst)
    
    mean_kl = mean_kl_hist_lst(true_emp_doc_word_hists,inf_ana_doc_word_hists)
    true_uni_kl = mean_kl_hist_lst(true_emp_doc_word_hists,uni_hist_lst)
    true_rand_kl = mean_kl_hist_lst(true_emp_doc_word_hists,rand_hist_lst)
    
    kls=[]
    for t_hist,i_hist in zip(true_emp_doc_word_hists,inf_ana_doc_word_hists):
        kls.append( kl(t_hist,i_hist) )
    
    if not vunit: 
        mean_diff_alphas = np.mean(np.abs(inf_alphas - true_alphas))
    else:
        mean_diff_alphas = 'na'
        logscore = 'na'
        
    
    return {'logscore':logscore, 
            'mean/max_diff_doc_word_hist':(mean_diff_doc_word_hist,max_diff_doc_word_hist),
            'mean diff: (inf,uni,rand)':(mean_diff_doc_word_hist,true_uni_diff,true_rand_diff),
            'mean_diff_alphas':mean_diff_alphas,
            'kls':kls,
            'mean kl: (inf,uni,rand)':(mean_kl,true_uni_kl,true_rand_kl),
            'inf_ana_doc_word_hists':inf_ana_doc_word_hists}
