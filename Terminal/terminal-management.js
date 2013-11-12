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
}

term_ripl.prototype.sendCommandToRIPLServer = function (command, example, term)
{
    term.pause();
    var tempcommand = '(' + command + ')';
    var parseList = parse(tempcommand);
    var ret;
    if (parseList[0] == 'assume') {
	if (example==true){
	    this.ripl.assume(parseList[1],command.substr(command.indexOf("("),command.length-1));}
	else{
	    this.ripl.assume_async(parseList[1],command.substr(command.indexOf("("),command.length-1));
	}	
    }
    if (parseList[0] == 'observe') {
	if (example==true){
	    this.ripl.observe('(' + parseList[1] + ')', parseList[2]);}
	else{
	    this.ripl.real_observe('(' + parseList[1] + ')', parseList[2]);}
    }
    if (parseList[0] == 'predict') {
	if (example==true){
	    ret = this.ripl.predict(parseList[1]);}
	else{
	    ret = this.ripl.predict_async(parseList[1]);}
    }
    if (parseList[0] == 'list_directives') {
	this.ripl.display_directives();
    }
    if (parseList[0] == 'clear') {
	ret = this.ripl.clear();
	term.echo("clear")
    }
    if (parseList[0] == 'infer') {
	if (example==true){
		this.ripl.infer(parseList[1]);
	} else {
		this.ripl.real_infer(parseList[1]);
	}
    }
    if (parseList[0] == 'start_continuous_inference') {
	this.ripl.start_continuous_inference();
	term.resume();
	term.echo("Starting continuous inference...");
    }
    if (parseList[0] == 'stop_continuous_inference') {
	this.ripl.stop_continuous_inference();
	term.resume();
	term.echo("Stopping continuous inference...");
    }
    if (parseList[0] == 'forget') {
	if (example==true){
		this.ripl.forget(parseList[1]);
	} else {
		this.ripl.real_forget(parseList[1]);
	}
    }
    if (ret != undefined){
	term.echo(JSON.stringify(ret).replace(/-NEWLINE-/g, "\n "));
    }
    term.resume();
};

term_ripl.prototype.loadExample = function ()
{
    
    // Read text file line-by-line and send into the engine
    var f =  document.getElementById('examplefile').files[0];
    var fr = new FileReader();
    fr.onload = function(e) {
	var content = e.target.result;
	var lines = content.split(/[\r\n]+/g);
	var exampleCode = '<h3>    CODE: </h3><br>'
	for(var i = 0, len = lines.length-1; i < len; i++){
	    term.echo("venture>" + lines[i]);
	    example = true;
	    riplOBJ.sendCommandToRIPLServer(lines[i],example,term);
	    exampleCode = exampleCode.concat("<b>",lines[i].substr(0,lines[i].indexOf(' ')),"</b>");
	    exampleCode = exampleCode.concat(lines[i].substr(lines[i].indexOf(' '),lines[i].length-1),"<br>");
	}
	term.echo("venture> Executing code...");
	riplOBJ.sendCommandToRIPLServer('list_directives',false,term);
	document.getElementById('metaContainer').innerHTML= exampleCode;
    }
    fr.readAsText(f);
};
