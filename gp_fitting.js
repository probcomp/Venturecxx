

function InitializeDemo() {

    var demo_id = 3;

    var inference_program = "(mh default one 1)"

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

    /* Latent variables in the model. */
    var model_variables = {
        /* Both */
        model_type: "gp",
        infer_noise: false,
        use_outliers: false,
        show_scopes: false,
        noise: 1.0,

        /* GP */
        mu: 0,
        
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
        ripl.infer("(loop (" + inference_program + "))");
        ripl.register_a_request_processed_callback(function () {});
    };
    
    var LoadGPModel = function() {
        ripl.clear();
        ripl.set_mode("church_prime");

        /* Model metadata */
        ripl.assume('demo_id', demo_id, 'demo_id');
        
        var program = "\
          [assume mu (normal 0 10)]\
          [assume a (inv_gamma 1 1)]\
          [assume l (inv_gamma 1 1)]\
          \
          [assume mean (app make_const_func mu)]\
          [assume cov (app make_squared_exponential a l)]\
          \
          gp : [assume gp (make_gp mean cov)]\
          \
          [assume obs_fn (lambda (obs_id x) (gp (array x)))]\
        "
        
        ripl.execute_program(program)

    };

    var LoadModel = function() {
        num_directives_loaded = 0;
        ripl.register_a_request_processed_callback(DirectiveLoadedCallback);
        ripl.stop_continuous_inference();
        loadGPModel();

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
        points = {};

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

        var observesAndPredicts = directives.filter(function(dir) {return dir.instruction != "assume";});
        observesAndPredicts.forEach(extract);

        for (obs_id in points) {
            points[obs_id].obs_id = obs_id;
        }
    };
    
    var toDict = function(type, value) {
        return {
            type: type,
            value: value
        };
    };
    
    var toNumber = function(x) {
        return toDict("number", x);
    };
    
    var toArray = function(xs) {
        return {
            type: "array",
            value: xs.map(toNumber)
        };
    };
    
    var ObservePoint = function(obs_id, x, y) {
        obs_str = 'points_' + obs_id;

        ripl.predict(x, obs_str + '_x');
        ripl.observe(['obs_fn', obs_id, ['quote', [x]]], toArray([y]), obs_str + '_y');
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
            inference_program = "(cycle ((mh default one 5) (gibbs structure one 1) (slice params one 0.5 100 1)) 1)";
        }
        if (!getEnumRequested() &&  getSliceRequested() && !getNesterovCycleRequested()) {
            inference_program = "(cycle ((mh default one 5) (slice params one 0.5 100 1)) 1)";
        }
        if ( getEnumRequested() && !getSliceRequested() && !getNesterovCycleRequested()) {
            inference_program = "(cycle ((mh default one 5) (gibbs structure one 1)) 1)";
        }
        if (!getEnumRequested() && !getSliceRequested() && !getNesterovCycleRequested()) {
            inference_program = "(mh default one 50)";
        }
        if ( getEnumRequested() &&  getSliceRequested() && getNesterovCycleRequested()) {
            inference_program = "(cycle ((mh default one 5) (gibbs structure one 1) (slice params one 0.5 100 1) (nesterov default all 0.03 5 1)) 1)";
        }
        if (!getEnumRequested() &&  getSliceRequested() && getNesterovCycleRequested()) {
            inference_program = "(cycle ((mh default one 5) (slice params one 0.5 100 1) (nesterov default all 0.03 5 1)) 1)";
        }
        if ( getEnumRequested() && !getSliceRequested() && getNesterovCycleRequested()) {
            inference_program = "(cycle ((mh default one 5) (gibbs structure one 1) (nesterov default all 0.03 5 1)) 1)";
        }
        if (!getEnumRequested() && !getSliceRequested() && getNesterovCycleRequested()) {
            inference_program = "(cycle ((mh default one 10) (nesterov default all 0.03 5 1)) 1)";
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

        //if (CheckModelVariables()) {
        //    SwitchModel(directives);
        //}

        //UpdateModelVariables(directives);
        UpdateVentureCode(directives);

        /* Get the observed points from the model. */
        GetPoints(directives);

        //var current_curve = getCurve[model_variables.model_type]();

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
        //add_previous_curve_object(DrawCurve(current_curve));

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
    
    var DrawLines = function(ys) {
        console.log(ys)
        var plot_y = (420 / 2) - ys[0] * 20;
        var line_description = "M-10 " + plot_y;
        for (var i = 1; i < ys.length; ++i) {
            x1 = modelToPaperX(xs[i-1])
            y1 = modelToPaperY(ys[i-1])
            x2 = modelToPaperX(xs[i])
            y2 = modelToPaperY(ys[i])
            line_description += "Q" + x1 + " " + y1 + " " + x2 + " " + y2;
        }
        add_previous_curve_object(paper.path(line_description));
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
    
    var xs = [];
    for (var x = -12; x <= 12; x += 1) {
      xs.push(x);
    }

    var RunDemo = function() {
        //document.getElementById(model_variables.model_type).checked = true;
        document.getElementById("clear_ripl").onclick = ForgetPoints;
        ripl.infer("(loop (" + inference_program + "))");
        
        var loop = function() {
            ripl.method("list_directives", [false, false, ["predict", "observe"]], RenderAll);
            ripl.method("sample", [['gp', ['quote', xs]]], DrawLines);
            setTimeout(loop, 75);
        };
        
        loop();
    };

    /* START CODE */
    InsertHTML('vis_holder');
    RenderInit();
    
    RunDemo();
};

