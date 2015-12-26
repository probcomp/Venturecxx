// Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

/* Description: Javascript library for communicating with Venture's RIPL
 * asynchronously, to assist in the development of Web demos.
 *  
 * Design Overview: A JRIPL object is essentially a wrapper around the
 * Python-layer RIPL class, except everything is made asynchronous so that
 * no values are returned from functions. All interaction with Venture is 
 * done via callbacks.
 *
 * Extensions: There are other RIPL functions that return values, that we 
 * may want to support via callbacks, such as GET_LOG_SCORE(). One option
 * is to add <pripl_function>_once(f,args) and 
 * <pripl_function>_continuously(time,f,args) for every function supported
 * by PRIPL.
 * 
 * Author: Daniel Selsam
 */

function jripl() {

/* Connect to Venture (vestigial hack) */
    CheckCookieWithVentureRIPLAddress();
    var server_url = 'http://' + $.cookie('venture__ripl_host') + ':';
    var port = $.cookie('venture__ripl_port');


/* URL utilities */
    var full_url = function(url) {
        return server_url + port + "/" + url;
    };

/* Status booleans */
    var request_in_progressQ = false;
    var get_directives_in_progressQ = false;

/* Private data */
    var request_queue = [];

/* Registered callbacks */

    /* Will be called everytime a request is processed. */
    var a_request_processed_callback = function() {};

    /* Will be called once whenever the queue next becomes empty. */
    var all_requests_processed_callback = function() {};

/* AJAX Utilities */

    /* Called during success callback for ajax requests
     * Asynchronously performs next request in queue.
     */
    var ajax_continue_requests = function() {
        if (request_queue.length > 0) {
            var next_request = request_queue.shift();
            ajax_execute_post(next_request.url, next_request.data_in, next_request.on_success);
        }
        else {
            request_in_progressQ = false;
            all_requests_processed_callback();
            all_requests_processed_callback = function() {};
        }
    };

    /* Send via AJAX in sequence, going through the request queue. */
    var ajax_post_in_sequence = function(URL,data_in,on_success) {
        if (request_in_progressQ) {
            request_queue.push({url: URL, 
                                data_in: data_in,
                                on_success: on_success});
        } 
        else {
            request_in_progressQ = true;
            ajax_execute_post(URL,data_in,on_success);
        }
    };
    
    this.method = ajax_post_in_sequence

    /* Perform the actual AJAX request. */
    var ajax_execute_post = function(URL,data_in,on_success) {
        var then = Date.now()
        console.log("Ajax request sent", request_queue.length, "left in queue")
        $.ajax({
            url: full_url(URL),
            type:'POST', 
            data: JSON.stringify(data_in),
            dataType: 'json',
            contentType: 'application/json',
            crossDomain: true,
            success: function(data) {
                now = Date.now();
                console.log("Ajax response received", now - then, "ms delay");
                a_request_processed_callback();
                on_success(data);
                ajax_continue_requests();
            },
            // TODO this error callback needs updating
            error: function(data) { 
                console.log("Got an error", data);
                ajax_continue_requests();
            },
            complete: function() {}
        });
    };

    
    /* These functions are all supported, and can be called just as in
     * the python layer, except the user cannot receive the return values.
     */
    var supported_pripl_functions = ['set_mode', 'execute_instruction', 'execute_program', 'split_program', 'expression_index_to_text_index', 'configure', 'infer', 'clear', 'rollback', 'assume', 'predict', 'observe', 'forget', 'force', 'sample', 'start_continuous_inference', 'stop_continuous_inference', 'continuous_inference_status'];

    /* Creates a function corresponding to one of the supported pripl functions 
     * listed above. */
    var create_closure = function(name, on_success) {
        return function() {
            ajax_post_in_sequence(name,
                                  Array.prototype.slice.call(arguments, 0), 
                                  on_success);
        };
    };

    /* Dynamically add supported pripl functions to JRIPL. */  
    for (i = 0; i < supported_pripl_functions.length; i++) {
        var name = supported_pripl_functions[i];
        this[name] = create_closure(name, function() {});
    };

    var pripl_functions_w_retval = ['assume_async','predict_async','observe_async'];

    for (i = 0; i < pripl_functions_w_retval.length; i++) {
        var name = pripl_functions_w_retval[i];
        var closure_name = name.substr(0,name.length-6);
        var on_success = function(data_in, data) {
               console.log(data);
               if(data != null) {
                       term.echo(data_in[0] + " | " + data)
               }
        }
        this[name] = create_closure(closure_name, on_success);
    };

    /* FIXME: write these, adding logs to term-mang.js to show that the procs are geting called with the
     * right arguments, returning the right values, and calling these versions for non-"example" mode */

    this['real_infer'] = function (num_iters) {
            ajax_post_in_sequence("infer", [num_iters], function () {
                    echo_str = "real_infer(" + num_iters + ")";
                    console.log(echo_str);
                    // term.echo(echo_str);
            });
    }

    this['real_forget'] = function (directive_id) {
            ajax_post_in_sequence("forget", [directive_id], function () {
                    echo_str = "real_forget(" + directive_id + ")";
                    console.log(echo_str);
                    // term.echo(echo_str);
            });
    }

    this['real_observe'] = function (expression, literal) {
            ajax_post_in_sequence("observe", [expression, literal], function () {
                    echo_str = "real_observe(" + expression + ", " + literal + ")";
                    console.log(echo_str);
                    // term.echo(echo_str);
            });
    }

/* Continuous directives */

/* TODO This section will need some tweaking moving forward.
 * I am not sure the best way to handle this, since I cannot
 * imagine even a single use case for running multiple sequences
 * at once. I expect we will revert this to a simpler form, and
 * have lower Venture layers offer a list of all directives that
 * have changed since this user has last been updated.
 */

    /* get_directives_continuously(seq) takes a list
     * [ [time1, f1, list-of-jids (optional)],
     *   ...,
     *   [timeN, fN, list-of-jids (optional)] ]
     * Right now, use only one list and do not pass anything to list-of-jids
     * to receive all directives.
     */
    var process_directives = function(time,f,ids) {
        return function(directives) {
            f(directives);
            get_directives_later(time,f,ids);
        };
    };

    var get_directives_later = function(time,f,ids) {
        setTimeout(
            function () {
                get_directives_recursively(time,f,ids);
            },
            time);
    };

    var get_directives_recursively = function(time,f,ids) {
        if (request_in_progressQ) {
            // Wait until all other requests have come back
            get_directives_later(time,f,ids);
        }
        else {
            ajax_post_in_sequence("list_directives",
                                  [],
                                  // ids, (see note above)
                                  process_directives(time,f,ids));
        };
    };

    /* This the user-facing function. */
    this.get_directives_continuously = function(list_of_time_f_ids) {
        if (get_directives_in_progressQ) {
            throw "Error: already getting directives continuously!"
        }
        else {
            get_directives_in_progressQ = true;
            for (i = 0; i < list_of_time_f_ids.length; i++) {
                var time = list_of_time_f_ids[i][0];
                var f = list_of_time_f_ids[i][1];
                var ids = list_of_time_f_ids[i][2];
                get_directives_recursively(time,f,ids);
            };
        };
    };

    this.get_directives_once = function(f) {
        ajax_post_in_sequence("list_directives", [], f);
    };
    
    /*
    this.display_directives = function() {
        var success_fun = function(data) {
            console.log(data);
            column_names = ["Directives", "Instruction", "Values", "Ids"];
            header = join_for_console(column_names);
            term.echo(header);
            for (i = 0; i < data.length; i++){
                sym = undefined_to_empty_str(data[i].symbol + "");
                exp = undefined_to_empty_str(data[i].expression + "");
                val = undefined_to_empty_str(data[i].value + "");
                directive_id = undefined_to_empty_str(data[i].directive_id + "");
                joined = join_for_console([sym, exp, val, directive_id]);
                term.echo(joined);
            }
        }
        ajax_post_in_sequence("list_directives", [], success_fun);
    };
    */
    
/* Registering special callback functions */
    this.register_a_request_processed_callback = function(f) {
        a_request_processed_callback = f;
    }

    
/* The user will register this callback after sending all requests of interest.
   If the request_queue is empty, all such requests have all been processed, and
   so we call the callback. Otherwise, the next time it becomes empty, we call the
   callback. Either way, we reset the callback.
   Use case: after the program has loaded, synchronize on all confirmation of all
   directives being received by Venture.
 */
    this.register_all_requests_processed_callback = function(f) {
        if (request_in_progressQ || request_queue.length > 0) {
            all_requests_processed_callback = f;
        }
        else {
            f();
            all_requests_process_callback = function() {};
        };
    };


};

jripl.prototype.seed = function (seedval,cb)
{
    $.post(this.server_url,seedval,cb);
};
