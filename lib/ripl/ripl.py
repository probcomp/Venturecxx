#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture.ripl import utils
from venture.exception import VentureException


class Ripl():
    def __init__(self,sivm,parsers):
        self.sivm = sivm
        self.parsers = parsers
        self.directive_id_to_string = {}
        self.directive_id_to_mode = {}
        self.mode = parsers.keys()[0]



    ############################################
    # Languages
    ############################################

    def get_mode(self):
        return self.mode

    def list_available_modes(self):
        return self.parsers.keys()

    def set_mode(self, mode):
        if mode in self.parsers:
            self.mode = mode
        else:
            raise VentureException('invalid_mode',
                    "Mode {} is not implemented by this RIPL".format(mode))


    ############################################
    # Execution
    ############################################

    def execute_instruction(self, instruction_string, params=None):
        p = self._cur_parser()
        # perform parameter substitution if necessary
        if params != None:
            instruction_string = self.substitute_params(instruction_string,params)
        # parse instruction
        parsed_instruction = p.parse_instruction(instruction_string)
        # calculate the positions of the arguments
        args, arg_ranges = p.split_instruction(instruction_string)
        try:
            # execute instruction, and handle possible exception
            ret_value = self.sivm.execute_instruction(parsed_instruction)
        except VentureException as e:
            # all exceptions raised by the Sivm get augmented with a
            # text index (which defaults to the entire instruction)
            e.data['text_index'] = [0,len(instruction_string)-1]
            # in the case of a parse exception, the text_index gets narrowed
            # down to the exact expression/atom that caused the error
            if e.exception == 'parse':
                try:
                    text_index = self._cur_parser().expression_index_to_text_index(
                            args['expression'], e.data['expression_index'])
                    offset = arg_ranges['expression'][0]
                    text_index = [x + offset for x in text_index]
                except VentureException as e2:
                    if e2.exception == 'no_text_index':
                        text_index = None
                    else:
                        raise
                e.data['text_index'] = text_index
            # in case of invalid argument exception, the text index
            # refers to the argument's location in the string
            if e.exception == 'invalid_argument':
                arg = e.data['argument']
                text_index = arg_ranges[arg]
                e.data['text_index'] = text_index
            a = e.data['text_index'][0]
            b = e.data['text_index'][1]+1
            e.data['text_snippet'] = instruction_string[a:b]
            raise
        # if directive, then save the text string
        if parsed_instruction['instruction'] in ['assume','observe',
                'predict','labeled_assume','labeled_observe','labeled_predict']:
            did = ret_value['directive_id']
            self.directive_id_to_string[did] = instruction_string
            self.directive_id_to_mode[did] = self.mode
        return ret_value


    def execute_program(self, program_string, params=None):
        p = self._cur_parser()
        # perform parameter substitution if necessary
        if params != None:
            program_string = self.substitute_params(program_string,params)
        instructions, positions = p.split_program(program_string)
        vals = []
        for instruction in instructions:
            vals.append(self.execute_instruction(instruction))
        return vals


    ############################################
    # Text manipulation
    ############################################

    def substitute_params(self,instruction_string,params):
        p = self._cur_parser()
        return p.substitute_params(instruction_string,params)

    def split_program(self,program_string):
        p = self._cur_parser()
        return p.split_program(program_string)

    def get_text(self,directive_id):
        if directive_id in self.directive_id_to_mode:
            return [self.directive_id_to_mode[directive_id], self.directive_id_to_string[directive_id]]
        return None

    def character_index_to_expression_index(self, directive_id, character_index):
        p = self._cur_parser()
        expression, offset = self._extract_expression(directive_id)
        return p.character_index_to_expression_index(expression, character_index-offset)

    def expression_index_to_text_index(self, directive_id, expression_index):
        p = self._cur_parser()
        expression, offset = self._extract_expression(directive_id)
        tmp = p.expression_index_to_text_index(expression, expression_index)
        return [x+offset for x in tmp]


    ############################################
    # Directives
    ############################################

    def assume(self, name, expression, label=None, type=False):
        if label==None:
            s = self._cur_parser().get_instruction_string('assume')
            d = {'symbol':name, 'expression':expression}
        else:
            s = self._cur_parser().get_instruction_string('labeled_assume')
            d = {'symbol':name, 'expression':expression, 'label':label}
        value = self.execute_instruction(s,d)['value']
        return value if type else value['value']

    def predict(self, expression, label=None, type=False):
        if label==None:
            s = self._cur_parser().get_instruction_string('predict')
            d = {'expression':expression}
        else:
            s = self._cur_parser().get_instruction_string('labeled_predict')
            d = {'expression':expression, 'label':label}
        value = self.execute_instruction(s,d)['value']
        return value if type else value['value']

    def observe(self, expression, value, label=None):
        if label==None:
            s = self._cur_parser().get_instruction_string('observe')
            d = {'expression':expression, 'value':value}
        else:
            s = self._cur_parser().get_instruction_string('labeled_observe')
            d = {'expression':expression, 'value':value, 'label':label}
        self.execute_instruction(s,d)
        return None

    ############################################
    # Core
    ############################################

    def configure(self, options={}):
        p = self._cur_parser()
        s = p.get_instruction_string('configure')
        d = {'options':options}
        return self.execute_instruction(s,d)['options']
    
    def get_seed(self):
        return self.configure()['seed']
    
    def set_seed(self, seed):
        self.configure({'seed': seed})
        return None
    
    def get_inference_timeout(self):
        return self.configure()['inference_timeout']
    
    def set_inference_timeout(self, inference_timeout):
        self.configure({'inference_timeout': inference_timeout})
        return None
    
    def forget(self, label_or_did):
        if isinstance(label_or_did,int):
            s = self._cur_parser().get_instruction_string('forget')
            d = {'directive_id':label_or_did}
        else:
            s = self._cur_parser().get_instruction_string('labeled_forget')
            d = {'label':label_or_did}
        self.execute_instruction(s,d)
        return None

    def report(self, label_or_did, type=False):
        if isinstance(label_or_did,int):
            s = self._cur_parser().get_instruction_string('report')
            d = {'directive_id':label_or_did}
        else:
            s = self._cur_parser().get_instruction_string('labeled_report')
            d = {'label':label_or_did}
        value = self.execute_instruction(s,d)['value']
        return value if type else value['value']

    def infer(self, iterations, resample=False):
        s = self._cur_parser().get_instruction_string('infer')
        d = {'iterations':iterations,'resample':resample}
        self.execute_instruction(s,d)
        return None

    def clear(self):
        s = self._cur_parser().get_instruction_string('clear')
        d = {}
        self.execute_instruction(s,{})
        return None

    def rollback(self):
        s = self._cur_parser().get_instruction_string('rollback')
        self.execute_instruction(s,{})
        return None

    def list_directives(self, type=False):
        s = self._cur_parser().get_instruction_string('list_directives')
        directives = self.execute_instruction(s,{})['directives']
        # modified to add value to each directive
        for directive in directives:
            value = self.report(directive['directive_id'], type)
            directive['value'] = value
        return directives

    def get_directive(self, label_or_did):
        if isinstance(label_or_did,int):
            s = self._cur_parser().get_instruction_string('get_directive')
            d = {'directive_id':label_or_did}
        else:
            s = self._cur_parser().get_instruction_string('labeled_get_directive')
            d = {'label':label_or_did}
        return self.execute_instruction(s,d)['directive']

    def force(self, expression, value):
        s = self._cur_parser().get_instruction_string('force')
        d = {'expression':expression, 'value':value}
        self.execute_instruction(s,d)
        return None

    def sample(self, expression, type=False):
        s = self._cur_parser().get_instruction_string('sample')
        d = {'expression':expression}
        value = self.execute_instruction(s,d)['value']
        return value if type else value['value']
    
    def continuous_inference_status(self):
        s = self._cur_parser().get_instruction_string('continuous_inference_status')
        return self.execute_instruction(s)['running']

    def start_continuous_inference(self):
        s = self._cur_parser().get_instruction_string('start_continuous_inference')
        self.execute_instruction(s)
        return None

    def stop_continuous_inference(self):
        s = self._cur_parser().get_instruction_string('stop_continuous_inference')
        self.execute_instruction(s)
        return None

    def get_current_exception(self):
        s = self._cur_parser().get_instruction_string('get_current_exception')
        return self.execute_instruction(s,{})['exception']

    def get_state(self):
        s = self._cur_parser().get_instruction_string('get_state')
        return self.execute_instruction(s,{})['state']

    def get_logscore(self, label_or_did):
        if isinstance(label_or_did,int):
            s = self._cur_parser().get_instruction_string('get_logscore')
            d = {'directive_id':label_or_did}
        else:
            s = self._cur_parser().get_instruction_string('labeled_get_logscore')
            d = {'label':label_or_did}
        return self.execute_instruction(s,d)['logscore']

    def get_global_logscore(self):
        s = self._cur_parser().get_instruction_string('get_global_logscore')
        return self.execute_instruction(s,{})['logscore']

    ############################################
    # Profiler methods
    ############################################
    
    def profiler_configure(self, options={}):
        s = self._cur_parser().get_instruction_string('profiler_configure')
        d = {'options': options}
        return self.execute_instruction(s, d)['options']
    
    def profiler_enable(self):
        self.profiler_configure({'profiler_enabled': True})
        return None
    
    def profiler_disable(self):
        self.profiler_configure({'profiler_enabled': False})
        return None
    
    ############################################
    # Private methods
    ############################################

    def _cur_parser(self):
        return self.parsers[self.mode]

    def _extract_expression(self,directive_id):
        text = self.directive_id_to_string[directive_id]
        mode = self.directive_id_to_mode[directive_id]
        p = self.parsers[mode]
        args, arg_ranges = p.split_instruction(text)
        return args['expression'], arg_ranges['expression'][0]

