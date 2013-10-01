jQuery(document).ready(function($) {
		riplOBJ = new term_ripl();
		term = $('#terminalWindow').terminal(function(command, term) {
		if (command == "") {
			return;
		}
		    		riplOBJ.sendCommandToRIPLServer(command, term)
		}, {
			greetings: 'Welcome to Venture!',
		      	name: 'terminalDemo',
		      	height: 390,
		      	prompt: riplOBJ.terminal_prompt,
		      	exit: false,
		      	clear: false
		});
    term.css("color", "green");
});
