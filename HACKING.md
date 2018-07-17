Overview
========

If you disagree with a suggestion you see here, please bring it up
rather than silently not following it.

- We use [Github Issues](http://github.com/probcomp/Venturecxx/Issues/) to track issues.

- We use [Slack](https://probcomp.slack.com/) for persistent group chat.

- We use [nosetests](https://nose.readthedocs.org/en/latest/) for running the test suite.

- We have a compute cluster at `probcomp-{1,2,3,4}.csail.mit.edu`, and we have EC2 as a fallback.

- We use [Jenkins](http://jenkins-ci.org/) for the continuous build.
  As of this writing, the server listens to
  https://probcomp-4.csail.mit.edu/.  Note in particular the
  `venture-master-crashes` build.

- We use [pylint](http://www.pylint.org/) to maintain our Python code style.  The normative
  pylint configuration files are `tool/pylintrc-<version>`.  See also [pylint](#pylint).

- We have a [Testing Policy](#testing-policy).

- We have a [Contributor Policy](#contributor-policy) for non-core developers.

Particulars
===========

Issue Metadata
--------------

- **Assigned** means you're imminently working on it. You preferably
  have <= 3 bugs assigned.

- **Milestones** indicate the most imminent external deliverable that
  a given issue is needed for.  Issues with no milestone attached are
  considered untraiged in this sense.

- For everything else, there are labels:

- **Disposition** [grays]: "no/wontfix/obsolete/etc." and "duplicate".
  All issues that are closed and not labeled with a disposition are
  assumed to be done as suggested in some sense.  The particular
  sub-disposition should be clear from the notes.

- **Effort** [greens]: "k hours", "k days" -- how long you imagine it
  might take.

- **Blockage** [reds]:

  - _"blocked"_: some other bug (mentioned) logically comes before
    this. There may be a workaround, or this may be doable with
    technical debt even without the other bug, but that order would be
    better.

  - _"needs decision"_: blocked not on software, but on a human
    decision. These should be super high priority.

  - _"help wanted"_: use especially for projects that an incoming
    person might be able to take up. Take care to describe how to get
    started well enough so such a person might even want to.

  - _"waiting"_: (cookie licked) you have a change in progress in some
    client, or on some branch, but you consider it unfinished. Write
    down enough context about what's left so that someone else could
    potentially pick it up, and do push your branch! But this is for
    bugs you intend to come back to.

- **Reason** [blues]: Why do we want to do this?  They are mostly
  self-explanatory, in the context of the following model of
  capability creation:

  - _proof of concept_ is the minimum needed to conclude that a
    capability is implementable, and give a frame for how it might
    integrate into the system.

  - _acquisition_ is the minimum needed to be able to show a
    capability deployed in the system, that looks integrated.  A demo
    at this level is permitted to have very large gaps that require a
    trained demo operator to avoid.  Contrast with

  - _completion_ is the work it takes to actually be able to offer the
    capability to a user who wants to get something out of it.  A
    completed capability is expected to interoperate in natural ways
    with all the system's other capabilities, but may be buggy.

  - _fixing bugs_ is about eliminating known problems with
    capabilities or their interactions, generally to be viewed in the
    context of completed capabilities.

  - _testing_ is about preemptively detecting such problems before
    users do (and preventing them from arising under further software
    evolution).


Testing Policy
--------------

- `nosetests -c crashes.cfg` runs the suite to quickly check for
  crashes without measuring inference quality.  Please keep this test
  suite passing on the master branch; raise `nose.SkipTest` if
  necessary.

    - `nosetests -c lite-crashes.cfg` runs only the tests that test
      the Lite backend

    - `nosetests -c puma-crashes.cfg` runs only the tests that test
      the Puma backend

    - `nosetests -c crashes.cfg --tc=get_ripl:lite` runs all the
      tests, using the Lite backend where not specified in the test.
      `puma` likewise.

- We treat a skipped test as an issue.  To wit, resolution is required
  but need not be immediate.  The actual skipped test should ideally
  be linked to an issue in the issue tracker. [*] When that issue is
  closed, the test should be re-enabled.  Issues that have skipped
  tests associated with them should ideally be marked as such, so the
  tests can be found (by grep) and turned back on.

  [*] Typically by copying the issue's URL into the message given to
  the SkipTest exception.

- See [test/README.md](https://github.com/probcomp/Venturecxx/tree/master/test)
  for the organization of the test suite.

Test Suite Configuration
------------------------

- `all-crashes` checks for crashes in several generic inference programs.

- `nosetests -c inference-quality.cfg` checks for inference quality
  problems.

- You can select the default inference program (used when the
  particular test doesn't specify) like this:
  `nosetests -c inference-quality.cfg --tc=infer:"(func_pgibbs default ordered 10 3)"`
  The default is `(resimulation_mh default one 100)`.

- `all-inference-quality` checks inference quality in several generic
  inference programs.  This takes a while.

- `nosetests -c performance.cfg` checks for performance issues.
  Currently there are only a handful of performance tests, all of
  which are asymptotic checks rather than benchmarks.

- The test suite can be sliced by test/group in the usual way.

- See `test/lite-config.py` and `test/config.py` for other configuration
  options.

- Python-side code coverage can be obtained via coverage.py and the
  nose-cov plugin.  A coverage report is generated by default when doing
  crash testing.  Read `crashes.cfg` to see how it's done.

- Ideally, we would define additional task-oriented test launch patterns:
  - Benchmark an inference program in a backend
    - speed per transition
    - convergence per transition
    - convergence per computron
  - Profile the computations triggered by the tests (statistically or by instrumentation)
  - Issue: https://app.asana.com/0/9277419963067/10442847514621

Pylint
------

We use pylint to maintain a Python code style.  The normative style
files are `tool/pylintrc-<version>`.  A number of existing style
violations are grandfathered, but we try not to introduce new ones.

- Pylint message exclusion lists are not forward or backward
  compatible, so we maintain separate style files for each of the
  Pylint versions that people use.

- You can run pylint in batch mode using the Venture style with, e.g.,
  `pylint --rcfile=tool/pylintrc-<version> backend/lite/wttree.py`
  where `<version>` is your Pylint version number, like 1.5.1.

- Pylint is more useful if the feedback is instantaneous.  If you edit
    in Emacs, this can be achieved using Flymake Mode:

    1. Either add the `tool/` directory to your PATH, or put a symlink
       on your path named `venture-epylint.py` and pointing to
       `tool/venture-epylint.py`

    2. Make sure your Emacs loads `tool/python-flymake.el` on startup,
       for example by adding `(load-file "/path/to/venture/tool/python-flymake.el")`
       to your `.emacs` file.

- Our attitude towards style violations is:

  - Code you recently understood (i.e., wrote, or heavily modified)
    should conform to the project style.
  - If there is a good reason to deviate from style, add a comment
    with `pylint: disable=<violation-type>` and a comment explaining
    why.
  - If you feel that a particular style constraint is too strict or
    inappropriate in general, let's discuss it.

Debugging C++ in GDB
--------------------

One way to run the Puma backend through Python under GDB is to create
a file named `Venturecxx/.gdbinit` with content like

```
target exec python
run /usr/bin/nosetests [params]
```

In order for this to work, it may be necessary to add a line like

```
add-auto-load-safe-path /home/axch/work/pcp/Venturecxx/.gdbinit
```

to one's `~/.gdbinit`.  With that ready, just run `gdb`.

Checking C++ with Valgrind
--------------------------

We have a Valgrind suppressions file for problems that are (apparently)
caused by Python rather than our code: `backend/new_cxx/valgrind-python.supp`.

Check out the `tool/grind` script for an example of how to use it.

Contributor Policy
==================

We have a process for contributions by non-core developers, since our
research group includes several students and junior programmers.

_If you are not a research engineer with ProbComp_, we ask that you
follow this process for contributions to `Venturecxx`.

Summary
-------

- Either fork the repo on Github (please keep the fork private) or
  work on your own branch.  _Do not push to master without review._

- Make sure there are tests covering your work

- When ready:

  - Merge master into your branch and resolve conflicts

  - Run the [crash test suite](#testing-policy) and make sure it
    passes.

  - Make sure your code does not introduce new [style](#pylint)
    violations.

  - Push your branch and ask for a review (e.g. by creating a pull
    request).

- Keep an eye on [Jenkins](https://probcomp-4.csail.mit.edu/) after
  being merged

Fuller Guide
------------

- You should have basic familiarity with [git](http://git-scm.com/),
  our source code control system, and willingness to learn relevant
  other third-party tools we use.

- Create a git branch for the thing you are doing (feel free to prefix
  with your name or initials)

- Work on that branch with whatever workflow suits you best

    - I personally like many small commits, each containing one
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

    - Run the [crash test suite](#testing-policy) and make sure it
      passes.

    - Run [pylint](#pylint) if you haven't been, and make sure your
      code does not introduce new style violations.

    - Push your branch, and send an email to an appropriate core Venture
      developer asking for a code review.  Be sure to include the name
      of the branch.

- Depending on the size of your contribution, there may be a cycle of
  reviews, comments, updates, and repeated reviews.  This is normal, and
  helps us maintain the quality of our software.  Eventually, a core
  developer will merge your branch into master.

- After your contribution is merged, it's good to monitor
  [Jenkins](https://probcomp-4.csail.mit.edu/) a
  bit, because the testing it's doing is likely to be more thorough
  than yours, and it may be running in a different environment.  If
  the venture-crashes build fails, we will be after you to produce a
  fix.  See also the [organization of the continuous
  build](test/README.md#jenkins-continuous-build).
