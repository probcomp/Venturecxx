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
    // Should be a string?
    var demo_id = 3;
    
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
    
    //TODO this number is arbritrary, not sure how to get browser dependent
    //max int
    var LargeRandomInt = function() {
        return Math.floor(Math.random() * 10000000);
    }
    
    var ripl = new jripl();
    
    /* For the A_DIRECTIVE_LOADED callback to display status. */
    var num_directives_loaded = 0;
    
    /* A unique ID for each observation. */
    var next_obs_id = 0; //LargeRandomInt();
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
    var model_variables = {'crp_alpha' : 1.0, 'cv_scale': 1.0};
    
    /* Raphael Objects */
    var paper;
    var paper_rect;
    
    /* Map from OBS_ID -> POINT, where POINT contains the Raphael objects
     * corresponding to a single point. */
    var local_points = {};
    
    /* Map from CLUSTER_ID -> CLUSTER, where CLUSTER contains the Raphael object
     * corresponding to a single cluster. */
    var local_clusters = {};
    
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
        
        ripl.assume('crp_alpha', "(gamma 1.0 3.0)");
        ripl.assume('cluster_crp', "(make_crp crp_alpha)");
        
        // cmvn hyperparameters. Put priors on these?
        ripl.assume('mu', '(array 0 0)');
        ripl.assume('k', 0.01);
        ripl.assume('v', 4);
        ripl.assume('S', '(matrix (array (array 1 0) (array 0 1)))');
        
        ripl.assume('get_cluster_sampler', "(mem (lambda (cluster) (make_cmvn mu k v S)))");
        
        ripl.assume('get_cluster', "(mem (lambda (point) (cluster_crp)))");
        ripl.assume('sample_cluster', "(lambda (cluster) ((get_cluster_sampler cluster)))");
        ripl.assume('get_point', "(mem (lambda (point) (sample_cluster (get_cluster point))))");
        
        /* For observations */
        //ripl.assume('noise','(mem (lambda (point dim) (inv_gamma 1.0 1.0)))');
        //ripl.assume('obs_fn','(lambda (point dim) (normal (get_datapoint point dim) (noise point dim)))');
        
        ripl.register_all_requests_processed_callback(AllDirectivesLoadedCallback);
    };
    
    var UpdateVentureCode = function(directives) {
        code = VentureCodeHTML(directives, false);
        code = "<font face='Courier New' size='2'>" + code + "</font>";
        $("#venture_code").html(code);
    };
    
    var UpdateModelVariables = function(directives) {
        for(var i = 0; i < directives.length; i++) {
            var dir = directives[i];
            if(dir.instruction === "assume") {
                if(dir.symbol.value in model_variables) {
                    model_variables[dir.symbol.value] = dir.value;
                }
            }
        }
    }
    
    /* Converts model coordinates to paper coordinates. */
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
        
        local_point.paint_x = modelToPaperX(p.xy[0]);
        local_point.paint_y = modelToPaperY(p.xy[1]);
        
        local_point.noise_circle = paper.ellipse(local_point.paint_x, local_point.paint_y, 5, 5);
        local_point.noise_circle.attr("fill", "white");
        //local_point.noise_circle.attr("opacity", "0.9");
        
        local_point.circle = paper.circle(local_point.paint_x, local_point.paint_y, 2);
        local_point.circle.attr("stroke", "white");
        //local_point.circle.attr("opacity", "0.5");
        
        local_point.circle.click(
            function(e) { 
                points_to_forget[local_point.obs_id] = true;
            }
        );
        
        local_point.noise_circle.click(
            function(e) { 
                points_to_forget[local_point.obs_id] = true;
            }
        );
        
        return local_point;
    };
    
    var colors = ['aqua', 'black', 'blue', 'fuchsia', 'gray', 'green', 'lime', 'maroon', 'navy', 'olive', 'orange', 'purple', 'red', 'silver', 'teal'];
    
    var MakeCluster = function(cluster) {
        var local_cluster = {};
        local_cluster.id = cluster.id;
        local_cluster.color = colors.pop();
        local_cluster.circle = paper.ellipse(0, 0, 0, 0);
        local_cluster.circle.attr('stroke-dasharray', "-");
        local_cluster.circle.attr('stroke-width', "3");
        return local_cluster;
    };
    
    var DeleteCluster = function(cluster_id) {
        var local_cluster = local_clusters[cluster_id];
        local_cluster.circle.remove();
        colors.push(local_cluster.color);
        delete local_clusters[cluster_id];
    };
    
    var DrawCluster = function(local_cluster, cluster) {
        var color = local_cluster.color;
        
        local_cluster.circle.attr("stroke", color);
        
        var [mu, sigma, v] = cluster.mvt;
        
        mu = numeric.transpose(mu)[0];
        console.log(mu);
        
        local_cluster.circle.attr("cx", modelToPaperX(mu[0]));
        local_cluster.circle.attr("cy", modelToPaperY(mu[1]));
        
        // the mean and variance are undefined in this case
        if (v <= 2) return;
        
        var scale = v / (v - 2);
        var decomp = numeric.eig(sigma);
        
        var eigVals = decomp.lambda.x;
        var eigVecs = decomp.E.transpose().x;
        
        var stdDevs = numeric.sqrt(numeric.dot(scale, eigVals));
        
        local_cluster.circle.attr("rx", Math.abs(xScale) * stdDevs[0]);
        local_cluster.circle.attr("ry", Math.abs(yScale) * stdDevs[1]);
        
        var vec = eigVecs[0];
        var angle = -Math.atan2(vec[1], vec[0]) / Math.PI * 180;
        
        local_cluster.circle.transform("R" + angle);
    };
    
    var ObservePoint = function(obs_id, x, y) {
        var obs_str = 'points_' + obs_id;
        
        ripl.observe('(get_point ' + obs_id + ')', toArray([x, y]), obs_str + '_xy');
        
        ripl.predict('(get_cluster ' + obs_id + ')', obs_str + '_cluster_id');
        ripl.predict('(get_cluster_sampler (get_cluster ' + obs_id + '))', obs_str + '_cluster_mvt');
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
        
        var observesAndPredicts = directives.filter(function(dir)
            {return dir.instruction in {"observe":true, "predict":true}});
        observesAndPredicts.forEach(extract);
        
        for (obs_id in points) {
            points[obs_id].obs_id = obs_id;
        }
        
        return points;
    };
    
    var DrawPoint = function(local_point, point) {
        color = local_clusters[point.cluster.id].color;
        
        local_point.circle.attr("fill", color);
        local_point.noise_circle.attr("stroke", color);
        local_point.noise_circle.attr("rx", 5.0);
        local_point.noise_circle.attr("ry", 5.0);
    };
    
    /* This is the callback that we pass to GET_DIRECTIVES_CONTINUOUSLY. */
    var RenderAll = function(directives) {
        
        UpdateVentureCode(directives);
        UpdateModelVariables(directives);
        
        /* Get the observed points from the model. */
        var points = GetPoints(directives);
        
        /* The unique clusters. */
        var clusters = {};
        
        for (obs_id in points) {
            p = points[obs_id];
            
            /* Add the point's cluster to the set of clusters. */
            cluster = p.cluster;
            if (!(cluster.id in clusters)) {
                clusters[cluster.id] = cluster;
                if (!(cluster.id in local_clusters)) {
                    local_clusters[cluster.id] = MakeCluster(cluster);
                }
            }
            
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
        
        /* Remove nonexistent clusters and draw the rest. */
        for (cluster_id in local_clusters) {
            if(!(cluster_id in clusters)) {
                DeleteCluster(cluster_id);
            } else {
                DrawCluster(local_clusters[cluster_id], clusters[cluster_id]);
            }
        }
        
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
            console.log("adding new point!");
            var click = clicks_to_add.shift();
            var x = paperToModelX(click[0]);
            var y = paperToModelY(click[1]);
            
            var obs_id = GetNextObsID();
            
            ObservePoint(obs_id, x, y);
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
<!--                <div class="btn-group">\
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
-->          <br><br>\
                Powered by the Venture probabilistic programming language\
              </td><td>&nbsp;&nbsp;&nbsp;</td>\
              <td style="vertical-align: top;">\
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
            ripl.infer("(loop (mh default one 10))");
            RunDemo();
        } else if (directives[0].symbol.value === "demo_id" && directives[0].value === demo_id) {
            RunDemo();
        } else {
            throw "Error: Something other than crp-mixture demo running in Venture."
        }
    });

};

