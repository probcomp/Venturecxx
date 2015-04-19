
venture__venture_ec2_demo_instance_host = "54.235.201.199"
venture__venture_ec2_demo_instance_port = 80

how_many_directives_were_loaded_during_initialization = 0

error_has_been_processed = false
omit_errors = false

function ProcessRIPLError() {
  if (omit_errors == true) {
    return
  }
  if (error_has_been_processed == true) {
    return
  }
  error_has_been_processed = true
  if (venture__venture_ec2_demo_instance_host == $.cookie('venture__ripl_host') && venture__venture_ec2_demo_instance_port == $.cookie('venture__ripl_port')) {
    if (confirm("Sorry, an error has happened. Most probably MIT.PCP Venture demo server needs to be restarted. Do you want try to restart it (it should take 2-3 seconds)?")) {
      navigateToUrl("http://54.235.201.199:81/restart_venture_server")
    }
  } else {
    alert("Sorry, an error has happened. Most probably, the server you specified (venture://" + $.cookie('venture__ripl_host') + ":" + $.cookie('venture__ripl_port') + ") is not active. You can choose another Venture RIPL by clicking 'Change'.")
  }
  throw "Error"
}

function OneMoreDirectiveHasBeenLoaded() {
  how_many_directives_were_loaded_during_initialization++
  if ($("#loading-status") != undefined) {
    $("#loading-status").html("Demo is loading... <b>" + how_many_directives_were_loaded_during_initialization + '</b> directive(s) have been already loaded.')
  }
}

function CheckCookieWithVentureRIPLAddress() {
  if ($.cookie('venture__ripl_host') == undefined) {
    GoToSelectRIPLAddress();
  }
  $("#ripl_address_info").html("You are using <i>venture://" + $.cookie('venture__ripl_host') + ":" + $.cookie('venture__ripl_port') + "</i>. <a href='#' style='text-decoration: underline;' onClick='GoToSelectRIPLAddress()'>Change</a>");
}

function GoToSelectRIPLAddress() {
  navigateToUrl("select_venture_server.html")
}
// From here (with editions): http://stackoverflow.com/questions/4762254/javascript-window-location-does-not-set-referer-in-the-request-header
function navigateToUrl(url) {
    var f = document.createElement("FORM");
    f.action = url;

    var indexQM = url.indexOf("?");
    if (indexQM>=0) {
        // the URL has parameters => convert them to hidden form inputs
        var params = url.substring(indexQM+1).split("&");
        for (var i=0; i<params.length; i++) {
            var keyValuePair = params[i].split("=");
            var input = document.createElement("INPUT");
            input.type="hidden";
            input.name  = keyValuePair[0];
            input.value = keyValuePair[1];
            f.appendChild(input);
        }
    }
    var input = document.createElement("INPUT");
    input.type="hidden";
    input.name  = "url_referrer";
    input.value = window.location.pathname;
    f.appendChild(input);

    document.body.appendChild(f);
    f.submit();
}

// ***

function refreshInfButton() {
	var r = new ripl();
	var ret = r.cont_infer_status()
	if (ret.status == 'off') {
		$('#infstat').html('INFERENCE IS OFF');
	}
	else {
		$('#infstat').html('INFERENCE IS ON.');
	}
}



var STR_PAD_LEFT = 1;
var STR_PAD_RIGHT = 2;
var STR_PAD_BOTH = 3;
 
function pad(str, len, pad, dir) {
 
	if (typeof(len) == "undefined") { var len = 0; }
	if (typeof(pad) == "undefined") { var pad = ' '; }
	if (typeof(dir) == "undefined") { var dir = STR_PAD_RIGHT; }
 
	if (len + 1 >= str.length) {
 
		switch (dir){
 
			case STR_PAD_LEFT:
				str = Array(len + 1 - str.length).join(pad) + str;
			break;
 
			case STR_PAD_BOTH:
				var right = Math.ceil((padlen = len - str.length) / 2);
				var left = padlen - right;
				str = Array(left+1).join(pad) + str + Array(right+1).join(pad);
			break;
 
			default:
				str = str + Array(len + 1 - str.length).join(pad);
			break;
 
		} // switch
 
	}
 
	return str;
 
}



function loadJS(file) {
		var oHead = document.getElementsByTagName('HEAD').item(0);
		var oScript= document.createElement("script");
		oScript.type = "text/javascript";
		oScript.src=file;
		oHead.appendChild( oScript);
}

function fetchUserScript(file) {
		if (file == "NONE") {
			loadJS($('#getLibLocation').val()); //isnt working for some reason
		}
		else {
			loadJS(file);	
		}	
		setTimeout("ex = new vistemplate();ex.run()",300);
}


function JustLoadProgramFromUserScript(file) {
		if (file == "NONE") {
			loadJS($('#getLibLocation').val()); //isnt working for some reason
		}
		else {
			loadJS(file);	
		}
		if (typeof LOADVISPAGE === 'undefined') {
			setTimeout("ex = new vistemplate();ex.loadProgram()",300);
		}
		else {
			setTimeout("ex = new vistemplate();ex.run()",300);
		}
}

function conInf(state) {
	var r=new ripl();
	if(state == 'INFON') {
		r.start_cont_infer(1);
		//this.handle = setInterval('nb.ShowDirectives()',70);
		if (typeof txtview != 'undefined') {
			TIMER = window.setInterval('txtview.ShowDirectives()',70);
			REFRESH = 1;
		}
		else if (typeof nb != 'undefined') {
			TIMER = window.setInterval('nb.ShowDirectives()',70);
			REFRESH = 1;
		}
	}
	else if (state == 'INFOFF') {
		r.stop_cont_infer();
		//clearInterval('nb.handle');
		if (typeof txtview != 'undefined') {
			window.clearInterval(TIMER);
			REFRESH = 0;
			txtview.ShowDirectives();
		}
		else if (typeof nb != 'undefined') {
			window.clearInterval(TIMER);
			REFRESH = 0;
			nb.ShowDirectives();
		}
	}
	else if (state == 'INFSTAT') {
		var stat = r.cont_infer_status()
		alert('Continous Inferece is: ' + stat.status);
	}
	else if (state == 'CLEAR') {
		r.clearTrace();
	}
	else if (state == 'INFER') {
		r.infer(100,1);
	}
	else if (state == 'REFRESH') {
		if (typeof txtview != 'undefined') {
			txtview.ShowDirectives();
		}
		else if (typeof nb != 'undefined') {
			nb.ShowDirectives();
		}
	}
}
