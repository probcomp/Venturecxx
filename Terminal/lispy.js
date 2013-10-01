//tejask@mit.edu
//Python port of LISP interpreter by Norvig: From here: http://norvig.com/lispy.html
//Including some tricks from here : https://github.com/jineshpaloor/LISP-interpreter-in-Javascript/blob/master/lispy.js

function read(s) {
    //"Read a Scheme expression from a string."
    tmp = read_from(tokenize(s));
    //tmp.shift();
    return tmp;
}

var parse = read;

function tokenize(s) {
    //"Convert a string into a list of tokens."
    s = s.replace(/\(/g,' ( ').replace(/\)/g,' ) ').split(" ");
    //s will have some blank spaces
    news = []
    while (s.length > 0){
        tmp = s.shift();
        if (tmp != "") {
	    news.push(tmp);
	}
    }
    return news;
}

function read_from(tokens) {
    //"Read an expression from a sequence of tokens."
    if (tokens.length == 0) {
        alert('unexpected EOF while reading');
    }
    var token = tokens.shift();
    if ('(' === token) {
        var L = [];
        while (tokens[0] !== ')'){
            L.push(read_from(tokens));
        }
        tokens.shift();// pop off ')'
	return L;
    }
    else if (')' == token) {
        alert('unexpected )');
    }
    else {
        return atom(token);
    }
}

function isNumber(n) {
   dtype = typeof n;
   if (dtype == "number") {
       return true;
   }
   else {
       return false;
   }
}

var Symbol = String;

var atom = function (token) {
    if (isNaN(token)) {
		return token;
    } else {
		return +token;
    }
};

         
