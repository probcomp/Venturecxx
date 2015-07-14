#!/usr/bin/env python

# Copyright (c) 2015 Alexey Radul.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''Ensure presence, format, and years of FSF-style copyright headers.

Library usage: copyright.process_file(fname, Corrector, [comment_syntax_override])
ensures that a copyright header as specified by the corrector (a
subclass of CopyCorrector, below) is present in the file, with
copyright years aligned with the opinions of 'git blame'.

- If this cannot be confirmed, prints a warning to standard output.

- If a header is observably missing, prints a warning to standard
  output and adds one (after a shebang line, if any).

- If a header of the proper form is present but with poor whitespace
  or copyright years, prints a warning to standard output and corrects
  it.

The assumptions about the syntax of comments in the file may (to a
point) be changed by providing an argument for the
'comment_syntax_override' position.  See 'process_file'.

Command line usage: copyright.py filename
does the above, assuming copyright belongs to Alexey Radul and the
proper license is GPLv3.  Configuration is by writing your own
executable using 'copyright' as a library.

'''

import subprocess as s
import os
import sys
import re
from contextlib import contextmanager

def process_file(fname, Corrector, comment_syntax_override=lambda fname: None):
  '''Ensure presence, format, and years of an FSF-style copyright header.

The 'fname' argument is the path (relative to process working directory)
of the file to process.

The 'Corrector' argument must be a subclass of 'CopyCorrector', which see.
This is how the expected header format is customized.  The CopyCorrector
class assumes copyright belongs to Alexey Radul and the license is GPL v3.

The comment_syntax_override argument, if present, configures the
comment style to be expected and enforced for the file.  If absent, a
default based on common file extensions is used.

Specifically: comment_syntax_override, if provided, must be a
callable, which will be called with the filename of the file to be
processed.  The callable should return a 2-tuple:

- the first component should be a regular expression recognizing valid
  comment lines, with a group select the non-comment portion of the
  syntax; and
- the second component should be a prefix string which produces a
  valid line comment.

The callable may also return 'None' to decline to specify a comment
syntax override, in which case the default extension-based comment
syntax will be used.

You may find it convenient to use 'repeated_character_comment_syntax'
to make such tuples.

A recommendation: make any spaces separating the comment characters
from the actual copyright notice part of the notice rather than part
of the comment syntax.  That way, you can have blank lines in the
notice with or without leaving trailing spaces on them.  The default
comment syntaxes obey this convention.

  '''
  comments = comment_syntax_override(fname)
  if comments is None:
    comments = _comment_syntax(fname)
  if comments is None:
    # Initially, assume unknown comment syntax
    print "Unknown comment syntax", fname
  elif comments == "skip":
    print "Skipping", fname
  else:
    (detect_comments, make_comments) = comments
    with open(fname) as f:
      lines = f.readlines()
    parse = CopyParser(detect_comments).parse(lines)
    correct = Corrector(parse)
    if parse.no_header():
      if any("opyright" in l for l in lines):
        print "Misparsed header", fname
      else:
        print "CHANGE by inserting copyright header", fname
        with open(fname, "w") as fw:
          yearstring = correct.proper_year_string(fname)
          parse.write_better(fw, correct.proper_header(make_comments, yearstring))
    elif correct.header_present():
      yearstring = correct.proper_year_string(fname)
      desired = correct.proper_header(make_comments, yearstring)
      if desired == parse.raw_header():
        pass
      else:
        print "CHANGE by correcting copyright header", fname
        with open(fname, "w") as fw:
          parse.write_better(fw, desired)
    else:
      # This requires attention
      print "Other header  ", fname


def repeated_character_comment_syntax(char, min_count, preferred_count):
  '''A comment syntax consisting of some number of required and desired repetitions of a single character.

- The comment recognizer is ^char{min_count,}(.*)$
- The comment prefix is char * preferred_count

This admits for example Scheme syntax, where a single ; character
suffices to begin a valid line comment, but copyright headers are
usually prefixed with ;;;

  '''
  detect = re.compile("^" + char * (min_count-1) + char + "+(.*)$")
  emit = char * preferred_count
  return (detect, emit)

# TODO css comments are all block (with /* */)
# TODO c, cxx, h, hpp, js admit block comments
# TODO html and xml comments are bizarre
def _comment_syntax(filename):
  (_, extension) = os.path.splitext(filename)
  if extension in [".conf", ".ipy", ".py", ".sh"]:
    return repeated_character_comment_syntax('#', 1, 1)
  elif extension in [".el", ".scm"]:
    return repeated_character_comment_syntax(';', 1, 3)
  elif extension in [".c", ".cxx", ".h", ".hpp", ".js"]:
    return repeated_character_comment_syntax('/', 2, 2)
  elif extension in [".elm"]:
    return repeated_character_comment_syntax('-', 2, 2)
  elif extension in [".png", ".jpg", ".gif"]:
    return "skip"
  return None


class CopyCorrector(object):
  '''The definition of the desired copyright header.

