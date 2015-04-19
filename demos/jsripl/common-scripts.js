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

var venture__venture_ec2_demo_instance_host = "54.235.201.199";
var venture__venture_ec2_demo_instance_port = 80;

function CheckCookieWithVentureRIPLAddress() {
    if ($.cookie('venture__ripl_host') == undefined) {
        GoToSelectRIPLAddress();
    }
    $("#ripl_address_info").html("You are using <i>venture://" + $.cookie('venture__ripl_host') + ":" + $.cookie('venture__ripl_port') + "</i>. <a href='#' style='text-decoration: underline;' onClick='GoToSelectRIPLAddress()'>Change</a>");
}

function GoToSelectRIPLAddress() {
    navigateToUrl("select_venture_server.html");
}

function navigateToUrl(url) {
    $.cookie("venture__demo_page", window.location, { expires: 21 });
    window.location = url;
}

