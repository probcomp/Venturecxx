// Copyright (c) 2015 MIT Probabilistic Computing Project.
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

function valueToString(value) {
    if (value instanceof Number) {
        return value.toFixed(2);
    } else if (value instanceof Array) {
        return String(value.map(valueToString));
    }
    return String(value)
}

function exprToString(expr, display_scopes) {
    //console.log(typeof expr);
    if (expr instanceof Array) {
        if (expr[0] === "scope_include" && !display_scopes) {
            return exprToString(expr[3]);
        } else {
            return "(" + expr.map(function (e) { return exprToString(e, display_scopes) }).join(" ") + ")";
        }
    } else if (expr instanceof String) {
        return expr;
    } else {
        return valueToString(expr.value);
    }
}

function directiveToString(directive, display_scopes) {
    var directive_str = "[" + directive.instruction + " ";
    
    if (directive.instruction === "assume") {
        directive_str += directive.symbol.value + " ";
    }
    
    directive_str += exprToString(directive.expression, display_scopes);
    
    if (directive.instruction === "observe") {
        directive_str += " " + valueToString(directive.value);
    }
    
    directive_str += "]";
    directive_str = directive_str.replace(/add/g, "+")
    directive_str = directive_str.replace(/sub/g, "-")
    directive_str = directive_str.replace(/mul/g, "*")
    directive_str = directive_str.replace(/div/g, "/")
    return directive_str;
}

blacklist = ['demo_id', 'model_type', 'use_outliers', 'infer_noise', 'outlier_prob', 'show_scopes', 'outlier_sigma'];

function isExtraneous(directive) {
    if (directive.instruction === "predict") return true;
    if (directive.instruction === "assume") {
        return blacklist.indexOf(directive.symbol) >= 0;
    }
    return false;
}

function VentureCodeHTML(directives, display_scopes) {
    var venture_code_str = "<b>Venture code:</b><br>";

    for (i = 0; i < directives.length; ++i) {
        if(!isExtraneous(directives[i])) {
            venture_code_str += directiveToString(directives[i], display_scopes) + '<br/>';
        }
    }
    
    return venture_code_str;
}

    
function toDict(type, value) {
    return {
        type: type,
        value: value
    };
}

function toNumber(x) {
    return toDict("number", x);
}

function toArray(xs) {
    return toDict("array", xs.map(toNumber));
}

