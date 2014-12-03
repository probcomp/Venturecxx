# -*- Python -*-

# Driver template for the LEMON parser generator.
# The author disclaims copyright to this source code.


# First off, define the token values.  These constants (all generated
# automatically by the parser generator) specify the various kinds of
# tokens (terminals) that the parser understands.
#
# Each symbol here is a terminal symbol in the grammar.

L_NAME                         =  1
T_COLON                        =  2
T_LSQUARE                      =  3
T_RSQUARE                      =  4
K_DEFINE                       =  5
K_ASSUME                       =  6
K_OBSERVE                      =  7
K_PREDICT                      =  8
K_CONFIGURE                    =  9
K_FORGET                       = 10
K_REPORT                       = 11
K_INFER                        = 12
K_CLEAR                        = 13
K_ROLLBACK                     = 14
K_LIST_DIRECTIVES              = 15
K_GET_DIRECTIVE                = 16
K_FORCE                        = 17
K_SAMPLE                       = 18
K_CONTINUOUS_INFERENCE_STATUS  = 19
K_START_CONTINUOUS_INFERENCE   = 20
K_STOP_CONTINUOUS_INFERENCE    = 21
K_GET_CURRENT_EXCEPTION        = 22
K_GET_STATE                    = 23
K_GET_LOGSCORE                 = 24
K_GET_GLOBAL_LOGSCORE          = 25
K_PROFILER_CONFIGURE           = 26
K_PROFILER_CLEAR               = 27
K_PROFILER_LIST_RANDOM         = 28
K_CHOICES                      = 29
K_LOAD                         = 30
L_INTEGER                      = 31
L_OPERATOR                     = 32
T_LROUND                       = 33
T_RROUND                       = 34
T_TRUE                         = 35
T_FALSE                        = 36
L_REAL                         = 37
T_LANGLE                       = 38
T_RANGLE                       = 39
L_STRING                       = 40
T_COMMA                        = 41
T_LCURLY                       = 42
T_RCURLY                       = 43

# The state of the parser is completely contained in an instance of
# the following class.

