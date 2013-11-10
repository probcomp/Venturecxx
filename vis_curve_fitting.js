

function InitializeDemo() {

    var demo_id = 2;

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

    /* Stores the obs_id of points that the user has clicked on. */
    var points_to_forget = {};

    /* Latent variables in the model. */
    var model_variables = {
        'poly_order': 0,
        'a0_c0': 0.0,
        'c1': 0.0,
        'c2': 0.0,
        'c3': 0.0,
        'c4': 0.0,
        'noise': 0.1,
        'alpha': 0.5,
        'fourier_a1': 0.0,
        'fourier_omega': 1.0,
        'fourier_theta1': 0.0,
    };

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
    var local_points = {};

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
        ripl.clear();
        ripl.set_mode("church_prime");
        
        ripl.register_a_request_processed_callback(DirectiveLoadedCallback);
        
        /* Model metadata */
        ripl.assume('demo_id', demo_id, 'demo_id');
        
        /* Outliers */
        ripl.assume('outlier_prob','(uniform_continuous 0.001 0.3)'); //(beta 1 3)?
        ripl.assume('outlier_sigma','(uniform_continuous 0.001 100)'); //why random?
        ripl.assume('is_outlier','(mem (lambda (obs_id) (flip outlier_prob)))');
        
        /* Shared */
        ripl.assume('a0_c0','(normal 0.0 10.0)');
        
        /* Polynomial */
        ripl.assume('poly_order','(uniform_discrete 0 5)');
        ripl.assume('make_coefficient','(lambda (degree value) (if (>= poly_order degree) (normal 0.0 value) 0))');
        ripl.assume('c1','(make_coefficient 1 1.0)');
        ripl.assume('c2','(make_coefficient 2 0.1)');
        ripl.assume('c3','(make_coefficient 3 0.01)');
        ripl.assume('c4','(make_coefficient 4 0.001)');
        
        ripl.assume('clean_func_poly','(lambda (x) (+ (* c1 (power x 1.0)) (* c2 (power x 2.0)) (* c3 (power x 3.0)) (* c4 (power x 4.0))))');
        
        /* Fourier */
        ripl.assume('pi','3.14159');
        ripl.assume('fourier_a1','(normal 0.0 5.0)');
        ripl.assume('fourier_omega','(uniform_continuous 0 pi)');
        ripl.assume('fourier_theta1','(uniform_continuous (- 0 pi) pi)');

        ripl.assume('clean_func_fourier','(lambda (x) (* fourier_a1 (sin (+ (* fourier_omega x) fourier_theta1))))');

        /* For combination polynomial and Fourier */
        ripl.assume('model_type','(uniform_discrete 0 3)');
        ripl.assume('alpha','(if (= model_type 0) 1 (if (= model_type 1) 0 (beta 1 1)))');
        ripl.assume('clean_func','(lambda (x) (+ a0_c0 (* alpha (clean_func_poly x)) (* (- 1 alpha) (clean_func_fourier x))))');

        /* For observations */
        ripl.assume('noise','(inv_gamma 1.0 1.0)');
        ripl.assume('obs_fn','(lambda (obs_id x) (normal (if (is_outlier obs_id) 0 (clean_func (normal x noise))) (if (is_outlier obs_id) outlier_sigma noise)))');

        ripl.register_all_requests_processed_callback(AllDirectivesLoadedCallback);
    };
    
    var UpdateVentureCode = function(directives) {
        var venture_code_str = "<b>Venture code:</b><br>";

        for (i = 0; i < directives.length; i++) {
            venture_code_str += directiveToString(directives[i]) + '<br/>';
        }

        //venture_code_str = venture_code_str.replace(/ /g, "&nbsp;");
        //venture_code_str = venture_code_str.replace(/\(if/g, "(<font color='#0000FF'>if</font>");
        //venture_code_str = venture_code_str.replace(/\(/g, "<font color='#0080D5'>(</font>");
        //venture_code_str = venture_code_str.replace(/\)/g, "<font color='#0080D5'>)</font>");

        //venture_code_str = venture_code_str.replace(/lambda/g, "<font color='#0000FF'>lambda</font>");
        //venture_code_str = venture_code_str.replace(/list/g, "<font color='#0000FF'>list</font>");
        //venture_code_str = venture_code_str.replace(/\>=/g, "<font color='#0000FF'>>=</font>");
        //venture_code_str = venture_code_str.replace(/\+/g, "<font color='#0000FF'>+</font>");
        //venture_code_str = venture_code_str.replace(/\*/g, "<font color='#0000FF'>*</font>");
        venture_code_str = "<font face='Courier New' size='2'>" + venture_code_str + "</font>";
        $("#venture_code").html(venture_code_str);
    };
    
    var UpdateModelVariables = function(directives) {
        for(var i = 0; i < directives.length; i++) {
            var dir = directives[i];
            if(dir.instruction === "assume") {
                if(dir.symbol in model_variables) {
                    model_variables[dir.symbol] = dir.value;
                }
            }
        }
    }
    
    var xScale = 20;
    var yScale = -20;
    var xOffset = 210;
    var yOffset = 210;
    
    function modelToPaperX(x) {
        return (x * xScale) + xOffset;
    }
    function modelToPaperY(y) {
        return (y * yScale) + yOffset;
    }
    function paperToModelX(x) {
        return (x - xOffset) / xScale;
    }
    function paperToModelY(y) {
        return (y - yOffset) / yScale;
    }
    
    /* Adds a point to the GUI. */
    var MakePoint = function(p) {
        var local_point = {};
        
        local_point.obs_id = p.obs_id;
        
        local_point.paint_x = modelToPaperX(p.x);
        local_point.paint_y = modelToPaperY(p.y);
        
        local_point.noise_circle = paper.ellipse(
            local_point.paint_x, local_point.paint_y,
            0.25 * xScale, 0.25 * yScale);
        local_point.noise_circle.attr("fill", "white");
        //local_point.noise_circle.attr("opacity", "0.9");
        
        local_point.circle = paper.circle(local_point.paint_x, local_point.paint_y, 2);
        local_point.circle.attr("stroke", "white");
        //local_point.circle.attr("opacity", "0.5");
        
        local_point.circle.click(
            function(e) { 
                //console.log("click circle: (" + local_point.x + ", " + local_point.y + ")");
                points_to_forget[local_point.obs_id] = true;
            }
        );
        
        local_point.noise_circle.click(
            function(e) { 
                //console.log("click noise_circle: (" + local_point.x + ", " + local_point.y + ")");
                points_to_forget[local_point.obs_id] = true;
            }
        );
        
        return local_point;
    };
    
    var record = function(dict, path, value) {
        if (path.length > 1) {
            var key = path[0];
            if (!(key in dict)) {
                dict[key] = {};
            }
            record(dict[key], path.slice(1), value);
        } else {
            dict[path[0]] = value;
        }
    };
    
    /* Gets the points that are in the ripl. */
    var GetPoints = function(directives) {
        var points = {};

        var extract = function(directive) {
            var path = directive.label.split('_').slice(1);
            //console.log(path.join("."));
            record(points, path, directive.value);
            
            var did = directive.directive_id;
            var point = points[path[0]];
            
            //console.log(point.toString());
            
            if (!('dids' in point)) {
                point.dids = [];
            }
            point.dids.push(parseInt(did));
        };
        
        var observesAndPredicts =
            directives.filter(function(dir) {return dir.instruction in {"observe":true, "predict":true}});
        observesAndPredicts.forEach(extract);
        
        for (obs_id in points) {
            points[obs_id].obs_id = obs_id;
        }
        
        return points;
    };
        
    var ObservePoint = function(obs_id, x, y) {
        obs_str = 'points_' + obs_id;
        
        ripl.predict(x, obs_str + '_x');
        ripl.observe('(obs_fn ' + obs_id + ' ' + x + ')', y, obs_str + '_y');
        ripl.predict('(is_outlier ' + obs_id + ')', obs_str + '_outlier')
    };
    
    var DeletePoint = function(obs_id) {
        local_points[obs_id].noise_circle.remove();
        local_points[obs_id].circle.remove();
        delete local_points[obs_id];
    };
    
    var record = function(dict, path, value) {
        if (path.length > 1) {
            var key = path[0];
            if (!(key in dict)) {
                dict[key] = {};
            }
            record(dict[key], path.slice(1), value);
        } else {
            dict[path[0]] = value;
        }
    };
    
    /* Gets the points that are in the ripl. */
    var GetPoints = function(directives) {
        var points = {};

        var extract = function(directive) {
            var path = directive.label.split('_').slice(1);
            //console.log(path.join("."));
            record(points, path, directive.value);
            
            var did = directive.directive_id;
            var point = points[path[0]];
            
            //console.log(point.toString());
            
            if (!('dids' in point)) {
                point.dids = [];
            }
            point.dids.push(parseInt(did));
        };
        
        var observesAndPredicts =
            directives.filter(function(dir) {return dir.instruction in {"observe":true, "predict":true}});
        observesAndPredicts.forEach(extract);
        
        for (obs_id in points) {
            points[obs_id].obs_id = obs_id;
        }
        
        return points;
    };
    
    var DrawPoint = function(local_point, point) {
        color = point.outlier ? "gray" : "red";
        
        local_point.circle.attr("fill", color);
        local_point.noise_circle.attr("stroke", color);
        
        var factor = point.outlier ? 1.0 : Math.sqrt(model_variables.noise);
        local_point.noise_circle.attr("rx", 0.25 * Math.abs(xScale) * factor);
        local_point.noise_circle.attr("ry", 0.25 * Math.abs(yScale) * factor);
    };
    
    /* This is the callback that we pass to GET_DIRECTIVES_CONTINUOUSLY. */
    var RenderAll = function(directives) {
        //console.log("CLICKS TO ADD: " + JSON.stringify(clicks_to_add));
                
        UpdateVentureCode(directives);
        UpdateModelVariables(directives);
        
        /* Get the observed points from the model. */
        var points = GetPoints(directives);
        
        var current_curve = jQuery.extend({}, model_variables);
        current_curve.polynomial_coefficients = [
            current_curve.a0_c0,
            current_curve.c1,
            current_curve.c2,
            current_curve.c3,
            current_curve.c4,
        ];
        
        for (obs_id in points) {
            p = points[obs_id];

            /* If this user does not have a point object for it, make one. */
            if (!(obs_id in local_points)) {
                local_points[obs_id] = MakePoint(p);
            }
            
            /* Forget a point if it has been clicked on. */
            if (obs_id in points_to_forget) {
                for (var i = 0; i < p.dids.length; i++) {
                    ripl.forget(p.dids[i]);
                }
            }
        }
        
        /* Reset this after each round of directives has been processed. */
        points_to_forget = {};
        
        /* Remove nonexistent points and draw the rest. */
        for (obs_id in local_points) {
            if (!(obs_id in points)) {
                DeletePoint(obs_id);
            } else {
                DrawPoint(local_points[obs_id], points[obs_id]);
            }
        }
        
        /* Add points for every click on the canvas. */
        //console.log("before unique: " + JSON.stringify(clicks_to_add.getClicks()));
        clicks_to_add.uniqueF();
        //console.log("after unique: " + JSON.stringify(clicks_to_add.getClicks()));
        while (clicks_to_add.length() > 0) {
            //console.log("adding new point!");
            var click = clicks_to_add.shift();
            var x = paperToModelX(click[0]);
            var y = paperToModelY(click[1]);
            
            var obs_id = GetNextObsID();
            
            ObservePoint(obs_id, x, y);
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
    
    var ShowCurvesQ = function() {
        return document.getElementById('IfShowCurves').checked == true;
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
        <div id="venture_code"></div>\
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
        } else if (directives[0].symbol === "demo_id" && directives[0].value === demo_id) {
            RunDemo();
        } else {
            throw "Error: Something other than curve-fitting demo running in Venture."
        };
    });

};

