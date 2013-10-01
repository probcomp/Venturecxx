/* Descrption: this script outlines the back end functionality of the terminal
* using the new asyncrhonous jripl.
*
* Overview: this allows the user to send inline commands into the ripl, load
* examples and vary example parameters.
* 
* The sister function of this file is index-load.js, that creates a terminal object.
*
* Author: Saee Paliwal
*/


function term_ripl() {
    this.ripl = new jripl();
    this.terminal_prompt = 'venture> ';
    this.ripl.set_mode("church_prime");
    this.ripl.clear()
//    this.ripl.register_a_request_processed_callback(DirectiveLoadedCallback);

}

term_ripl.prototype.sendCommandToRIPLServer = function (command, term)
{
    term.pause();
    var tempcommand = '(' + command + ')';
    var parseList = parse(tempcommand);
    var ret;
    if (parseList[0] == 'assume') {
	this.ripl.assume_async(parseList[1],command.substr(command.indexOf("("),command.length-1));
    }
    if (parseList[0] == 'observe') {
	this.ripl.observe_async('(' + parseList[1] + ')', parseList[2]);
    }
    if (parseList[0] == 'predict') {
	ret = this.ripl.predict_async(parseList[1], 'predict_model');
	    }
    if (parseList[0] == 'list_directives') {
	this.ripl.display_directives();
   }
    if (parseList[0] == 'clear') {
	ret = this.ripl.clear();
	term.echo("clear")
    }
    if (parseList[0] == 'infer') {
	this.ripl.infer(parseList[1]);
    }
    if (parseList[0] == 'start_continuous_inference') {
	this.ripl.start_continuous_inference();
	term.echo("Starting continuous inference...");
    }
    if (parseList[0] == 'stop_continuous_inference') {
	this.ripl.stop_continuous_inference();
	term.echo("Stopping continuous inference...");
    }
    if (parseList[0] == 'forget') {
	this.ripl.forget(parseList[1]);
    }
    if (ret != undefined){
	term.echo(JSON.stringify(ret).replace(/-NEWLINE-/g, "\n "));
    }
    
    term.resume(); 
};

term_ripl.prototype.loadExample = function (filename)
{
    $.get('./' + filename + '.txt', function(myContentFile) {
	var lines = myContentFile.split("\n");
	var exampleCode = '<h3>    CODE: </h3><br>'
	for(var i = 0, len = lines.length-1; i < len; i++){
	    term.echo("venture>" + lines[i]);
	    riplOBJ.sendCommandToRIPLServer(lines[i],term);
	    exampleCode = exampleCode.concat("<b>",lines[i].substr(0,lines[i].indexOf(' ')),"</b>");
	    exampleCode = exampleCode.concat(lines[i].substr(lines[i].indexOf(' '),lines[i].length-1),"<br>");
	}
	document.getElementById('examplecode').innerHTML= exampleCode;
    }, 'text');
    
};