class Parser(object):

    # defaults
    YYERRORSYMBOL = None
    YYWILDCARD = None

    # The next thing included is series of definitions which control
    # various aspects of the generated parser.
    #    YYNOCODE           is a number which corresponds
    #                       to no legal terminal or nonterminal number.  This
    #                       number is used to fill in empty slots of the hash 
    #                       table.
    #    YYNSTATE           the combined number of states.
    #    YYNRULE            the number of rules in the grammar
    #    YYERRORSYMBOL      is the code number of the error symbol.  If not
    #                       defined, then do no error processing.

    YYNOCODE = 61
    YYNSTATE = 129
    YYNRULE = 72
    YYERRORSYMBOL = 44
    YY_NO_ACTION     = YYNSTATE + YYNRULE + 2
    YY_ACCEPT_ACTION = YYNSTATE + YYNRULE + 1
    YY_ERROR_ACTION  = YYNSTATE + YYNRULE


    # Next are that tables used to determine what action to take based on the
    # current state and lookahead token.  These tables are used to implement
    # functions that take a state number and lookahead value and return an
    # action integer.  
    #
    # Suppose the action integer is N.  Then the action is determined as
    # follows
    #
    #   0 <= N < YYNSTATE                  Shift N.  That is, push the lookahead
    #                                      token onto the stack and goto state N.
    #
    #   YYNSTATE <= N < YYNSTATE+YYNRULE   Reduce by rule N-YYNSTATE.
    #
    #   N == YYNSTATE+YYNRULE              A syntax error has occurred.
    #
    #   N == YYNSTATE+YYNRULE+1            The parser accepts its input.
    #
    #   N == YYNSTATE+YYNRULE+2            No such action.  Denotes unused
    #                                      slots in the yy_action[] table.
    #
    # The action table is constructed as a single large table named yy_action[].
    # Given state S and lookahead X, the action is computed as
    #
    #      yy_action[ yy_shift_ofst[S] + X ]
    #
    # If the index value yy_shift_ofst[S]+X is out of range or if the value
    # yy_lookahead[yy_shift_ofst[S]+X] is not equal to X or if yy_shift_ofst[S]
    # is equal to YY_SHIFT_USE_DFLT, it means that the action is not in the table
    # and that yy_default[S] should be used instead.  
    #
    # The formula above is for computing the action when the lookahead is
    # a terminal symbol.  If the lookahead is a non-terminal (as occurs after
    # a reduce action) then the yy_reduce_ofst[] array is used in place of
    # the yy_shift_ofst[] array and YY_REDUCE_USE_DFLT is used in place of
    # YY_SHIFT_USE_DFLT.
    #
    # The following are the tables generated in this section:
    #
    #  yy_action[]        A single table containing all actions.
    #  yy_lookahead[]     A table containing the lookahead for each entry in
    #                     yy_action.  Used to detect hash collisions.
    #  yy_shift_ofst[]    For each state, the offset into yy_action for
    #                     shifting terminals.
    #  yy_reduce_ofst[]   For each state, the offset into yy_action for
    #                     shifting non-terminals after a reduce.
    #  yy_default[]       Default action for each state.

    yy_action = [
           42,   51,   15,   16,    9,   30,   31,   17,  109,  110, #     0
          111,   32,   18,   19,  115,   20,  117,  118,  119,   33, #    10
          121,   10,  123,   56,   48,  129,   37,   77,    3,   57, #    20
          202,   23,   61,  128,   36,   65,   89,    1,   73,   89, #    30
           45,    1,   87,   48,   98,   71,   72,   28,   44,   52, #    40
           76,   71,   72,   71,   72,  113,   95,   88,   34,   43, #    50
           93,   94,   96,   50,   97,   69,   92,   55,   89,   69, #    60
           89,   70,   53,   54,   68,   70,   12,   26,   68,   95, #    70
           12,   89,   99,   93,   94,   96,   89,   49,   46,   95, #    80
           88,   34,   90,   93,   94,   96,   43,   42,   51,   15, #    90
           16,   81,   80,   82,   71,   72,   71,   72,   24,   86, #   100
           78,  103,   71,   72,   71,   72,  122,   74,  125,   71, #   110
           72,   71,   72,   35,    7,  108,   95,   88,   34,   89, #   120
           93,   94,   96,  130,   38,   57,    3,   29,   83,   62, #   130
           27,  114,   49,  116,   89,   89,   41,   89,   60,  106, #   140
           85,   40,   39,   59,    5,   47,  104,   84,  107,  112, #   150
          120,   39,    4,   25,   21,   13,   63,   64,    2,   75, #   160
           66,   67,   79,    6,    7,   91,   14,  100,  101,  105, #   170
          102,  124,   58,  126,   22,  131,  127,    8,    2, #   180
        ]
    yy_lookahead = [
            5,    6,    7,    8,    9,   10,   11,   12,   13,   14, #     0
           15,   16,   17,   18,   19,   20,   21,   22,   23,   24, #    10
           25,   26,   27,   28,   40,    0,    1,   43,    3,   44, #    20
           45,   46,   47,   48,   44,   47,   51,    3,    4,   51, #    30
           44,    3,   52,   40,   51,   55,   56,   57,   52,    1, #    40
           52,   55,   56,   55,   56,   51,   31,   32,   33,    1, #    50
           35,   36,   37,   44,   47,   31,   47,   44,   51,   31, #    60
           51,   37,   49,   50,   40,   37,   42,   47,   40,   31, #    70
           42,   51,   47,   35,   36,   37,   51,   44,   44,   31, #    80
           32,   33,   34,   35,   36,   37,    1,    5,    6,    7, #    90
            8,   52,   59,   52,   55,   56,   55,   56,   41,   52, #   100
           43,   52,   55,   56,   55,   56,   52,    4,   52,   55, #   110
           56,   55,   56,   44,    2,   47,   31,   32,   33,   51, #   120
           35,   36,   37,    0,    1,   44,    3,   58,   59,   48, #   130
           47,   47,   44,   47,   51,   51,   44,   51,   44,    1, #   140
            4,   49,    2,   49,   41,   44,   53,   59,   53,   53, #   150
           53,    2,   54,   41,    3,    1,    4,    4,   38,    4, #   160
           39,   39,   43,    2,    2,   34,    1,    4,    4,   31, #   170
            4,   29,    2,    4,    3,    0,    4,   41,   38, #   180
        ]
    YY_SHIFT_USE_DFLT = -17
    YY_SHIFT_MAX = 61
    yy_shift_ofst = [
           25,   34,   38,   -5,   58,   38,   38,   38,   38,   38, #     0
           38,   38,  -16,   95,   95,   95,   95,   95,   95,   95, #    10
           95,   92,   92,  133,    3,    3,   48,   48,  113,   67, #    20
          148,  148,  148,  148,  -17,  122,  146,  150,  159,  161, #    30
          162,  163,  164,  130,  131,  132,  165,  129,  171,  172, #    40
          141,  175,  130,  173,  174,  176,  152,  180,  181,  179, #    50
          182,  185, #    60
        ]
    YY_REDUCE_USE_DFLT = -16
    YY_REDUCE_MAX = 34
    yy_reduce_ofst = [
          -15,  -10,   -4,   23,   19,   -2,   49,   51,   57,   59, #     0
           64,   66,   79,  -12,   17,   30,   35,   78,   93,   94, #    10
           96,  102,  104,   91,   43,   98,   -7,    4,   44,  111, #    20
          103,  105,  106,  107,  108, #    30
        ]
    yy_default = [
          201,  201,  201,  201,  201,  201,  201,  201,  201,  201, #     0
          201,  201,  201,  201,  201,  201,  201,  201,  201,  201, #    10
          201,  201,  201,  201,  201,  201,  201,  201,  201,  201, #    20
          201,  201,  201,  201,  173,  201,  201,  168,  201,  201, #    30
          201,  201,  201,  168,  201,  201,  201,  201,  201,  201, #    40
          201,  201,  201,  201,  201,  201,  201,  201,  201,  201, #    50
          201,  201,  133,  134,  138,  141,  179,  180,  181,  182, #    60
          183,  184,  185,  186,  187,  188,  191,  193,  194,  195, #    70
          197,  199,  200,  196,  198,  189,  192,  190,  169,  170, #    80
          171,  172,  174,  175,  176,  177,  178,  142,  143,  144, #    90
          135,  136,  140,  145,  146,  166,  167,  147,  148,  149, #   100
          150,  151,  152,  153,  154,  155,  156,  157,  158,  159, #   110
          160,  161,  162,  163,  164,  165,  137,  139,  132, #   120
        ]
    YY_SZ_ACTTAB = len(yy_action)


    # The next table maps tokens into fallback tokens.  If a construct
    # like the following:
    #
    #      %fallback ID X Y Z.
    #
    # appears in the grammer, then ID becomes a fallback token for X, Y,
    # and Z.  Whenever one of the tokens X, Y, or Z is input to the parser
    # but it does not parse, the type of the token is changed to ID and
    # the parse is retried before an error is thrown.

    yyFallback = [
          0,  #          $ => nothing
          0,  #     L_NAME => nothing
          0,  #    T_COLON => nothing
          0,  #  T_LSQUARE => nothing
          0,  #  T_RSQUARE => nothing
          0,  #   K_DEFINE => nothing
          1,  #   K_ASSUME => L_NAME
          1,  #  K_OBSERVE => L_NAME
          1,  #  K_PREDICT => L_NAME
          1,  # K_CONFIGURE => L_NAME
          1,  #   K_FORGET => L_NAME
          1,  #   K_REPORT => L_NAME
          1,  #    K_INFER => L_NAME
          1,  #    K_CLEAR => L_NAME
          1,  # K_ROLLBACK => L_NAME
          1,  # K_LIST_DIRECTIVES => L_NAME
          1,  # K_GET_DIRECTIVE => L_NAME
          1,  #    K_FORCE => L_NAME
          1,  #   K_SAMPLE => L_NAME
          1,  # K_CONTINUOUS_INFERENCE_STATUS => L_NAME
          1,  # K_START_CONTINUOUS_INFERENCE => L_NAME
          1,  # K_STOP_CONTINUOUS_INFERENCE => L_NAME
          1,  # K_GET_CURRENT_EXCEPTION => L_NAME
          1,  # K_GET_STATE => L_NAME
          1,  # K_GET_LOGSCORE => L_NAME
          1,  # K_GET_GLOBAL_LOGSCORE => L_NAME
          1,  # K_PROFILER_CONFIGURE => L_NAME
          1,  # K_PROFILER_CLEAR => L_NAME
          1,  # K_PROFILER_LIST_RANDOM => L_NAME
          1,  #  K_CHOICES => L_NAME
          1,  #     K_LOAD => L_NAME
          0,  #  L_INTEGER => nothing
          0,  # L_OPERATOR => nothing
          0,  #   T_LROUND => nothing
          0,  #   T_RROUND => nothing
          0,  #     T_TRUE => nothing
          0,  #    T_FALSE => nothing
          0,  #     L_REAL => nothing
         32,  #   T_LANGLE => L_OPERATOR
         32,  #   T_RANGLE => L_OPERATOR
          0,  #   L_STRING => nothing
          0,  #    T_COMMA => nothing
          0,  #   T_LCURLY => nothing
          0,  #   T_RCURLY => nothing
        ]


    # The following structure represents a single element of the
    # parser's stack.  Information stored includes:
    #
    #   +  The state number for the parser at this level of the stack.
    #
    #   +  The value of the token stored at this level of the stack.
    #      (In other words, the "major" token.)
    #
    #   +  The semantic value stored at this level of the stack.  This is
    #      the information used by the action routines in the grammar.
    #      It is sometimes called the "minor" token.
    #
    class yyStackEntry(object):
        def __init__(
            self,
            stateno, # The state-number
            major,   # The major token value.  This is the code
                     # number for the token at this stack level
            minor,   # The user-supplied minor token value.  This
                     # is the value of the token
            ):
            self.stateno = stateno
            self.major = major
            self.minor = minor
            return


    yyTraceFILE = None
    yyTracePrompt = None

    def trace(self, TraceFILE, zTracePrompt):
        '''Turn parser tracing on by giving a stream to which to write
        the trace and a prompt to preface each trace message.  Tracing
        is turned off by making either argument None.
        '''
        self.yyTraceFILE = TraceFILE
        self.yyTracePrompt = zTracePrompt
        if self.yyTraceFILE is None:
            self.yyTracePrompt = None
        elif self.yyTracePrompt is None:
            self.yyTraceFILE = None
        return


    # For tracing shifts, the names of all terminals and nonterminals
    # are required.  The following table supplies these names
    yyTokenName = [
        "$",                   "L_NAME",              "T_COLON",             "T_LSQUARE",   
        "T_RSQUARE",           "K_DEFINE",            "K_ASSUME",            "K_OBSERVE",   
        "K_PREDICT",           "K_CONFIGURE",         "K_FORGET",            "K_REPORT",    
        "K_INFER",             "K_CLEAR",             "K_ROLLBACK",          "K_LIST_DIRECTIVES",
        "K_GET_DIRECTIVE",        "K_FORCE",             "K_SAMPLE",            "K_CONTINUOUS_INFERENCE_STATUS",
        "K_START_CONTINUOUS_INFERENCE",        "K_STOP_CONTINUOUS_INFERENCE",        "K_GET_CURRENT_EXCEPTION",        "K_GET_STATE", 
        "K_GET_LOGSCORE",        "K_GET_GLOBAL_LOGSCORE",        "K_PROFILER_CONFIGURE",        "K_PROFILER_CLEAR",
        "K_PROFILER_LIST_RANDOM",        "K_CHOICES",           "K_LOAD",              "L_INTEGER",   
        "L_OPERATOR",          "T_LROUND",            "T_RROUND",            "T_TRUE",      
        "T_FALSE",             "L_REAL",              "T_LANGLE",            "T_RANGLE",    
        "L_STRING",            "T_COMMA",             "T_LCURLY",            "T_RCURLY",    
        "error",               "venture",             "instructions",        "expression",  
        "instruction",         "directive",           "command",             "literal",     
        "json",                "directive_ref",        "expressions",         "json_list",   
        "json_dict",           "json_list_terms",        "json_dict_entries",        "json_dict_entry",
        ]

    # For tracing reduce actions, the names of all rules are required.
    yyRuleName = [
        "venture ::=", #   0
        "venture ::= instructions", #   1
        "venture ::= expression", #   2
        "instructions ::= instruction", #   3
        "instructions ::= instructions instruction", #   4
        "instruction ::= L_NAME T_COLON T_LSQUARE directive T_RSQUARE", #   5
        "instruction ::= T_LSQUARE directive T_RSQUARE", #   6
        "instruction ::= T_LSQUARE command T_RSQUARE", #   7
        "instruction ::= error T_COLON T_LSQUARE directive T_RSQUARE", #   8
        "instruction ::= L_NAME T_COLON T_LSQUARE error T_RSQUARE", #   9
        "instruction ::= error T_COLON T_LSQUARE error T_RSQUARE", #  10
        "instruction ::= T_LSQUARE error T_RSQUARE", #  11
        "directive ::= K_DEFINE L_NAME expression", #  12
        "directive ::= K_ASSUME L_NAME expression", #  13
        "directive ::= K_OBSERVE expression literal", #  14
        "directive ::= K_PREDICT expression", #  15
        "command ::= K_CONFIGURE json", #  16
        "command ::= K_FORGET directive_ref", #  17
        "command ::= K_REPORT directive_ref", #  18
        "command ::= K_INFER expression", #  19
        "command ::= K_CLEAR", #  20
        "command ::= K_ROLLBACK", #  21
        "command ::= K_LIST_DIRECTIVES", #  22
        "command ::= K_GET_DIRECTIVE directive_ref", #  23
        "command ::= K_FORCE expression literal", #  24
        "command ::= K_SAMPLE expression", #  25
        "command ::= K_CONTINUOUS_INFERENCE_STATUS", #  26
        "command ::= K_START_CONTINUOUS_INFERENCE expression", #  27
        "command ::= K_STOP_CONTINUOUS_INFERENCE", #  28
        "command ::= K_GET_CURRENT_EXCEPTION", #  29
        "command ::= K_GET_STATE", #  30
        "command ::= K_GET_LOGSCORE directive_ref", #  31
        "command ::= K_GET_GLOBAL_LOGSCORE", #  32
        "command ::= K_PROFILER_CONFIGURE json", #  33
        "command ::= K_PROFILER_CLEAR", #  34
        "command ::= K_PROFILER_LIST_RANDOM K_CHOICES", #  35
        "command ::= K_LOAD json", #  36
        "directive_ref ::= L_INTEGER", #  37
        "directive_ref ::= L_NAME", #  38
        "expression ::= L_NAME", #  39
        "expression ::= L_OPERATOR", #  40
        "expression ::= literal", #  41
        "expression ::= T_LROUND expressions T_RROUND", #  42
        "expression ::= T_LROUND expressions error T_RROUND", #  43
        "expressions ::=", #  44
        "expressions ::= expressions expression", #  45
        "literal ::= T_TRUE", #  46
        "literal ::= T_FALSE", #  47
        "literal ::= L_INTEGER", #  48
        "literal ::= L_REAL", #  49
        "literal ::= L_NAME T_LANGLE json T_RANGLE", #  50
        "literal ::= L_NAME T_LANGLE error T_RANGLE", #  51
        "json ::= L_STRING", #  52
        "json ::= L_INTEGER", #  53
        "json ::= L_REAL", #  54
        "json ::= json_list", #  55
        "json ::= json_dict", #  56
        "json_list ::= T_LSQUARE T_RSQUARE", #  57
        "json_list ::= T_LSQUARE json_list_terms T_RSQUARE", #  58
        "json_list ::= T_LSQUARE json_list_terms error T_RSQUARE", #  59
        "json_list ::= T_LSQUARE error T_RSQUARE", #  60
        "json_list_terms ::= json", #  61
        "json_list_terms ::= json_list_terms T_COMMA json", #  62
        "json_list_terms ::= error T_COMMA json", #  63
        "json_dict ::= T_LCURLY T_RCURLY", #  64
        "json_dict ::= T_LCURLY json_dict_entries T_RCURLY", #  65
        "json_dict ::= T_LCURLY json_dict_entries error T_RCURLY", #  66
        "json_dict_entries ::= json_dict_entry", #  67
        "json_dict_entries ::= json_dict_entries T_COMMA json_dict_entry", #  68
        "json_dict_entries ::= error T_COMMA json_dict_entry", #  69
        "json_dict_entry ::= L_STRING T_COLON json", #  70
        "json_dict_entry ::= error T_COLON json", #  71
        ]


    def __init__(self, delegate):
        self.yystack = [] # The parser's stack
        self.delegate = delegate
        return


    def yy_pop_parser_stack(self):
        """Pop the parser's stack once. Return the major token number
        for the symbol popped.
        """
        if not self.yystack:
            return 0
        yytos = self.yystack.pop()
        if self.yyTraceFILE:
            self.yyTraceFILE.write("%sPopping %s\n" % (
                self.yyTracePrompt,
                self.yyTokenName[yytos.major]))
        yymajor = yytos.major
        return yymajor


    def yy_find_shift_action(self,       # The parser
                             iLookAhead  # The look-ahead token
                             ):
        '''Find the appropriate action for a parser given the terminal
        look-ahead token iLookAhead.

        If the look-ahead token is YYNOCODE, then check to see if the
        action is independent of the look-ahead.  If it is, return the
        action, otherwise return YY_NO_ACTION.
        '''
        yyTraceFILE = self.yyTraceFILE
        stateno = self.yystack[-1].stateno
        if stateno > self.YY_SHIFT_MAX:
            return self.yy_default[stateno]
        i = self.yy_shift_ofst[stateno]
        if i == self.YY_SHIFT_USE_DFLT:
            return self.yy_default[stateno]
        assert iLookAhead != self.YYNOCODE
        i += iLookAhead
        if i < 0 or i >= self.YY_SZ_ACTTAB or self.yy_lookahead[i] != iLookAhead:
            if iLookAhead > 0:
                yyFallback = self.yyFallback
                yyTokenName = self.yyTokenName
                if iLookAhead < len(yyFallback):
                    iFallback = yyFallback[iLookAhead] # Fallback token
                    if iFallback != 0:
                        if yyTraceFILE:
                            yyTraceFILE.write(
                                "%sFALLBACK %s => %s\n" %
                                (self.yyTracePrompt,
                                 yyTokenName[iLookAhead], yyTokenName[iFallback]))
                        return self.yy_find_shift_action(iFallback);
                YYWILDCARD = self.YYWILDCARD
                if YYWILDCARD is not None:
                    j = i - iLookAhead + YYWILDCARD
                    if j >= 0 and j < self.YY_SZ_ACTTAB and self.yy_lookahead[j] == YYWILDCARD:
                        if yyTraceFILE:
                            yyTraceFILE.write(
                                "%sWILDCARD %s => %s\n" %
                                (self.yyTracePrompt,
                                 yyTokenName[iLookAhead], yyTokenName[YYWILDCARD]))
                        return self.yy_action[j];
            return self.yy_default[stateno]
        else:
            return self.yy_action[i]


    def yy_find_reduce_action(self,
                              stateno,    # Current state number
                              iLookAhead  # The look-ahead token
                              ):
        '''Find the appropriate action for a parser given the
        non-terminal look-ahead token iLookAhead.
        
        If the look-ahead token is YYNOCODE, then check to see if the
        action is independent of the look-ahead.  If it is, return the
        action, otherwise return YY_NO_ACTION.
        '''
        YYERRORSYMBOL = self.YYERRORSYMBOL
        if YYERRORSYMBOL is not None:
            if stateno > self.YY_REDUCE_MAX:
                return self.yy_default[stateno]
        else:
            assert stateno <= self.YY_REDUCE_MAX
        i = self.yy_reduce_ofst[stateno]
        assert i != self.YY_REDUCE_USE_DFLT
        assert iLookAhead != self.YYNOCODE
        i += iLookAhead
        if YYERRORSYMBOL is not None:
            if i < 0 or i >= self.YY_SZ_ACTTAB or self.yy_lookahead[i] != iLookAhead:
                return self.yy_default[stateno]
        else:
            assert i >= 0 and i < self.YY_SZ_ACTTAB
            assert self.yy_lookahead[i] == iLookAhead
        return self.yy_action[i]


    def yy_shift(self,        # The parser to be shifted
                 yyNewState,  # The new state to shift in
                 yyMajor,     # The major token to shift in
                 yyMinor      # The minor token to shift in
                 ):
        '''Perform a shift action.'''

        yytos = self.yyStackEntry(
            stateno = yyNewState,
            major = yyMajor,
            minor = yyMinor
            )
        self.yystack.append(yytos)

        yyTraceFILE = self.yyTraceFILE
        if yyTraceFILE:
            yyTraceFILE.write("%sShift %d\n" % (self.yyTracePrompt, yyNewState))
            yyTraceFILE.write("%sStack:" % self.yyTracePrompt)
            for entry in self.yystack:
                yyTraceFILE.write(" %s" % self.yyTokenName[entry.major])
            yyTraceFILE.write("\n")

        return


    # The following table contains information about every rule that
    # is used during the reduce.
    from collections import namedtuple
    yyRuleInfoEntry = namedtuple(
        'yyRuleInfoEntry',
        ('lhs',  # Symbol on the left-hand side of the rule
         'nrhs', # Number of right-hand side symbols in the rule
         ))
    yyRuleInfo = [
        yyRuleInfoEntry( 45, 0 ),
        yyRuleInfoEntry( 45, 1 ),
        yyRuleInfoEntry( 45, 1 ),
        yyRuleInfoEntry( 46, 1 ),
        yyRuleInfoEntry( 46, 2 ),
        yyRuleInfoEntry( 48, 5 ),
        yyRuleInfoEntry( 48, 3 ),
        yyRuleInfoEntry( 48, 3 ),
        yyRuleInfoEntry( 48, 5 ),
        yyRuleInfoEntry( 48, 5 ),
        yyRuleInfoEntry( 48, 5 ),
        yyRuleInfoEntry( 48, 3 ),
        yyRuleInfoEntry( 49, 3 ),
        yyRuleInfoEntry( 49, 3 ),
        yyRuleInfoEntry( 49, 3 ),
        yyRuleInfoEntry( 49, 2 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 50, 1 ),
        yyRuleInfoEntry( 50, 1 ),
        yyRuleInfoEntry( 50, 1 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 50, 3 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 50, 1 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 50, 1 ),
        yyRuleInfoEntry( 50, 1 ),
        yyRuleInfoEntry( 50, 1 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 50, 1 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 50, 1 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 50, 2 ),
        yyRuleInfoEntry( 53, 1 ),
        yyRuleInfoEntry( 53, 1 ),
        yyRuleInfoEntry( 47, 1 ),
        yyRuleInfoEntry( 47, 1 ),
        yyRuleInfoEntry( 47, 1 ),
        yyRuleInfoEntry( 47, 3 ),
        yyRuleInfoEntry( 47, 4 ),
        yyRuleInfoEntry( 54, 0 ),
        yyRuleInfoEntry( 54, 2 ),
        yyRuleInfoEntry( 51, 1 ),
        yyRuleInfoEntry( 51, 1 ),
        yyRuleInfoEntry( 51, 1 ),
        yyRuleInfoEntry( 51, 1 ),
        yyRuleInfoEntry( 51, 4 ),
        yyRuleInfoEntry( 51, 4 ),
        yyRuleInfoEntry( 52, 1 ),
        yyRuleInfoEntry( 52, 1 ),
        yyRuleInfoEntry( 52, 1 ),
        yyRuleInfoEntry( 52, 1 ),
        yyRuleInfoEntry( 52, 1 ),
        yyRuleInfoEntry( 55, 2 ),
        yyRuleInfoEntry( 55, 3 ),
        yyRuleInfoEntry( 55, 4 ),
        yyRuleInfoEntry( 55, 3 ),
        yyRuleInfoEntry( 57, 1 ),
        yyRuleInfoEntry( 57, 3 ),
        yyRuleInfoEntry( 57, 3 ),
        yyRuleInfoEntry( 56, 2 ),
        yyRuleInfoEntry( 56, 3 ),
        yyRuleInfoEntry( 56, 4 ),
        yyRuleInfoEntry( 58, 1 ),
        yyRuleInfoEntry( 58, 3 ),
        yyRuleInfoEntry( 58, 3 ),
        yyRuleInfoEntry( 59, 3 ),
        yyRuleInfoEntry( 59, 3 ),
        ]


    # Action code for each rule follows.
    def action_000(self):
        # venture ::=
        return self.delegate.p_venture_empty(
            )
    def action_001(self):
        # venture ::= instructions
        return self.delegate.p_venture_i(
            insts = self.yystack[-1].minor,
            )
    def action_002(self):
        # venture ::= expression
        return self.delegate.p_venture_e(
            exp = self.yystack[-1].minor,
            )
    def action_003(self):
        # instructions ::= instruction
        return self.delegate.p_instructions_one(
            inst = self.yystack[-1].minor,
            )
    def action_004(self):
        # instructions ::= instructions instruction
        return self.delegate.p_instructions_many(
            insts = self.yystack[-2].minor,
            inst = self.yystack[-1].minor,
            )
    def action_005(self):
        # instruction ::= L_NAME T_COLON T_LSQUARE directive T_RSQUARE
        return self.delegate.p_instruction_labelled(
            l = self.yystack[-5].minor,
            open = self.yystack[-3].minor,
            d = self.yystack[-2].minor,
            close = self.yystack[-1].minor,
            )
    def action_006(self):
        # instruction ::= T_LSQUARE directive T_RSQUARE
        return self.delegate.p_instruction_unlabelled(
            open = self.yystack[-3].minor,
            d = self.yystack[-2].minor,
            close = self.yystack[-1].minor,
            )
    def action_007(self):
        # instruction ::= T_LSQUARE command T_RSQUARE
        return self.delegate.p_instruction_command(
            open = self.yystack[-3].minor,
            c = self.yystack[-2].minor,
            close = self.yystack[-1].minor,
            )
    def action_008(self):
        # instruction ::= error T_COLON T_LSQUARE directive T_RSQUARE
        return self.delegate.p_instruction_laberror(
            colon = self.yystack[-4].minor,
            open = self.yystack[-3].minor,
            d = self.yystack[-2].minor,
            close = self.yystack[-1].minor,
            )
    def action_009(self):
        # instruction ::= L_NAME T_COLON T_LSQUARE error T_RSQUARE
        return self.delegate.p_instruction_direrror(
            l = self.yystack[-5].minor,
            colon = self.yystack[-4].minor,
            open = self.yystack[-3].minor,
            close = self.yystack[-1].minor,
            )
    def action_010(self):
        # instruction ::= error T_COLON T_LSQUARE error T_RSQUARE
        return self.delegate.p_instruction_labdirerror(
            colon = self.yystack[-4].minor,
            open = self.yystack[-3].minor,
            close = self.yystack[-1].minor,
            )
    def action_011(self):
        # instruction ::= T_LSQUARE error T_RSQUARE
        return self.delegate.p_instruction_error(
            open = self.yystack[-3].minor,
            close = self.yystack[-1].minor,
            )
    def action_012(self):
        # directive ::= K_DEFINE L_NAME expression
        return self.delegate.p_directive_define(
            k = self.yystack[-3].minor,
            n = self.yystack[-2].minor,
            e = self.yystack[-1].minor,
            )
    def action_013(self):
        # directive ::= K_ASSUME L_NAME expression
        return self.delegate.p_directive_assume(
            k = self.yystack[-3].minor,
            n = self.yystack[-2].minor,
            e = self.yystack[-1].minor,
            )
    def action_014(self):
        # directive ::= K_OBSERVE expression literal
        return self.delegate.p_directive_observe(
            k = self.yystack[-3].minor,
            e = self.yystack[-2].minor,
            v = self.yystack[-1].minor,
            )
    def action_015(self):
        # directive ::= K_PREDICT expression
        return self.delegate.p_directive_predict(
            k = self.yystack[-2].minor,
            e = self.yystack[-1].minor,
            )
    def action_016(self):
        # command ::= K_CONFIGURE json
        return self.delegate.p_command_configure(
            k = self.yystack[-2].minor,
            options = self.yystack[-1].minor,
            )
    def action_017(self):
        # command ::= K_FORGET directive_ref
        return self.delegate.p_command_forget(
            k = self.yystack[-2].minor,
            dr = self.yystack[-1].minor,
            )
    def action_018(self):
        # command ::= K_REPORT directive_ref
        return self.delegate.p_command_report(
            k = self.yystack[-2].minor,
            dr = self.yystack[-1].minor,
            )
    def action_019(self):
        # command ::= K_INFER expression
        return self.delegate.p_command_infer(
            k = self.yystack[-2].minor,
            e = self.yystack[-1].minor,
            )
    def action_020(self):
        # command ::= K_CLEAR
        return self.delegate.p_command_clear(
            k = self.yystack[-1].minor,
            )
    def action_021(self):
        # command ::= K_ROLLBACK
        return self.delegate.p_command_rollback(
            k = self.yystack[-1].minor,
            )
    def action_022(self):
        # command ::= K_LIST_DIRECTIVES
        return self.delegate.p_command_list_directives(
            k = self.yystack[-1].minor,
            )
    def action_023(self):
        # command ::= K_GET_DIRECTIVE directive_ref
        return self.delegate.p_command_get_directive(
            k = self.yystack[-2].minor,
            dr = self.yystack[-1].minor,
            )
    def action_024(self):
        # command ::= K_FORCE expression literal
        return self.delegate.p_command_force(
            k = self.yystack[-3].minor,
            e = self.yystack[-2].minor,
            v = self.yystack[-1].minor,
            )
    def action_025(self):
        # command ::= K_SAMPLE expression
        return self.delegate.p_command_sample(
            k = self.yystack[-2].minor,
            e = self.yystack[-1].minor,
            )
    def action_026(self):
        # command ::= K_CONTINUOUS_INFERENCE_STATUS
        return self.delegate.p_command_continuous_inference_status(
            k = self.yystack[-1].minor,
            )
    def action_027(self):
        # command ::= K_START_CONTINUOUS_INFERENCE expression
        return self.delegate.p_command_start_continuous_inference(
            k = self.yystack[-2].minor,
            e = self.yystack[-1].minor,
            )
    def action_028(self):
        # command ::= K_STOP_CONTINUOUS_INFERENCE
        return self.delegate.p_command_stop_continuous_inference(
            k = self.yystack[-1].minor,
            )
    def action_029(self):
        # command ::= K_GET_CURRENT_EXCEPTION
        return self.delegate.p_command_get_current_exception(
            k = self.yystack[-1].minor,
            )
    def action_030(self):
        # command ::= K_GET_STATE
        return self.delegate.p_command_get_state(
            k = self.yystack[-1].minor,
            )
    def action_031(self):
        # command ::= K_GET_LOGSCORE directive_ref
        return self.delegate.p_command_get_logscore(
            k = self.yystack[-2].minor,
            d = self.yystack[-1].minor,
            )
    def action_032(self):
        # command ::= K_GET_GLOBAL_LOGSCORE
        return self.delegate.p_command_get_global_logscore(
            k = self.yystack[-1].minor,
            )
    def action_033(self):
        # command ::= K_PROFILER_CONFIGURE json
        return self.delegate.p_command_profiler_configure(
            k = self.yystack[-2].minor,
            options = self.yystack[-1].minor,
            )
    def action_034(self):
        # command ::= K_PROFILER_CLEAR
        return self.delegate.p_command_profiler_clear(
            k = self.yystack[-1].minor,
            )
    def action_035(self):
        # command ::= K_PROFILER_LIST_RANDOM K_CHOICES
        return self.delegate.p_command_profiler_list_random(
            k = self.yystack[-2].minor,
            )
    def action_036(self):
        # command ::= K_LOAD json
        return self.delegate.p_command_load(
            k = self.yystack[-2].minor,
            pathname = self.yystack[-1].minor,
            )
    def action_037(self):
        # directive_ref ::= L_INTEGER
        return self.delegate.p_directive_ref_numbered(
            number = self.yystack[-1].minor,
            )
    def action_038(self):
        # directive_ref ::= L_NAME
        return self.delegate.p_directive_ref_labelled(
            label = self.yystack[-1].minor,
            )
    def action_039(self):
        # expression ::= L_NAME
        return self.delegate.p_expression_symbol(
            name = self.yystack[-1].minor,
            )
    def action_040(self):
        # expression ::= L_OPERATOR
        return self.delegate.p_expression_operator(
            op = self.yystack[-1].minor,
            )
    def action_041(self):
        # expression ::= literal
        return self.delegate.p_expression_literal(
            value = self.yystack[-1].minor,
            )
    def action_042(self):
        # expression ::= T_LROUND expressions T_RROUND
        return self.delegate.p_expression_combination(
            open = self.yystack[-3].minor,
            es = self.yystack[-2].minor,
            close = self.yystack[-1].minor,
            )
    def action_043(self):
        # expression ::= T_LROUND expressions error T_RROUND
        return self.delegate.p_expression_comb_error(
            open = self.yystack[-4].minor,
            es = self.yystack[-3].minor,
            close = self.yystack[-1].minor,
            )
    def action_044(self):
        # expressions ::=
        return self.delegate.p_expressions_none(
            )
    def action_045(self):
        # expressions ::= expressions expression
        return self.delegate.p_expressions_some(
            es = self.yystack[-2].minor,
            e = self.yystack[-1].minor,
            )
    def action_046(self):
        # literal ::= T_TRUE
        return self.delegate.p_literal_true(
            t = self.yystack[-1].minor,
            )
    def action_047(self):
        # literal ::= T_FALSE
        return self.delegate.p_literal_false(
            f = self.yystack[-1].minor,
            )
    def action_048(self):
        # literal ::= L_INTEGER
        return self.delegate.p_literal_integer(
            v = self.yystack[-1].minor,
            )
    def action_049(self):
        # literal ::= L_REAL
        return self.delegate.p_literal_real(
            v = self.yystack[-1].minor,
            )
    def action_050(self):
        # literal ::= L_NAME T_LANGLE json T_RANGLE
        return self.delegate.p_literal_json(
            type = self.yystack[-4].minor,
            open = self.yystack[-3].minor,
            value = self.yystack[-2].minor,
            close = self.yystack[-1].minor,
            )
    def action_051(self):
        # literal ::= L_NAME T_LANGLE error T_RANGLE
        return self.delegate.p_literal_json_error(
            type = self.yystack[-4].minor,
            open = self.yystack[-3].minor,
            close = self.yystack[-1].minor,
            )
    def action_052(self):
        # json ::= L_STRING
        return self.delegate.p_json_string(
            v = self.yystack[-1].minor,
            )
    def action_053(self):
        # json ::= L_INTEGER
        return self.delegate.p_json_integer(
            v = self.yystack[-1].minor,
            )
    def action_054(self):
        # json ::= L_REAL
        return self.delegate.p_json_real(
            v = self.yystack[-1].minor,
            )
    def action_055(self):
        # json ::= json_list
        return self.delegate.p_json_list(
            l = self.yystack[-1].minor,
            )
    def action_056(self):
        # json ::= json_dict
        return self.delegate.p_json_dict(
            d = self.yystack[-1].minor,
            )
    def action_057(self):
        # json_list ::= T_LSQUARE T_RSQUARE
        return self.delegate.p_json_list_empty(
            )
    def action_058(self):
        # json_list ::= T_LSQUARE json_list_terms T_RSQUARE
        return self.delegate.p_json_list_nonempty(
            ts = self.yystack[-2].minor,
            )
    def action_059(self):
        # json_list ::= T_LSQUARE json_list_terms error T_RSQUARE
        return self.delegate.p_json_list_error1(
            ts = self.yystack[-3].minor,
            )
    def action_060(self):
        # json_list ::= T_LSQUARE error T_RSQUARE
        return self.delegate.p_json_list_error(
            )
    def action_061(self):
        # json_list_terms ::= json
        return self.delegate.p_json_list_terms_one(
            t = self.yystack[-1].minor,
            )
    def action_062(self):
        # json_list_terms ::= json_list_terms T_COMMA json
        return self.delegate.p_json_list_terms_many(
            ts = self.yystack[-3].minor,
            t = self.yystack[-1].minor,
            )
    def action_063(self):
        # json_list_terms ::= error T_COMMA json
        return self.delegate.p_json_list_terms_error(
            t = self.yystack[-1].minor,
            )
    def action_064(self):
        # json_dict ::= T_LCURLY T_RCURLY
        return self.delegate.p_json_dict_empty(
            )
    def action_065(self):
        # json_dict ::= T_LCURLY json_dict_entries T_RCURLY
        return self.delegate.p_json_dict_nonempty(
            es = self.yystack[-2].minor,
            )
    def action_066(self):
        # json_dict ::= T_LCURLY json_dict_entries error T_RCURLY
        return self.delegate.p_json_dict_error(
            es = self.yystack[-3].minor,
            )
    def action_067(self):
        # json_dict_entries ::= json_dict_entry
        return self.delegate.p_json_dict_entries_one(
            e = self.yystack[-1].minor,
            )
    def action_068(self):
        # json_dict_entries ::= json_dict_entries T_COMMA json_dict_entry
        return self.delegate.p_json_dict_entries_many(
            es = self.yystack[-3].minor,
            e = self.yystack[-1].minor,
            )
    def action_069(self):
        # json_dict_entries ::= error T_COMMA json_dict_entry
        return self.delegate.p_json_dict_entries_error(
            e = self.yystack[-1].minor,
            )
    def action_070(self):
        # json_dict_entry ::= L_STRING T_COLON json
        return self.delegate.p_json_dict_entry_e(
            key = self.yystack[-3].minor,
            value = self.yystack[-1].minor,
            )
    def action_071(self):
        # json_dict_entry ::= error T_COLON json
        return self.delegate.p_json_dict_entry_error(
            value = self.yystack[-1].minor,
            )
    yy_action_method = [
        action_000,
        action_001,
        action_002,
        action_003,
        action_004,
        action_005,
        action_006,
        action_007,
        action_008,
        action_009,
        action_010,
        action_011,
        action_012,
        action_013,
        action_014,
        action_015,
        action_016,
        action_017,
        action_018,
        action_019,
        action_020,
        action_021,
        action_022,
        action_023,
        action_024,
        action_025,
        action_026,
        action_027,
        action_028,
        action_029,
        action_030,
        action_031,
        action_032,
        action_033,
        action_034,
        action_035,
        action_036,
        action_037,
        action_038,
        action_039,
        action_040,
        action_041,
        action_042,
        action_043,
        action_044,
        action_045,
        action_046,
        action_047,
        action_048,
        action_049,
        action_050,
        action_051,
        action_052,
        action_053,
        action_054,
        action_055,
        action_056,
        action_057,
        action_058,
        action_059,
        action_060,
        action_061,
        action_062,
        action_063,
        action_064,
        action_065,
        action_066,
        action_067,
        action_068,
        action_069,
        action_070,
        action_071,
    ]


    def yy_reduce(self,     # The parser
                  yyruleno  # Number of the rule by which to reduce
                  ):
        '''Perform a reduce action and the shift that must immediately
        follow the reduce.'''
        
        if (self.yyTraceFILE and
            yyruleno >= 0 and yyruleno < len(self.yyRuleName)
            ):
            self.yyTraceFILE.write("%sReduce [%s].\n" % (
                self.yyTracePrompt, self.yyRuleName[yyruleno]))

        # get the action
        action = self.yy_action_method[yyruleno]

        # 'yygotominor' is the LHS of the rule reduced
        yygotominor = action(self)

        yygoto = self.yyRuleInfo[yyruleno].lhs   # The next state
        yysize = self.yyRuleInfo[yyruleno].nrhs  # Amount to pop the stack
        if yysize > 0:
            del self.yystack[-yysize:]

        # The next action
        yyact = self.yy_find_reduce_action(self.yystack[-1].stateno, yygoto)

        if yyact < self.YYNSTATE:
            self.yy_shift(yyact, yygoto, yygotominor)
        else:
            assert yyact == self.YYNSTATE + self.YYNRULE + 1
            self.yy_accept()

        return


    def yy_parse_failed(self):
        '''This method executes when the parse fails.'''

        if self.yyTraceFILE:
            self.yyTraceFILE.write("%sFail!\n" % self.yyTracePrompt)

        while self.yystack:
            self.yy_pop_parser_stack()

        self.delegate.parse_failed()

        return


    def yy_syntax_error(self, token):
        '''This method executes when a syntax error occurs.'''
        self.delegate.syntax_error(token)
        return


    def yy_accept(self):
        '''This method executes when the parser accepts.'''

        if self.yyTraceFILE:
            self.yyTraceFILE.write("%sAccept!\n" % self.yyTracePrompt)

        while self.yystack:
            self.yy_pop_parser_stack()

        self.delegate.accept()

        return


    def parse(self, tokens):
        for token in tokens:
            self.feed(token)
        self.feed((0, None))
        return


    def feed(self, token):
        '''The main parser routine.'''

        yymajor = token[0]  # The major token code number
        yyminor = token[1]  # The value for the token

        yyerrorhit = False  # True if yymajor has invoked an error

        # (re)initialize the parser, if necessary
        if not self.yystack:
            self.yyerrcnt = -1
            yytos = self.yyStackEntry(
                stateno = 0,
                major = 0,
                minor = None
                )
            self.yystack.append(yytos)

        yyendofinput = (yymajor == 0) # True if we are at the end of input
        
        if self.yyTraceFILE:
            self.yyTraceFILE.write(
                "%sInput %s\n" %
                (self.yyTracePrompt, self.yyTokenName[yymajor]))


        cond = True
        while cond:

            # The parser action.
            yyact = self.yy_find_shift_action(yymajor)

            YYNOCODE = self.YYNOCODE
            YYNSTATE = self.YYNSTATE
            YYNRULE  = self.YYNRULE

            if yyact < YYNSTATE:
                assert not yyendofinput, "Impossible to shift the $ token"
                self.yy_shift(yyact, yymajor, yyminor)
                self.yyerrcnt -= 1
                yymajor = YYNOCODE
            elif yyact < YYNSTATE + YYNRULE:
                self.yy_reduce(yyact - YYNSTATE)
            else:
                assert yyact == self.YY_ERROR_ACTION
                if self.yyTraceFILE:
                    self.yyTraceFILE.write(
                        "%sSyntax Error!\n" % self.yyTracePrompt)

                YYERRORSYMBOL = self.YYERRORSYMBOL
                if YYERRORSYMBOL is not None:
                    # A syntax error has occurred.
                    # The response to an error depends upon whether or not the
                    # grammar defines an error token "ERROR".  
                    #
                    # This is what we do if the grammar does define ERROR:
                    #
                    #  * Call the %syntax_error function.
                    #
                    #  * Begin popping the stack until we enter a state where
                    #    it is legal to shift the error symbol, then shift
                    #    the error symbol.
                    #
                    #  * Set the error count to three.
                    #
                    #  * Begin accepting and shifting new tokens.  No new error
                    #    processing will occur until three tokens have been
                    #    shifted successfully.
                    #
                    if self.yyerrcnt < 0:
                        self.yy_syntax_error(token)

                    yymx = self.yystack[-1].major
                    if yymx == YYERRORSYMBOL or yyerrorhit:
                        if self.yyTraceFILE:
                            self.yyTraceFILE.write(
                                "%sDiscard input token %s\n" % (
                                    self.yyTracePrompt,
                                    self.yyTokenName[yymajor]))
                        yymajor = YYNOCODE
                    else:
                        while self.yystack and yymx != YYERRORSYMBOL:
                            yyact = self.yy_find_reduce_action(
                                self.yystack[-1].stateno,
                                YYERRORSYMBOL
                                )
                            if yyact < YYNSTATE:
                                break
                            self.yy_pop_parser_stack()

                        if not self.yystack or yymajor == 0:
                            self.yy_parse_failed()
                            yymajor = YYNOCODE
                        elif yymx != YYERRORSYMBOL:
                            self.yy_shift(yyact, YYERRORSYMBOL, None)

                    self.yyerrcnt = 3
                    yyerrorhit = True

                else: # YYERRORSYMBOL is not defined
                    # This is what we do if the grammar does not define ERROR:
                    #
                    #  * Report an error message, and throw away the input token.
                    #
                    #  * If the input token is $, then fail the parse.
                    #
                    # As before, subsequent error messages are suppressed until
                    # three input tokens have been successfully shifted.
                    #
                    if self.yyerrcnt <= 0:
                        self.yy_syntax_error(token)

                    self.yyerrcnt = 3
                    if yyendofinput:
                        self.yy_parse_failed()

                    yymajor = YYNOCODE

            cond = yymajor != YYNOCODE and self.yystack

        return


