
function InitializeDemo() {
    // Should be a string?
    var demo_id = 1;
    
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
            }
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
        for (key in obj) { a.push(key); }
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
    
    var random_variables = ['alpha'];
    
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
        ripl.assume('demo_id', demo_id, 'demo_id');
        
        ripl.assume('alpha', '(gamma 1.0 1.0)');
        ripl.assume('cluster_crp', '(crp_make alpha)');
        //ripl.assume('scale', '(gamma 4.0 1.0)');
        
        ripl.assume('get_cluster_mean', "(mem (lambda (cluster dim) (uniform_continuous -10.0 10.0)))");
        ripl.assume('get_cluster_variance', "(mem (lambda (cluster dim) (inv_gamma 1.0 1.0)))");
        ripl.assume('get_cluster', "(mem (lambda (point) (cluster_crp)))");
        ripl.assume('sample_cluster', "(lambda (cluster dim) (normal (get_cluster_mean cluster dim) (get_cluster_variance cluster dim)))");
        ripl.assume('get_datapoint', "(mem (lambda (point dim) (sample_cluster (get_cluster point) dim)))");
        
        /* For observations */
        ripl.assume('noise','(mem (lambda (point dim) (inv_gamma 1.0 1.0)))');
        ripl.assume('obs_fn','(lambda (point dim) (normal (get_datapoint point dim) (noise point dim)))');
        
        /* One predict for every quantity of interest.
        Ideally this would iterate over RANDOM_VARIABLES. */
        //ripl.predict('(list poly_order a0_c0 c1 c2 c3 c4 noise alpha fourier_a1 fourier_omega fourier_theta1)','predict_model');
        
        ripl.register_all_requests_processed_callback(AllDirectivesLoadedCallback);
    };
    
    var UpdateChurchCode = function(directives) {
        var church_code_str = "<b>Venture code:</b><br>";
        
        for (i = 0; i < directives.length; i++) {
            church_code_str += JSON.stringify(directives[i]["expression"]) + '<br>';
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
    
    function record(dict, path, value) {
        if (path.length > 1) {
            var key = path[0];
            if (!(key in dict)) {
                dict[key] = {};
            }
            record(dict[key], path.slice(1), value);
        } else {
            dict[path[0]] = value;
        }
    }
    
    /* Gets the points that are in the ripl. */
    var ExtractData = function(predicts, observes) {
        var data = {};
        var directives = predicts.concat(observes);
        
        var extract = function(directive) {
            var path = directive.label.split('_').slice(1);
            record(data, path, directive.value);
            
            var did = directive.directive_id;
            var p = data[path[0]];
            
            if (!('dids' in p)) {
                p.dids = [];
            }
            p.dids.push(did);
        };
        
        directives.forEach(extract);
        
        return data;
    };
    
    /* Adds a point to the GUI. */
    var MakePoint = function(x,y) {
        var point = new Object();
        
        point.x = x;
        point.y = y;
        
        point.paint_x = (point.x * 20) + 210;
        point.paint_y = (point.y * 20) + 210;
        
        point.noise_circle = paper.ellipse(point.paint_x, point.paint_y, 5, 5);
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
    
    var colors = ['aqua', 'black', 'blue', 'fuchsia', 'gray', 'green', 'lime', 'maroon', 'navy', 'olive', 'orange', 'purple', 'red', 'silver', 'teal', 'white', 'yellow'];
    
    var DrawPoint = function(point, data) {
        color = colors[data.cluster.id % colors.length];
        
        point.circle.attr("fill", color);
        point.noise_circle.attr("stroke", color);
        point.noise_circle.attr("rx", data.noise.x * 5.0);
        point.noise_circle.attr("ry", data.noise.y * 5.0);
    };
    
    /* This is the callback that we pass to GET_DIRECTIVES_CONTINUOUSLY. */
    var RenderAll = function(directives) {
        //console.log("CLICKS TO ADD: " + JSON.stringify(clicks_to_add));
        
        UpdateChurchCode(directives);
        
        var observes = directives.filter(function(dir) { return dir.instruction === "observe" });
        var predicts = directives.filter(function(dir) { return dir.instruction === "predict" });
        
        var data = ExtractData(predicts, observes);
        
        /* Bookkeeping so we can delete forgotten points from POINTS. */
        var current_obs_ids = [];
        
        for (obs_id in data) {
            p = data[obs_id];
            
            /* If this user does not have a point object for it, make one. */
            if (!(obs_id in points)) {
                var point = MakePoint(p.x, p.y);
                point.obs_id = obs_id;
                points[obs_id] = point;
            }
            
            /* This user already CLICKED on the point, indicating that he
            * wants to forget it. */
            if (clicks_to_forget.indexOfClick([p.x, p.y]) != -1) {
                for (var i = 0; i < p.dids.length; i++) {
                    ripl.forget(parseInt(p.dids[i]));
                }
                continue;
            }
            
            /* Otherwise, we register that the POINT is still active. */
            current_obs_ids.push(obs_id);
            
            DrawPoint(points[obs_id], p);
        }
        
        /* Reset this after each round of directives has been processed. */
        clicks_to_forget = new ClickList();
        
        /* Delete points for which there is no observation. */
        for (obs_id in points) {
            if (!(obs_id in data)) {
                points[obs_id].noise_circle.remove();
                points[obs_id].circle.remove();
                delete points[obs_id];
            }
        }
        
        /* Add points for every click on the canvas. */
        //console.log("before unique: " + JSON.stringify(clicks_to_add.getClicks()));
        clicks_to_add.uniqueF();
        //console.log("after unique: " + JSON.stringify(clicks_to_add.getClicks()));
        while (clicks_to_add.length() > 0) {
            console.log("adding new point!");
            var click = clicks_to_add.shift();
            var x = (click[0] - 210)/20;
            var y = (click[1] - 210)/20;
            
            var obs_id = GetNextObsID();
            
            // use labels here?
            obs_str = 'points_' + obs_id.toString();
            
            ripl.observe('(obs_fn ' + obs_id + ' 0)', x, obs_str + '_x');
            ripl.observe('(obs_fn ' + obs_id + ' 1)', y, obs_str + '_y');
            
            /*
            ripl.predict('(list\
                (obs_fn ' + obs_id + ' 0) (obs_fn ' + obs_id + ' 1)\
                (noise ' + obs_id + ' 0) (noise ' + obs_id + ' 1) (get_cluster ' + obs_id + ')\
                (get_cluster_mean (get_cluster ' + obs_id + ') 0) (get_cluster_mean (get_cluster ' + obs_id + ') 1)\
                (get_cluster_variance (get_cluster ' + obs_id + ') 0) (get_cluster_variance (get_cluster ' + obs_id + ') 1)\
                )',
                obs_str)
            */
            
            ripl.predict('(noise ' + obs_id + ' 0)', obs_str + '_noise_x');
            ripl.predict('(noise ' + obs_id + ' 1)', obs_str + '_noise_y');
            ripl.predict('(get_cluster ' + obs_id + ')', obs_str + '_cluster_id');
            ripl.predict('(get_cluster_mean (get_cluster ' + obs_id + ') 0)', obs_str + '_cluster_mean_x');
            ripl.predict('(get_cluster_mean (get_cluster ' + obs_id + ') 1)', obs_str + '_cluster_mean_y');
            ripl.predict('(get_cluster_variance (get_cluster ' + obs_id + ') 0)', obs_str + '_cluster_variance_x');
            ripl.predict('(get_cluster_variance (get_cluster ' + obs_id + ') 1)', obs_str + '_cluster_variance_y');
        }
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


    // The main crp mixture HTML code.
    var InsertHTML = function(divclass) {
        $('div.'+divclass).html('\
            <h3>CRP Mixture demo</h3>\
            <div id="working_space" style="display: ;">\
              <table><tr><td style="vertical-align: top;">\
                <div id="div_for_plots" style="background-color: white; width: 420px; height: 420px;"></div>\
                <br>\
                <div>\
                <div class="btn-group">\
                    <button class="btn btn-danger">Engine Status</button>\
                    <button class="btn btn-danger dropdown-toggle" data-toggle="dropdown"><span class="caret"></span></button>\
                    <ul class="dropdown-menu">\
                        <li><a href="#" onclick="ex.handle = window.setInterval(\'ex.render();\',15)">Turn Engine ON</a></li>\
                         <li><a href="#" onclick="window.clearInterval(ex.handle)">Turn Engine OFF</a></li>\
                    </ul>\
                </div>\
                </div>\
                <br>\
          <a href="http://www.yuraperov.com/MIT.PCP/demo.html">Return to the list of demos.</a>\
          <br><br>\
                Based on the Venture probabilistic programming language\
              </td><td>&nbsp;&nbsp;&nbsp;</td>\
              <td style="vertical-align: top;">\
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
            throw "Error: Something other than crp-mixture demo running in Venture."
        }
    });

};

