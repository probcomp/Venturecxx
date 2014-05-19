function exprToString(expr) {
    //console.log(typeof expr);
    if (expr instanceof Array) {
        return "(" + expr.map(exprToString).join(" ") + ")";
    } else if (typeof expr === "string") {
        return expr;
    } else {
        return expr.value.toString();
    }
}

function directiveToString(directive) {
    var directive_str = "[" + directive.instruction + " ";
    
    if (directive.instruction === "assume") {
        directive_str += directive.symbol + " ";
    }
    
    directive_str += exprToString(directive.expression);
    
    if (directive.instruction === "observe") {
        directive_str += " " + directive.value;
    }
    
    directive_str += "]";
    return directive_str;
}

blacklist = ['demo_id', 'model_type', 'use_outliers', 'infer_noise', 'outlier_prob', 'outlier_sigma'];

function isExtraneous(directive) {
    if (directive.instruction === "predict") return true;
    if (directive.instruction === "assume") {
        return blacklist.indexOf(directive.symbol) >= 0;
    }
    return false;
}

function VentureCodeHTML(directives) {
    var venture_code_str = "<b>Venture code:</b><br>";

    for (i = 0; i < directives.length; ++i) {
        if(!isExtraneous(directives[i])) {
            venture_code_str += directiveToString(directives[i]) + '<br/>';
        }
    }
    
    venture_code_str = "<font face='Courier New' size='2'>" + venture_code_str + "</font>";
    return venture_code_str;
}

