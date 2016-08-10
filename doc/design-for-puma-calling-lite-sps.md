Puma calling Lite SPs
Notes circa mid-late 2014
Status: Implemented

Getting Lite SPs to be usable from Puma traces should be pretty
straightforward (if tedious and time-consuming).
- Sacrifice the goat that boost::python needs sacrificed to get a view
  in Puma on a Lite-style VentureSP object
  - This will presumably need to be passed boost::python objects to
    its methods in order to work
- Define an appropriate wrapper class called something like LiteSP
  that uses the puma_value_to_lite_value abstraction to create values
  that the Lite SP can consume
  - This may necessitate a Python-side wrapper too, like
    SPInvokableFromPuma (which is not a VentureValue because Lite
    presumably can't invoke such an SP) (maybe the methods take stack
    dicts and transform them to VentureValues?)
- Translate the Args struct that SP methods accept as arguments by
  stubbing out most of it -- just translate the values, and let the
  thing crash if somebody wants to use from Puma a Lite SP that needs
  to read the environment, or any nodes, or anything like that.  This
  can be improved later.
- Can expose this facility by making engine.bind_foreign_sp (which
  accepts a Lite SP object) work on Puma traces too.

Getting Puma SPs to be usable from Lite traces should be similar
(though I don't know how reusable the tedium would be).  My
suggestion: go from Lite SPs to Puma SPs first, and then see whether
the other way becomes obvious.
- N.B.: We need a mechanism for binding user-written Puma SPs into
  Venture anyway, by analogy with engine.bind_foreign_sp.  How are
  such things structured?
