DRAFT Non-core Venture contributor guide
========================================

Instead of Github's pull request feature, we are currently giving
contributors push access to the main repository, with the expectation
that they will work on branches, which will be merged to master after
code review.

This guide assumes basic familiarity with [git](http://git-scm.com/),
our source code control system, and willingness to learn relevant
other third-party tools we use.

Workflow for a contribution
---------------------------

- Create a git branch for the thing you are doing (feel free to prefix
  with your name or initials)
- Work on that branch with whatever workflow suits you best
    - I presonally like many small commits, each containing one
      "semantic change"
    - I am not strict about keeping the test suite passing on every
      commit on a branch, because sometimes my semantic changes are
      exploratory.
    - If the branch is long-running, we recommend merging master into
      it from time to time.
    - Push early, push often.  That makes it possible to ask for help
      on things, talk about design choices or tactics, etc.
    - Do not merge your branch into master without code review.
- When you are ready to have your contribution included in the
  main development Venture, we will need to code review it.
    - Feel free to look it over and review it yourself first.  Is there
      anything you know will confuse the reviewer?  Now is a good time
      to fix or clarify it.
    - If you are adding new functionality, add sufficient tests to
      exercise it reasonably thoroughly (we can help you with this).
      See the description of the [test suite organization](test/README.md).
    - If you are fixing a bug, add a regression test that fails if the
      bug is not fixed and passes when it is.
    - Merge master into your branch and resolve any conflicts.
    - Run the [crash test suite](core-dev-style-guide.md#testing-policy)
      and make sure it passes.
      TODO Refer to multiple run modes, explanation of that
    - Run [pylint](core-dev-style-guide.md#pylint) if you haven't
      been, and make sure your code does not introduce new style
      violations.
    - Push your branch, and send an email to an appropriate core Venture
      developer asking for a code review.  Be sure to include the name
      of the branch.
- Depending on the size of your contribution, there may be a cycle of
  reviews, comments, updates, and repeated reviews.  This is normal, and
  helps us maintain the quality of our software.  Eventually, a core
  developer will merge your branch into master.
- After your contribution is merged, it's good to monitor
  [Jenkins](http://ec2-54-84-30-252.compute-1.amazonaws.com:8080/) a
  bit, because the testing it's doing is likely to be more thorough
  than yours, and it may be running in a different environment.  If
  the venture-crashes build fails, we will be after you to produce a
  fix.  See also the [organization of the continuous
  build](test/README.md#jenkins-continuous-build).
