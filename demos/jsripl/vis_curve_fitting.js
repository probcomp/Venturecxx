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


function InitializeDemo() {

    var demo_id = 2;

    var inference_program = "(mh default one 10)"

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
            if (click1[0] === click2[0] && click1[1] === click2[1]) {
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
            for (var i = 0; i < clicks.length; ++i) {
                if (clickEquals(clicks[i],click)) {
                    return i;
                }
            };
            return -1;
        };

        this.uniqueF = function() {
            var unique = [];
            for (var i = 0; i < clicks.length; ++i) {
                if (this.indexOfClick(unique,clicks[i]) === -1) {
                    unique.push(clicks[i]);
                }
            }
            clicks = unique;
        };

        this.length = function() { return clicks.length; }

        this.push = function(click) {
            //console.log("ADDING A CLICK!");
            clicks.push(click);
            //console.log("clicks: " + clicks);
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
    var next_obs_id = 0; // LargeRandomInt();
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

    var model_types = ["simple", "advanced"];

    /* Latent variables in the model. */
    var model_variables = {
        /* Both */
        model_type: "simple",
        infer_noise: false,
        use_outliers: false,
        show_scopes: false,
        noise: 0.1,

        /* Simple */
        a: 0,
        b: 0,

        /* Advanced */
        poly_order: 0,
        a0_c0: 0.0,
        c1: 0.0,
        c2: 0.0,
        c3: 0.0,
        c4: 0.0,
        alpha: 0.5,
        fourier_a1: 0.0,
        fourier_omega: 1.0,
        fourier_theta1: 0.0,
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

    var points = {};

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
        ripl.infer("(loop " + inference_program + ")");
        ripl.register_a_request_processed_callback(function () {});
    };

    var LoadSimpleModel = function() {
        ripl.clear();
        ripl.set_mode("church_prime");

        /* Model metadata */
        ripl.assume('demo_id', demo_id, 'demo_id');
        ripl.assume('model_type', '(quote simple)', 'model_type');
        ripl.assume('use_outliers', "" + model_variables.use_outliers, 'use_outliers');
        ripl.assume('infer_noise', "" + model_variables.infer_noise, 'infer_noise');
        ripl.assume('show_scopes', "" + model_variables.show_scopes, 'show_scopes');

        if (model_variables.use_outliers) {
            ripl.assume('outlier_prob','(uniform_continuous 0.001 0.3)'); //(beta 1 3)?
            ripl.assume('is_outlier','(mem (lambda (obs_id) (flip outlier_prob)))');
        }

        /* Linear */
        ripl.assume('a','(normal 0.0 10.0)');
        ripl.assume('b','(normal 0.0 3.0)');
        ripl.assume('f','(lambda (x) (+ a (* b x)))');

        ripl.assume('noise', model_variables.infer_noise ? '(sqrt (inv_gamma 2.0 1.0))' : '1.0')

        if (model_variables.use_outliers) {
            ripl.assume('obs_fn','(lambda (obs_id x) (normal (if (is_outlier obs_id) 0 (f (normal x noise))) (if (is_outlier obs_id) 100 noise)))');
        } else {
            ripl.assume('obs_fn','(lambda (obs_id x) (normal (f (normal x noise)) noise))');
        }
    };

    var LoadAdvancedModel = function() {
        ripl.clear();
        ripl.set_mode("church_prime");

        /* Model metadata */
        ripl.assume('demo_id', demo_id, 'demo_id');
        ripl.assume('model_type', '(quote advanced)', 'model_type');

        /* Outliers */
        if (model_variables.use_outliers) {
            ripl.assume('outlier_prob','(tag (quote params) 0 (uniform_continuous 0.001 0.3))'); //(beta 1 3)?
            ripl.assume('outlier_sigma','(tag (quote params) 1 (uniform_continuous 0.001 100))'); //why random?
            ripl.assume('is_outlier','(mem (lambda (obs_id) (tag (quote outliers) obs_id (flip outlier_prob))))');
        }

        /* Shared */
        ripl.assume('a0_c0','(tag (quote params) 2 (normal 0.0 10.0))');

        /* Polynomial */
        ripl.assume('poly_order','(tag (quote structure) 0 (uniform_discrete 0 5))');
        ripl.assume('make_coefficient','(lambda (degree value) (if (>= poly_order degree) (tag (quote params) (+ 2 degree) (normal 0.0 value)) 0))');
        ripl.assume('c1','(make_coefficient 1 3.0)');
        ripl.assume('c2','(make_coefficient 2 1.0)');
        ripl.assume('c3','(make_coefficient 3 0.3)');
        ripl.assume('c4','(make_coefficient 4 0.1)');

        ripl.assume('clean_poly','(lambda (x) (+ (* c1 (pow x 1.0)) (* c2 (pow x 2.0)) (* c3 (pow x 3.0)) (* c4 (pow x 4.0))))');

        /* Fourier */
        ripl.assume('pi','3.14159');
        ripl.assume('fourier_a1','(tag (quote params) 7 (normal 0.0 5.0))');
        ripl.assume('fourier_omega','(tag (quote params) 8 (uniform_continuous 0 pi))');
        ripl.assume('fourier_theta1','(tag (quote params) 9 (uniform_continuous (- 0 pi) pi))');

        ripl.assume('clean_fourier','(lambda (x) (* fourier_a1 (sin (+ (* fourier_omega x) fourier_theta1))))');

        /* For combination polynomial and Fourier */
        ripl.assume('poly_fourier_mode','(tag (quote structure) 1 (uniform_discrete 0 3))');
        ripl.assume('alpha','(if (= poly_fourier_mode 0) 1 (if (= poly_fourier_mode 1) 0 (tag (quote params) 10 (beta 1 1))))');
        ripl.assume('clean_func','(lambda (x) (+ a0_c0 (* alpha (clean_poly x)) (* (- 1 alpha) (clean_fourier x))))');

        /* For observations */
        ripl.assume('noise', model_variables.infer_noise ? '(sqrt (tag (quote params) 11 (inv_gamma 2.0 1.0)))' : '1.0');
        if (model_variables.use_outliers) {
            ripl.assume('obs_fn','(lambda (obs_id x) (normal (if (is_outlier obs_id) 0 (clean_func (normal x noise))) (if (is_outlier obs_id) outlier_sigma noise)))');
        } else {
            ripl.assume('obs_fn','(lambda (obs_id x) (normal (clean_func (normal x noise)) noise))');
        }
    };

    var modelLoaders = {simple: LoadSimpleModel, advanced: LoadAdvancedModel};

    var LoadModel = function() {
        num_directives_loaded = 0;
        ripl.register_a_request_processed_callback(DirectiveLoadedCallback);
        ripl.stop_continuous_inference();
        modelLoaders[model_variables.model_type]();

        ripl.register_all_requests_processed_callback(AllDirectivesLoadedCallback);
    };

    var UpdateVentureCode = function(directives) {
        code = VentureCodeHTML(directives, getShowScopes());
        code += "[infer (loop " + inference_program + ")]";
        code = "<font face='Courier New' size='2'>" + code + "</font>";
        $("#venture_code").html(code);
    };

    var UpdateModelVariables = function(directives) {
        for(var i = 0; i < directives.length; ++i) {
            var dir = directives[i];
            if(dir.instruction === "assume") {
                if(dir.symbol.value in model_variables) {
                    model_variables[dir.symbol.value] = dir.value;
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
        points = {};

        var extract = function(directive) {
            var path = directive.label.value.split('_').slice(1);
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

        var observesAndPredicts = directives.filter(function(dir) {return dir.instruction != "assume";});
        observesAndPredicts.forEach(extract);

        for (obs_id in points) {
            points[obs_id].obs_id = obs_id;
        }
    };

    var ObservePoint = function(obs_id, x, y) {
        obs_str = 'points_' + obs_id;

        ripl.predict(x, obs_str + '_x');
        ripl.observe('(obs_fn ' + obs_id + ' ' + x + ')', y, obs_str + '_y');
        if (!model_variables.use_outliers) {
            ripl.predict('false', obs_str + '_outlier');
        } else {
            ripl.predict('(is_outlier ' + obs_id + ')', obs_str + '_outlier');
        }
    };

    var DeletePoint = function(obs_id) {
        local_points[obs_id].noise_circle.remove();
        local_points[obs_id].circle.remove();
        delete local_points[obs_id];
    };

    var ForgetPoints = function() {
        for (obs_id in points) {
            p = points[obs_id];
            for (var i = 0; i < p.dids.length; ++i) {
                ripl.forget(p.dids[i]);
            }
        }
    };

    var DrawPoint = function(local_point, point) {
        color = point.outlier ? "gray" : "red";

        local_point.circle.attr("fill", color);
        local_point.noise_circle.attr("stroke", color);

        var factor = point.outlier ? 1.0 : Math.sqrt(model_variables.noise);
        local_point.noise_circle.attr("rx", 0.25 * Math.abs(xScale) * factor);
        local_point.noise_circle.attr("ry", 0.25 * Math.abs(yScale) * factor);
    };

    var CheckModelVariables = function() {
        var model_type = getModelType();
        var use_outliers = getUseOutliers();
        var infer_noise = getInferNoise();
        var show_scopes = getShowScopes();

        var changed = false;

        if (model_variables.model_type != model_type) {
            model_variables.model_type = model_type;
            changed = true;
        }

        var simple = model_type === "simple";
        document.getElementById("show_scopes").disabled = simple;
        document.getElementById("enum").disabled = simple;
        document.getElementById("slice").disabled = simple;
        document.getElementById("nesterov_only").disabled = (getEnumRequested() || getSliceRequested() || getNesterovCycleRequested())

        if (model_variables.use_outliers != use_outliers) {
            model_variables.use_outliers = use_outliers;
            changed = true;
        }

        if (model_variables.infer_noise != infer_noise) {
            model_variables.infer_noise = infer_noise;
            changed = true;
        }

        if (model_variables.show_scopes != show_scopes) {
            model_variables.show_scopes = show_scopes;
            changed = true;
        }

        var old_inf_prog = inference_program;
        if ( getEnumRequested() &&  getSliceRequested() && !getNesterovCycleRequested()) {
            inference_program = "(do (mh default one 5) (gibbs structure one 1) (slice params one 0.5 100 1))";
        }
        if (!getEnumRequested() &&  getSliceRequested() && !getNesterovCycleRequested()) {
            inference_program = "(do (mh default one 5) (slice params one 0.5 100 1))";
        }
        if ( getEnumRequested() && !getSliceRequested() && !getNesterovCycleRequested()) {
            inference_program = "(do (mh default one 5) (gibbs structure one 1))";
        }
        if (!getEnumRequested() && !getSliceRequested() && !getNesterovCycleRequested()) {
            inference_program = "(mh default one 10)";
        }
        if ( getEnumRequested() &&  getSliceRequested() && getNesterovCycleRequested()) {
            inference_program = "(do (mh default one 5) (gibbs structure one 1) (slice params one 0.5 100 1) (nesterov default all 0.03 5 1))";
        }
        if (!getEnumRequested() &&  getSliceRequested() && getNesterovCycleRequested()) {
            inference_program = "(do (mh default one 5) (slice params one 0.5 100 1) (nesterov default all 0.03 5 1))";
        }
        if ( getEnumRequested() && !getSliceRequested() && getNesterovCycleRequested()) {
            inference_program = "(do (mh default one 5) (gibbs structure one 1) (nesterov default all 0.03 5 1))";
        }
        if (!getEnumRequested() && !getSliceRequested() && getNesterovCycleRequested()) {
            inference_program = "(do (mh default one 10) (nesterov default all 0.03 5 1))";
        }
        if (getNesterovOnlyRequested()) {
            inference_program = "(nesterov default all 0.03 5 1)"
        }
        if (old_inf_prog != inference_program) {
            changed = true;
        }

        return changed;
    };

    var SwitchModel = function(directives) {
        LoadModel();

        // reload all of the observed points
        for (obs_id in points) {
            p = points[obs_id];
            DeletePoint(obs_id);
            ObservePoint(obs_id, p.x, p.y);
        }
    }

    /* This is the callback that we pass to GET_DIRECTIVES_CONTINUOUSLY. */
    var RenderAll = function(directives) {
        //console.log("CLICKS TO ADD: " + JSON.stringify(clicks_to_add));

        //console.log("Rendering starting")
        then = Date.now()

        if (CheckModelVariables()) {
            SwitchModel(directives);
        }

        UpdateModelVariables(directives);
        UpdateVentureCode(directives);

        /* Get the observed points from the model. */
        GetPoints(directives);

        var current_curve = getCurve[model_variables.model_type]();

        // console.log(current_curve.polynomial_coefficients);

        for (obs_id in points) {
            p = points[obs_id];

            /* If this user does not have a point object for it, make one. */
            if (!(obs_id in local_points)) {
                local_points[obs_id] = MakePoint(p);
            }

            /* Forget a point if it has been clicked on. */
            if (obs_id in points_to_forget) {
                for (var i = 0; i < p.dids.length; ++i) {
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

        now = Date.now()
        //console.log("Rendering took", now - then, "ms")
    };

    var ShowCurvesQ = function() {
        return document.getElementById("show_curves").checked;
    };

    var getModelType = function() {
        for (var i = 0; i < model_types.length; ++i) {
            if (document.getElementById(model_types[i]).checked) {
                return model_types[i];
            }
        }
        return null;
    };

    var getUseOutliers = function() {
        return document.getElementById("use_outliers").checked;
    };

    var getInferNoise = function() {
        return document.getElementById("infer_noise").checked;
    };

    var getShowScopes = function() {
        return document.getElementById("show_scopes").checked;
    };

    var getEnumRequested = function() {
        return document.getElementById("enum").checked;
    };

    var getSliceRequested = function() {
        return document.getElementById("slice").checked;
    };

    var getNesterovCycleRequested = function() {
        return document.getElementById("nesterov_cycle").checked;
    }

    var getNesterovOnlyRequested = function() {
        return document.getElementById("nesterov_only").checked;
    }

    var LinearCurve = function() {
        var curve = function(x) {
            return model_variables.a + model_variables.b * x;
        };

        return curve;
    };

    var AdvancedCurve = function() {
        polynomial_coefficients = [
            model_variables.a0_c0,
            model_variables.c1,
            model_variables.c2,
            model_variables.c3,
            model_variables.c4,
        ];

        var curve = function(x) {
            var result_poly = 0;
            for (var i = 1; i < polynomial_coefficients.length; ++i) {
                result_poly += polynomial_coefficients[i] * Math.pow(x, i);
            }
            var result_f = model_variables.fourier_a1 * Math.sin(model_variables.fourier_omega * x + model_variables.fourier_theta1);
            result = polynomial_coefficients[0] + model_variables.alpha * result_poly + (1.0 - model_variables.alpha) * result_f;
            //console.log(x + ", " + result);
            return result;
        };

        return curve;
    };

    var getCurve = {simple: LinearCurve, advanced: AdvancedCurve};

    var DrawCurve = function(curve) {
        var step = 1;
        var plot_y = (420 / 2) - curve(-10) * 20;
        var line_description = "M-10 " + plot_y;
        var plot_x1 = 0;
        var plot_y1 = 0;
        var plot_x = 0;
        var plot_y = 0;
        for (var x = -12 + step; x <= 12; x += step) {
            plot_x = (420 / 2) + x * 20;
            plot_y = (420 / 2) - curve(x) * 20;
            plot_x1 = (420 / 2) + (x + step / 2) * 20;
            plot_y1 = (420 / 2) - curve(x + step / 2) * 20;
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
        <h3>Bayesian Curve Fitting Demo</h3>\
        <div id="working_space" style="display: ;">\
        <table><tr><td style="vertical-align: top;">\
        <div id="div_for_plots" style="background-color: white; width: 420px; height: 420px;"></div>\
        <br>\
        <label><input type="checkbox" id="show_curves" name="show_curves" checked>Show Curves</label>\
        <br>\
        <button type="button" id="clear_ripl">Clear RIPL</button>\
        <br><br>\
        Powered by the Venture probabilistic programming language\
        </td><td>&nbsp;&nbsp;&nbsp;</td>\
        <td style="vertical-align: top;">\
        <table width="100%" height="120px">\
        <tr>\
        <label><input type="radio" name="model_type" id="simple" value="simple">Simple Model</label>\
        <label><input type="radio" name="model_type" id="advanced" value="advanced">Advanced Model</label>\
        <br>\
        <label><input type="checkbox" id="use_outliers" name="use_outliers">Infer Outliers</label>\
        <label><input type="checkbox" id="infer_noise" name="infer_noise">Infer Noise</label>\
        <label><input type="checkbox" id="show_scopes" name="show_scopes">Display inference hints</label>\
        <br><br>\
        <div id="venture_code"></div>\
        <br>\
        <label><input type="checkbox" name="enum" id="enum" value="enum">Enumerate structure</label>\
        <label><input type="checkbox" name="slice" id="slice" value="slice">Slice sample parameters</label>\
        <br>\
        <label><input type="checkbox" name="nesterov_cycle" id="nesterov_cycle" value="nesterov_cycle">Cycle MAP inference</label>\
        <label><input type="checkbox" name="nesterov_only" id="nesterov_only" value="nesterov_only">MAP inference only</label>\
        </tr>\
        </table>\
        <br>\
        ');
    };

    var RunDemo = function() {
        document.getElementById(model_variables.model_type).checked = true;
        document.getElementById("clear_ripl").onclick = ForgetPoints;
        ripl.get_directives_continuously(
            [[75,
            RenderAll,
            []]] // empty list means get all directives
        );
    };

    /* START CODE */
    InsertHTML('vis_holder');
    RenderInit();

    ripl.get_directives_once(function(directives) {
        if (directives.length === 0) {
            // fresh Venture instance
            LoadModel();
            RunDemo();
        } else if (directives[0].symbol.value == "demo_id" && directives[0].value == demo_id) {
            UpdateModelVariables(directives);
            RunDemo();
        } else {
            throw "Error: Something other than curve-fitting demo running in Venture."
        }
    });

};

