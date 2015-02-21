jQuery(document).ready(function($) {
    riplOBJ = new term_ripl();
		term = $('#terminalWindow').terminal(function(command, term) {
		if (command == "") {
			return;
		}
		    term.pause();
		    riplOBJ.sendCommandToRIPLServer(command, false,term)
		}, {
			greetings: 'Welcome to Venture!',
		      	name: 'terminalDemo',
		      	height: 390,
		      	prompt: riplOBJ.terminal_prompt,
		      	exit: true,
		      	clear: false
		});
    term.css("color", "green");
});
