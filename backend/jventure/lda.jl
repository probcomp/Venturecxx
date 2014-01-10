require("engine.jl")

function runLDA(N,topics,vocab,documents,wordsPerDocument)
  sivm = Engine()
  assume(sivm,"topics",string(topics))
  assume(sivm,"vocab", string(vocab))
  assume(sivm,"alpha_document_topic","(gamma 0.1 0.1)")
  assume(sivm,"alpha_topic_word", "(gamma 0.1 0.1)")
  assume(sivm,"get_document_topic_sampler", "(mem (lambda (doc) (make_sym_dir_mult alpha_document_topic topics)))")
  assume(sivm,"get_topic_word_sampler", "(mem (lambda (topic) (make_sym_dir_mult alpha_topic_word vocab)))")
  assume(sivm,"get_word", "(lambda (doc) ((get_topic_word_sampler ((get_document_topic_sampler doc))))))")
  
  for doc = 1:documents
    for pos = 1:wordsPerDocument
      observe(sivm,string("(get_word ",doc,")"), doc)
    end
  end

  infer(sivm.trace,N)
  for doc = 1:documents
    println(string("Expected: ",doc))
    println("Observed: ")
    for i = 1:100
      (_,value) = predict(sivm,string("(get_word ",doc,")"))
      print(value)
      print(" ")
    end
    println("")
  end

end
