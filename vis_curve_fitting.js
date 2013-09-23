

function InitializeDemo() {

    var Curve = function(model_values) {
        this.poly_order = model_values[0];

        this.a0_c0 = model_values[1];
        this.c1 = model_values[2];
        this.c2 = model_values[3];
        this.c3 = model_values[4];
        this.c4 = model_values[5];

        this.polynomial_coefficients = [this.a0_c0,this.c1,this.c2,this.c3,this.c4];

        this.noise = model_values[6];
        this.alpha = model_values[7];
        this.fourier_a1 = model_values[8];
        this.fourier_omega = model_values[9];
        this.fourier_theta1 = model_values[10];
    };

    /* This is awkward because it looks like an array but requires some subtleties,
     * like calling .length() instead of .length. This is all because javascript
     * doesn't seem to have a deep equals. It used to be just some click-list methods,
     * which may be worth reverting to.
     */
    var ClickList = function() {
        var clicks = [];

        this.getClicks = function() {
            return clicks;
        };
        
        var clickEquals = function(click1,click2) {
            if (click1[0] == click2[0] && click1[1] == click2[1]) {
                return true;
            }
            return false;
        };

        this.shift = function() {
            return clicks.shift();
        };

        this.remove = function(from, to) {
            var rest = this.slice((to || from) + 1 || this.length);
            this.length = from < 0 ? this.length + from : from;
            return this.push.apply(this, rest);
        };

        this.indexOfClick = function(click) {
            for (var i = 0; i < clicks.length; i++) {
                if (clickEquals(clicks[i],click)) {
                    return i;
                }
            };
            return -1;
        };

        this.uniqueF = function() {
            var unique = [];
            for (var i = 0; i < clicks.length; i++) {
                if (this.indexOfClick(unique,clicks[i]) == -1) {
                    unique.push(clicks[i]);
                }
            }
            clicks = unique;
        };

        this.length = function() { return clicks.length; }

        this.push = function(click) {
            console.log("ADDING A CLICK!");
            clicks.push(click);
            console.log("clicks: " + clicks);
        };

    }

    var ArrayOfKeys = function(obj) {
        a = [];
        for (key in obj) { a.push(key); };
        return a;
    };

    //TODO this number is arbritrary, not sure how to get browser dependent
    //max int
    var LargeRandomInt = function() {
        return Math.floor(Math.random() * 10000000);
    }

    var ripl = new jripl();


    /* For the A_DIRECTIVE_LOADED callback to display status. */
    var num_directives_loaded = 0;

    /* A unique ID for each observation. */
    var next_obs_id = LargeRandomInt();
    var GetNextObsID = function() {
        id = next_obs_id;
        next_obs_id++;
        return id;
    };

    /* Stores every click that has occurred since the previous directives 
     * arrived. Clicks on the canvas are to be added, clicks on points are
     * to be forgotten. */
    var clicks_to_add = new ClickList();
    var clicks_to_forget = new ClickList();

    /* TODO ideally we iterate over this for the final PREDICT statement
     * in our generative model, but not worth the effort. */
    var random_variables = ['poly_order','a0_c0','c1','c2','c3','c4',
                            'noise','alpha','fourier_a1','fourier_omega',
                            'fourier_theta1'];
    /* We use this to go from the name of a random variable to its position 
     * in the predicted value. */
    var name_to_index = function(name) { random_variables.indexOf(name); };

    /* Polynomial orders (displayed upper-right) */
    var poly_orders = [];
    var poly_orders_histogram = [0,0,0,0,0];
    var num_poly_orders_stored = 0;
    var num_poly_orders_to_store = 100;
    var add_to_poly_orders = function(order) {
        if (poly_orders.length >= num_poly_orders_to_store) {
            num_poly_orders_stored--;
            poly_orders_histogram[poly_orders.shift()]--;
        };
        num_poly_orders_stored++;
        poly_orders.push(order);
        poly_orders_histogram[order]++;
    };

    var display_poly_orders_histogram = function() {
        poly_orders_histogram.map(
            function(value,degree) {
                document.getElementById('poly' + degree).style.height = Math.round(100 * value / num_poly_orders_stored) + 'px'
            }
        );
    };
    
    /* previous curve objects (for fading out) */
    var previous_curve_objects= [];
    var num_previous_curve_objects_stored = 0;
    var num_previous_curve_objects_to_store = 10;
    var add_previous_curve_object = function(curve_object) {
        if (previous_curve_objects.length >= num_previous_curve_objects_to_store) {
            num_previous_curve_objects_stored--;
            previous_curve_objects.pop();
        };
        num_previous_curve_objects_stored++;
        previous_curve_objects.unshift(curve_object);
    };

    /* Raphael Objects */
    var paper;
    var paper_rect;

    /* Will be a map from OBS_ID -> POINT, where POINT contains the Raphael objects
     * corresponding to a single point. */
    var points = {};

    var DirectiveLoadedCallback = function() {
        num_directives_loaded++;
        $("#loading-status").html("Demo is loading... <b>" + num_directives_loaded + '</b> directive(s) have been already loaded.');
    };

    var AllDirectivesLoadedCallback = function() {
        $("#loading-status").html("Demo loaded successfully!");
        $("#loading-status").remove();
        ripl.register_a_request_processed_callback(function () {});
    };

    var LoadModel = function() {
        ripl.set_mode("church_prime");
        ripl.clear();

        ripl.register_a_request_processed_callback(DirectiveLoadedCallback);

        /* Model metadata */
        ripl.assume('test_name','0');

        /* Outliers */
        ripl.assume('outlier_prob','(uniform_continuous 0.001 0.3)');
        ripl.assume('outlier_sigma','(uniform_continuous 0.001 100)');
        ripl.assume('is_outlierQ','(mem (lambda (obs_id) (flip outlier_prob)))');

        /* Shared */
        ripl.assume('a0_c0','(normal 0.0 10.0)');

        /* Polynomial */
        ripl.assume('poly_order','(uniform_discrete 0 4)');
        ripl.assume('make_coefficient','(lambda (degree value) (if (>= poly_order degree) (normal 0.0 value) 0))');
        ripl.assume('c1','(make_coefficient 1 1.0)');
        ripl.assume('c2','(make_coefficient 2 0.1)');
        ripl.assume('c3','(make_coefficient 3 0.01)');
        ripl.assume('c4','(make_coefficient 4 0.001)');

        ripl.assume('clean_func_poly','(lambda (x) (+ (* c1 (power x 1.0)) (* c2 (power x 2.0)) (* c3 (power x 3.0)) (* c4 (power x 4.0))))');
        
        /* Fourier */
        ripl.assume('pi','3.14');
        ripl.assume('fourier_a1','(normal 0.0 5.0)');
        ripl.assume('fourier_omega','(uniform_continuous (/ pi 50) pi)');
        ripl.assume('fourier_theta1','(uniform_continuous (* -1 pi) pi)');

        ripl.assume('clean_func_fourier','(lambda (x) (* fourier_a1 (sin (+ (* fourier_omega x) fourier_theta1))))');

        /* For combination polynomial and Fourier */
        ripl.assume('model_type','(uniform_discrete 0 2)');
        ripl.assume('alpha','(if (= model_type 0) 1 (if (= model_type 1) 0 (beta 1 1)))');
        ripl.assume('clean_func','(lambda (x) (+ a0_c0 (* alpha (clean_func_poly x)) (* (- 1 alpha) (clean_func_fourier x))))');

        /* For observations */
        ripl.assume('noise','(uniform_continuous 0.1 1.0)');
        ripl.assume('obs_fn','(lambda (obs_id x) (normal (if (is_outlierQ obs_id) 0 (clean_func (normal x noise))) (if (is_outlierQ obs_id) outlier_sigma noise)))');

        /* One predict for every quantity of interest.
        Ideally this would iterate over RANDOM_VARIABLES. */
        ripl.predict('(list poly_order a0_c0 c1 c2 c3 c4 noise alpha fourier_a1 fourier_omega fourier_theta1)','predict_model');

        ripl.register_all_requests_processed_callback(AllDirectivesLoadedCallback);
    };

    var ShowCurvesQ = function() {
        return document.getElementById('IfShowCurves').checked == true;
    };

    var UpdateChurchCode = function(directives) {
        var church_code_str = "<b>Venture code:</b><br>";

        for (i = 0; i < directives.length; i++) {
            church_code_str += directiveToString(directives[i]) + '<br/>';
        }

        church_code_str = church_code_str.replace(/ /g, "&nbsp;");
        church_code_str = church_code_str.replace(/\(if/g, "(<font color='#0000FF'>if</font>");
        church_code_str = church_code_str.replace(/\(/g, "<font color='#0080D5'>(</font>");
        church_code_str = church_code_str.replace(/\)/g, "<font color='#0080D5'>)</font>");

        church_code_str = church_code_str.replace(/lambda/g, "<font color='#0000FF'>lambda</font>");
        church_code_str = church_code_str.replace(/list/g, "<font color='#0000FF'>list</font>");
        church_code_str = church_code_str.replace(/\>=/g, "<font color='#0000FF'>>=</font>");
        church_code_str = church_code_str.replace(/\+/g, "<font color='#0000FF'>+</font>");
        church_code_str = church_code_str.replace(/\*/g, "<font color='#0000FF'>*</font>");
        church_code_str = "<font face='Courier New' size='2'>" + church_code_str + "</font>";
        $("#church_code").html(church_code_str);
    };

    /* This is the callback that we pass to GET_DIRECTIVES_CONTINUOUSLY. */
    var RenderAll = function(directives) {
        //console.log("CLICKS TO ADD: " + JSON.stringify(clicks_to_add));
        
        UpdateChurchCode(directives);

        var observations = directives.filter(function(dir) { return dir.instruction === "observe" });

        /* [model_predictions, outlier_pred1, ..., outlier_predN] */
        var predictions = directives.filter(function(dir) { return dir.instruction === "predict" });

        var model_prediction = predictions.shift();
        var model_predicted_value = model_prediction.value;

        var current_curve = new Curve(model_predicted_value);

        /* Bookkeeping so we can delete forgotten points from POINTS. */
        var current_obs_ids = [];

        /* Process every observation. */
        observations.map(
            function(observation) {
                values = ParseObservation(predictions,observation);
                
                /* This user already CLICKED on the point, indicating that he
                * wants to forget it. */
                var click_index = clicks_to_forget.indexOfClick([values.x,values.y]);
                if (click_index != -1) {
                    ripl.forget(values.directive_id_pred.toString());
                    ripl.forget(values.directive_id_obs.toString());
                    return;
                };
                
                /* Otherwise, we register that the POINT is still active. */
                current_obs_ids.push(values.obs_id.toString());

                /* If this user does not have a point object for it,
                * make one. */
                if (!(values.obs_id in points)) {
                    var point = MakePoint(values.x,values.y);

                    point.obs_id = values.obs_id;
                    point.directive_id_pred = values.directive_id_pred;
                    point.directive_id_obs = values.directive_id_obs;
                    points[point.obs_id] = point;
                }

                /* Color it depending on whether it is an outlier. */
                if (values.isOutlierQ) {
                    points[values.obs_id].circle.attr("fill", "#888888");
                    points[values.obs_id].noise_circle.attr("stroke", "#888888");
                    points[values.obs_id].noise_circle.attr("r", 5.0);
                } else {
                    points[values.obs_id].circle.attr("fill", "red");
                    points[values.obs_id].noise_circle.attr("stroke", "red");
                    points[values.obs_id].noise_circle.attr("r", current_curve.noise * 10.0);
                }
            }
        );

        /* Reset this after each round of directives has been processed. */
        clicks_to_forget = new ClickList();

        /* Delete points for which there is no observation. */
        for (obs_id in points) {
            if ($.inArray(obs_id, current_obs_ids) == -1) {
                points[obs_id].noise_circle.remove();
                points[obs_id].circle.remove();
                delete points[obs_id];
            }
        }

        /* Add points for every click on the canvas. */
        console.log("before unique: " + JSON.stringify(clicks_to_add.getClicks()));
        clicks_to_add.uniqueF();
        console.log("after unique: " + JSON.stringify(clicks_to_add.getClicks()));
        while (clicks_to_add.length() > 0) {
            console.log("adding new point!");
            var click = clicks_to_add.shift();
            var obs_id = GetNextObsID();
            ripl.predict('(is_outlierQ ' + obs_id + ')');
            ripl.observe('(obs_fn ' + obs_id + ' ' + ((click[0] - 210)/20) + ')',((click[1] - 210)/-20).toString());
        }

        /* Process polynomial orders and display results. */
        add_to_poly_orders(current_curve.poly_order);
        display_poly_orders_histogram();

        // Change opacity of previously drawn polynomials.
        previous_curve_objects.map(
            function(curve,i) {
                scaled_i = i * 40;
                previous_curve_objects[i].attr("stroke", "#" + scaled_i.toString(16) + scaled_i.toString(16) + scaled_i.toString(16));
            }
        );

        /* Save current polynomial, to be faded out in the future. */
        add_previous_curve_object(DrawCurve(current_curve));

        /* Make every curve invisible if SHOWCURVES is not checked. */
        if (!ShowCurvesQ()) {
            previous_curve_objects.map(
                function(curve_object) {
                    curve_object.attr("stroke-opacity", "0.0");
                }
            );
        }
    };

    var CalculateCurve = function(x,curve) {
        var result_poly = 0;
        for (var i = 1; i < curve.polynomial_coefficients.length; ++i) {
            result_poly += curve.polynomial_coefficients[i] * Math.pow(x, i);
        }
        var result_f = curve.fourier_a1 * Math.sin(curve.fourier_omega * x + curve.fourier_theta1);
        result = curve.polynomial_coefficients[0] + curve.alpha * result_poly + (1.0 - curve.alpha) * result_f;
        return result;
    };

    var DrawCurve = function(curve) {
        var step = 1;
        var plot_y = (420 / 2) - CalculateCurve(-10, curve) * 20;
        var line_description = "M-10 " + plot_y;
        var plot_x1 = 0;
        var plot_y1 = 0;
        var plot_x = 0;
        var plot_y = 0;
        for (var x = -12 + step; x <= 12; x = x + step) {
            plot_x = (420 / 2) + x * 20;
            plot_y = (420 / 2) - CalculateCurve(x, curve) * 20;
            plot_x1 = (420 / 2) + (x + step / 2) * 20;
            plot_y1 = (420 / 2) - CalculateCurve(x + step / 2, curve) * 20;
            line_description += "Q" + plot_x + " " + plot_y + " " + plot_x1 + " " + plot_y1;
        }
        var curve_object = paper.path(line_description);
        return curve_object;
    };

    var RenderGrid = function() {
        for (var x = 0; x <= 400; x = x + (400) / 10) {
            currentObject = paper.path("M" + (x + 10) + " 0L" + (x + 10) + " 420");
            currentObject.attr("stroke-dasharray", "-");
            currentObject.attr("stroke-width", "0.2");
            currentObject = paper.path("M0 " + (x + 10) + "L420 " + (x + 10) + "");
            currentObject.attr("stroke-dasharray", "-");
            currentObject.attr("stroke-width", "0.2");

            currentObject = paper.text(x + 10, 15, "" + (((x / 40) - 5) * 2) + "");
            currentObject.attr("fill", "#aaaaaa");

            if (x != 0) {
                currentObject = paper.text(10, x + 10, "" + (((x / 40) - 5) * -2) + "");
                currentObject.attr("fill", "#aaaaaa");
            }
        }

        currentObject = paper.circle(420 / 2, 420 / 2, 2);
        currentObject = paper.text(420 / 2 + 20, 420 / 2, "(0; 0)");
        currentObject.attr("fill", "#aaaaaa");
    };


    var MakePoint = function(x,y) {
        var point = new Object();

        point.x = x;
        point.y = y;

        point.paint_x = (point.x * 20) + 210;
        point.paint_y = (point.y * -20) + 210;

        point.noise_circle = paper.circle(point.paint_x, point.paint_y, 5);
        point.noise_circle.attr("stroke", "red");
        point.noise_circle.attr("fill", "white");
        point.noise_circle.attr("opacity", "0.9");

        point.circle = paper.circle(point.paint_x, point.paint_y, 2);
        point.circle.attr("fill", "red");
        point.circle.attr("stroke", "white");
        point.circle.attr("opacity", "0.5");

        point.circle.click(
            function(e) { 
                console.log("click circle: (" + point.x + ", " + point.y + ")");
                clicks_to_forget.push([point.x,point.y]); 
            }
        );

        point.noise_circle.click(
            function(e) { 
                console.log("click noise_circle: (" + point.x + ", " + point.y + ")");
                clicks_to_forget.push([point.x,point.y]); 
            }
        );

        return point;

    };

    var GetPredictionForObsID = function(predictions,obs_id) {
        for (i = 0; i < predictions.length; i++) {
            if (predictions[i].expression[1].value === obs_id) {
                return predictions[i];
            }
        }
        throw "PREDICTION NOT FOUND! -- " + JSON.stringify(predictions) + ", (obs_id): " + obs_id;
    };

    var ParseObservation = function(predictions,observation) {
        var values = new Object();
        values.obs_id = observation.expression[1].value;
        values.directive_id_obs = observation.directive_id;

        var prediction = GetPredictionForObsID(predictions,values.obs_id);

        values.directive_id_pred = prediction.directive_id;
        values.isOutlierQ = prediction.value;

        values.x = observation.expression[2].value;
        values.y = observation.value;

        return values;
    }

    var DeletePoint = function(point) {
        point.noise_circle.remove();

        ripl.forget(point.directive_id_pred.toString());
        ripl.forget(point.directive_id_obs.toString());

        point.circle.remove();
        delete points[point.obs_id];
    };


    // Initialize the canvas, and necessary variables.
    var RenderInit = function() {
        paper = Raphael('div_for_plots', 420, 420);
        paper_rect =  paper.rect(0, 0, 420, 420).attr({fill: "white"});

        RenderGrid();

        paper_rect.click(function(e) {
            clicks_to_add.push([e.pageX - $('#div_for_plots').offset().left,
            e.pageY - $('#div_for_plots').offset().top]);
        });
    };


    // // The main curve fitting HTML code.
    var InsertHTML = function(divclass) {
        $('.'+divclass).html('\
        <h3><a href="https://github.com/perov/simpleinterpreter/">Bayesian Curve Fitting Demo</a></h3>\
        <div id="working_space" style="display: ;">\
        <table><tr><td style="vertical-align: top;">\
        <div id="div_for_plots" style="background-color: white; width: 420px; height: 420px;"></div>\
        <br>\
        <label for="IfShowCurves"><input type="checkbox" id="IfShowCurves" name="IfShowCurves" checked> Show curves</label>\
        <div>\
        <div class="btn-group">\
        <button class="btn btn-danger">Engine Status</button>\
        <button class="btn btn-danger dropdown-toggle" data-toggle="dropdown"><span class="caret"></span></button>\
        <ul class="dropdown-menu">\
        </ul>\
        </div>\
        </div>\
        <br>\
        <a href="graphingCurvefittingSimplified_simple.html">Basic demo.</a> <a href="http://www.yuraperov.com/MIT.PCP/demo.html">Return to the list of demos.</a>\
        <br><br>\
        Based on the Venture probabilistic programming language\
        </td><td>&nbsp;&nbsp;&nbsp;</td>\
        <td style="vertical-align: top;">\
        <table width="100%" height="120px">\
        <tr>\
        <td width="30px" valign="bottom"><b>Degree:</b></td>\
        <td width="30px" align="center" valign="bottom"><div id="poly0" style="width: 20px; height: 50px; background-color: #ee1111;"></div><br>0</td>\
        <td width="30px" align="center" valign="bottom"><div id="poly1" style="width: 20px; height: 50px; background-color: #ee1111;"></div><br>1</td>\
        <td width="30px" align="center" valign="bottom"><div id="poly2" style="width: 20px; height: 50px; background-color: #ee1111;"></div><br>2</td>\
        <td width="30px" align="center" valign="bottom"><div id="poly3" style="width: 20px; height: 50px; background-color: #ee1111;"></div><br>3</td>\
        <td width="30px" align="center" valign="bottom"><div id="poly4" style="width: 20px; height: 50px; background-color: #ee1111;"></div><br>4</td>\
        <td width="20px"></td>\
        <td valign="bottom" align="right">\
        \
        </td>\
        </tr>\
        </table>\
        <br>\
        <div id="church_code"></div>\
        <div style="display: none;"><div style="display: none;"><input type="text" id="iteration_info" style="border:0; background-color: white;" value="" disabled></div>\
        <div id="slider" style="width: 500px; font-size: 10; display: none;"></div>\
        <div id="function_formula"></div>\
        <div id="noise_value"></div>\
        Number of MH burn-in iterations: <input type="text" id="number_of_MH_burnin_iterations" value="100" style="width: 50px;">\
        <input type="hidden" id="number_of_steps_to_show" value="1">\
        start from\
        <input type="radio" id="where_start_the_burnin__from_prior" name="where_start_the_burnin" value="from_prior"> the prior\
        <input type="radio" id="where_start_the_burnin__from_last_state" name="where_start_the_burnin" value="from_last_state" checked> the last state\
        <br>Polynomial degree (from 0 to 4 inclusive): <input type="text" id="polynomial_degree" value="4" style="width: 20px;">\
        <br>\
        <table><tr><td valign="top" style="width: 450px;">\
        <br><br></div>\
        </td><td>&nbsp;</td>\
        <td valign="top">\
        <small>\
        Noise type:\
        <input type="radio" name="noise_type" id="noise_type__uni_cont" checked> U[0.1; 1.0]\
        <input type="radio" name="noise_type" id="noise_type__beta1"> &beta;(1, 3)\
        <input type="radio" name="noise_type" id="noise_type__beta2"> &beta;(1, 3) * 0.9 + 0.1\
        </small>\
        <br>\
        <input type="radio" name="coeff_type" id="coeff_type__decr" checked> Decreasing coefficients (normal)<br>\
        <input type="radio" name="coeff_type" id="coeff_type__ident_sigma10"> Identical coefficients (normal, sigma = 10)<br>\
        <input type="radio" name="coeff_type" id="coeff_type__ident_sigma1"> Identical coefficients (normal, sigma = 1)<br>\
        <input type="radio" name="coeff_type" id="coeff_type__incr"> Increasing coefficients (normal)<br>\
        <input type="radio" name="coeff_type" id="coeff_type__ident_uniform"> Via &beta;<br>\
        <input type="checkbox" id="center_is_random"> If the center of distribution on coefficients is random<br>\
        <input type="checkbox" id="a_is_random" disabled> If the center of polynomial is random\
        </td></tr>\
        </table>\
        <br><div id="polynomialListbox" style="display: none;"></div>\
        <br><input type="button" value="Do inference" id="do_inference_button" style="display: none;">\
        </td></tr></table>\
        </div>\
        <div id="forced_disconnection" style="display: none;">\
        Oh, no, you has been disconnected from the SimpleInterpreter cloud.<br>\
        It is not very good. I am sorry about it.<br>\
        Please, contact Yura Perov (<a href="mailto:yura.perov@gmail.com">yura.perov@gmail.com</a>)\
        about this issue.\
        </div>\
        ');
    };

    var RunDemo = function() {
        ripl.get_directives_continuously(
            [[50, 
            RenderAll,
            []]] // empty list means get all directives
        );
    };

    /* START CODE */
    InsertHTML('vis_holder');
    RenderInit();

    ripl.get_directives_once(function(directives) {
        if (directives.length == 0) {
            // fresh Venture instance
            LoadModel();
            ripl.start_continuous_inference();
            RunDemo();
        } else if (directives[0].symbol === "test_name" && directives[0].value === 0) {
            RunDemo();
        } else {
            throw "Error: Something other than curve-fitting demo running in Venture."
        };
    });

};

