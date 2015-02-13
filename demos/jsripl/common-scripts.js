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