The 'copyright' module is intended to be customized by passing an
instance of a subclass of this class as the second argument to
'process_file'.  The four methods that are intended to be overridden
by a subclass are

- claim_regex,
- claim_format,
- notice, and
- default_default_year

For greater flexibility, you may instead or in addition wish to
override any of

- claim_present,
- notice_present,
- header_present, or
- claimed_years.

For even greater flexibility, read the source and do what you want.
  '''
  def __init__(self, parser):
    self.parser = parser

  def claim_regex(self):
    '''Return a regular expression for the copyright claim.

Should match the intended "Copyright years entity" line of a copyright
header, without any leading or trailing comment or space characters.
Group 1 should select the copyright years as a string, without leading
or trailing whitespace.

Default: ^Copyright \(c\) ([-0-9 ,]+) Alexey Radul\.$

    '''
    return r'^Copyright \(c\) ([-0-9 ,]+) Alexey Radul\.$'

  def claim_format(self):
    '''Return a format string suitable for constructing the proper copyright claim.

Should be a valid format string for a single string argument, which
will be the years that the file is copyright, without leading or
trailing spaces.

Default: ' Copyright (c) %s Alexey Radul.'

(the leading space is there because the default comment syntaxes do
not add spaces between the comment characters and the text, so that
the header may have blank lines with or without trailing whitespace).

    '''
    return r' Copyright (c) %s Alexey Radul.'

  def notice(self):
    '''Return the desired license notice as a string.

Recommendation: include a leading space in each line with text,
because the standard comment syntaxes do not insert it (to permit
blank lines with or without trailing whitespace).

Default: the one-file-program notice for GPL v3.

    '''
    return """\
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>."""

  def default_default_year(self):
    '''Default default year(s) for which to claim copyright, as a string.

This is used for a file that has no 'git blame' information to deduce
years from, and no existing copyright header to blindly propagate
years from, such as __init__.py files.

Default: "2015"
'''
    return "2015"

  def claim_present(self):

    '''Compute whether the copyright claim is present.'''
    return re.match(self.claim_regex(), self.parser.claim_text())

  def notice_present(self):
    '''Compute whether the license notice is present.'''
    return self.notice_text() == self.parser.notice_text()

  def header_present(self):
    '''Compute whether the full copyright header is present.'''
    return self.claim_present() and self.notice_present()

  def claimed_years(self):
    '''Compute the years for which copyright is claimed in the header,
as a string.

This is used only for a file that has no content other than the
copyright header itself, so the proper years cannot be deduced from
'git blame' output, for example __init__.py files.

This may return 'None', perhaps for a file that does not have a
header either, in which case the default default year is used.

    '''
    m = re.match(self.claim_regex(), self.parser.claim_text())
    if m is not None:
      return m.group(1)
    else:
      return None

  def notice_text(self):
    return ' '.join(self.notice().split())

  def proper_year_string(self, filename):
    skip = self.parser.header_offset() + 1  # + 1 to correct a fencepost discrepancy againt tail
    # From /home/axch/bin/git-contrib-years
    cmd = """git blame -f -e --date short -M -C -C -- '%s' | tail -n +%d | tr -s ' ' | cut -d ' ' -f 4 | cut -d '-' -f 1 | sort -u""" % (filename, skip)
    result = s.Popen(cmd, shell=True, stdout=s.PIPE).stdout.read()
    if len(result.strip()) == 0:
      # The file has no content other than the copright header, e.g. __init__.py
      # Use the existing year(s).
      years = self.claimed_years()
      if years is None:
        return self.default_default_year()
      else:
        return years
    else:
      years = [int(st) for st in result.strip().split("\n")]
      return ", ".join([str(y) for y in years])

  def proper_header(self, comment_prefix, year_string):
    claim = self.claim_format() % year_string
    header = claim + "\n\n" + self.notice()
    return "\n".join(comment_prefix + l for l in header.split("\n")) + "\n"


class CopyParser(object):
  '''Parse FSF-multifile-style copyright and license headers.

Usage: CopyParser(<comment-line-regex>).parse(<line-list>) returns a
complete CopyParser object whose other methods give access to a
decomposition of the text in the line list (presumed derived from
f.readlines()) into a preamble, a copyright claim, a license notice,
and content.

  '''
  def __init__(self, detect_comments):
    self._preamble = []
    self._claim = []
    self._notice = []
    self._content = []
    self.comment_regex = detect_comments

  def preamble(self, line):
    assert len(self._claim) == 0
    self._preamble.append(line)

  def claim(self, line):
    assert len(self._notice) == 0
    self._claim.append(line)

  def notice(self, line):
    assert len(self._content) == 0
    self._notice.append(line)

  def content(self, line):
    self._content.append(line)

  def parse(self, lines):
    # Manual trampoline because Guido does not understand tail recursion
    cont = (self._preamble_or_claim_or_end, (0, lines))
    while cont is not None:
      cont = cont[0](*cont[1])
    self._clean_up()
    return self

  # Invariant of the parsing functions:
  # All control paths EITHER
  # - Stop at the end of the given lines list without changing the state, OR
  # - Call another parsing function with the same index without changing the state, OR
  # - BOTH
  #   - Append the current line to exactly one of the result lists, AND
  #   - Call a parsing function with the index increased by 1, OR
  # - Slice the rest of the lines into the _content list
  #
  # Therefore, the union of the lines in the result lists is the full
  # set of lines, and each result list contains its lines in order.
  #
  # Furthermore, since appending can only be done in the order
  # "preamble", "claim", "notice", "content", we will have
  # self._preamble + self._claim + self._notice + self._content = lines

  def _preamble_or_claim_or_end(self, index, lines):
    if index == len(lines):
      # End of file
      return None
    else:
      with self._non_comment_portion(index, lines) as (line, line_text):
        if line_text is not None:
          # A line comment
          if line_text.startswith("Copyright"):
            # The copyright claim line
            self.claim(line)
            return (self._claim_or_notice_or_end, (index+1, lines))
          else:
            self.preamble(line)
            return (self._preamble_or_claim_or_end, (index+1, lines))
        else:
          # Not a line comment
          self.preamble(line)
          return (self._preamble_or_claim_or_end, (index+1, lines))

  def _claim_or_notice_or_end(self, index, lines):
    if index == len(lines):
      # End of file
      return None
    else:
      with self._non_comment_portion(index, lines) as (line, line_text):
        if line_text is not None:
          # A line comment
          if line_text.startswith("This file is part of"):
            # Beginning of notice
            self.notice(line)
            return (self._notice_or_content_or_end, (index+1, lines))
          else:
            # Continuation of copyright claim, presumably
            self.claim(line)
            return (self._claim_or_notice_or_end, (index+1, lines))
        else:
          # Not a line comment
          if len(line.strip()) == 0:
            # A blank line; may be part of the claim
            self.claim(line)
            return (self._claim_or_notice_or_end, (index+1, lines))
          else:
            # Content; disallow subsequent claim or notice lines
            return (self._content_or_end, (index, lines))

  def _notice_or_content_or_end(self, index, lines):
    if index == len(lines):
      # End of file
      return None
    else:
      with self._non_comment_portion(index, lines) as (line, line_text):
        if line_text is not None:
          # A line comment
          if "http://www.gnu.org/licenses" in line_text:
            # Last part of notice
            self.notice(line)
            return (self._content_or_end, (index+1, lines))
          else:
            self.notice(line)
            return (self._notice_or_content_or_end, (index+1, lines))
        else:
          # Not a line comment
          if len(line.strip()) == 0:
            # A blank line; may be part of the notice
            self.notice(line)
            return (self._notice_or_content_or_end, (index+1, lines))
          else:
            # Content
            return (self._content_or_end, (index, lines))

  def _content_or_end(self, index, lines):
    self._content.extend(lines[index:])
    return None

  @contextmanager
  def _non_comment_portion(self, index, lines):
    line = lines[index]
    m = re.match(self.comment_regex, line)
    if m is not None:
      # A line comment
      line_text = m.group(1).strip()
      yield (line, line_text)
    else:
      yield (line, None)

  def _clean_up(self):
    if len(self._claim) == 0 and len(self._notice) == 0:
      # There was no header, so I was probably too aggressive about the preamble
      self._content = self._preamble + self._content
      self._preamble = []
      if len(self._content) > 0 and len(self._content[0]) >= 2 and self._content[0].startswith("#!"):
        # Shebang lines are in the preamble
        self._preamble.append(self._content[0])
        self._content = self._content[1:]

  def _text_of(self, string):
    no_comment = [re.sub(self.comment_regex, r'\1', line) for line in string]
    return ' '.join(' '.join(no_comment).split())

  def claim_text(self): return self._text_of(self._claim)
  def notice_text(self): return self._text_of(self._notice)

  def no_header(self):
    return len(self._claim) == 0 and len(self._notice) == 0

  def header_offset(self):
    ans = len(self._preamble) + len(self._claim) + len(self._notice)
    if len(self._content) > 0 and len(self._content[0].strip()) == 0:
      # Blank line may have been inserted by running this script
      return ans + 1
    else:
      return ans

  def raw_header(self):
    return "".join(self._claim + self._notice)

  def write_better(self, fw, desired_header):
    for l in self._preamble:
      fw.write(l)
    if len(self._preamble) > 0 and len(self._preamble[-1].strip()) > 0:
      # Preamble ended in a non-blank line
      fw.write("\n")
    fw.write(desired_header)
    if len(self._content) > 0 and len(self._content[0].strip()) > 0:
      # Content started in a non-blank line
      fw.write("\n")
    for l in self._content:
      fw.write(l)

if __name__ == "__main__":
  process_file(sys.argv[1], CopyCorrector)
