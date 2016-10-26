define([
    'jquery',
    'notebook/js/toolbar',
], function(
    $
) {
    function load_ipython_extension() {
      var PACKAGE_NAME = "trustedanalytics";
      var MENU_SELECTOR = ".navbar-nav .dropdown";
      var TAP_LINKS = 
      {
      "install":
      {
        name: "Install ATK Client",
        snippet: "#To install direclty from a running ATK server use \n" +
                "#!pip install SERVER_URI/client\n\n"+
                "#To install from pypi.python.org\n"+
                "#!pip install trustedanalytics\n\n" +
                "#a specific version can be installed by providing the version after the package name\n" +
                "#!pip install trustedanalytics==0.4.2.dev201512019643\n",
        id: "install-atk",
        title: "Install ATK Client"
      },
      "connect":
      {
        name: "Create Credentials",
        link: "#",
        title: "Adds boilerplate for creating the credentials file",
        snippet: "import trustedanalytics as atk\n\n" +
                 "print \"ATK installation path = %s\" % (atk.__path__) \n\n" +
                 "#You will need your server URI to create the credentials file.\n" +
                 "#Don't include the protocol when assigning to atk.server.uri.\n" +
                 "#    incorrect atk.server.uri = 'http://my-server.some.domain.com'\n" +
                 "#    correct atk.server.uri = 'my-server.some.domain.com'\n" +
                 "atk.server.uri = 'YOUR_ATK_SERVER_URI' \n\n"+
                 "#The file name passed to create_credentails_file() can be anything you like\n"+
                 "#     but you must use the same name when executing atk.connect.\n" +
                 "atk.create_credentials_file('ATK.creds')\n\n" +
                 "#After creating the credentials file we can connect to the ATK server.\n"+
                 "atk.connect(r'/ATK.creds')"
      },
      "s1":
      {"section": true},
      "cd": 
      {
        name: "ATK Documentation",
        link: "http://trustedanalytics.github.io/atk/",
        title: "Trusted Analytics Python Client Documentation"
      },
      "git":
      {
        name: "ATK Git Repo",
        link: "https://github.com/trustedanalytics/atk",
        title: "ATK Github Repository"
      },
      "jira":
      {
        name: "TAP Jira",
        link: "https://trustedanalytics.atlassian.net",
        title: "File bugs"
      },
      "tap":
      {
        name: "TAP Home Page",
        link: "http://trustedanalytics.org/",
        title: "Trusted Analytics Platform Home Page"
      },
      "community":
      {
        name: "TAP Community",
        link: "https://community.trustedanalytics.org/",
        title: "Trusted Analytifcs Platform Community"
      }
    }
    
    function sort(x, y){
      var xn = Date.parse(x["upload_time"]);
      var yn = Date.parse(y["upload_time"]); 
      return ((xn > yn) ? -1 : ((xn < yn) ? 1 : 0));
    }
    var recent_releases = function(releases){
      max = 5;
      var tmp = [];
      for( var key in releases){
        if( max <= 0 ){break;}
        tmp.push(releases[key]);
        max = max - 1;
      }
      return tmp;
    }
    var add_recent = function(release,section){
      TAP_LINKS["install"]["menu"].push(section)
      releases = recent_releases(release);
      for( var x in releases){
        TAP_LINKS["install"]["menu"].push(releases[x]);
      }
    }
    var atk_releases = function(){
      $.ajax({
        method: 'POST',
        dataType: 'json',
        url: 'http://pypi.python.org/pypi/trustedanalytics/json?callback=?',
        success: function(data) {
          var releases = [];
          var weekly = [];
          var production = [];
          for(var key in data.releases){
            
            date = new Date(Date.parse(data.releases[key][0]["upload_time"]))
            data.releases[key][0]["version"] = key;
            data.releases[key][0]["title"] = "Uploaded to pypi.python.org on " + date.toLocaleString();
            data.releases[key][0]["name"] = key;
            data.releases[key][0]["link"] = "#";
            data.releases[key][0]["snippet"] = "#This will install version "+key+" of the ATK client\n"+
                                               "!pip install trustedanalytics=="+key;
            data.releases[key][0]["classs"] = "pypi-install";
            
            releases.push(data.releases[key][0]);
            if( key.indexOf("dev") > -1 ){
              weekly.push(data.releases[key][0])
            }else if(key.indexOf("post") > -1){
              production.push(data.releases[key][0])
            }else{
              weekly.push(data.releases[key][0])
            }
          }
          weekly.sort(sort);
          
          production.sort(sort);
          
          
          TAP_LINKS["install"]["menu"] = [
            {"name":"From PyPi central", 
            "title":"Install the client from PyPi central.", 
            "link": "https://pypi.python.org/pypi/trustedanalytics"},
            {"section":true}
          ];
          
          add_recent(weekly, {"name": "Weekly Builds", "title": "Most recent weekly builds."});
          add_recent(production, {"name":"Production Builds", "title": "Most recent production builds."});
          
          TAP_LINKS["install"]["menu"].push({"section":true});
          TAP_LINKS["install"]["menu"].push({"name": "From ATK Server",
          "title": "Install the client directly from an ATK server instance.",
          "link": "#",
          "snippet": "#Replace YOUR_ATK_SERVER_URL with the URL to your ATK server instance. \n\n" +
                     "!pip install YOUR_ATK_SERVER_URL/client\n\n"})
          
          console.log(TAP_LINKS);
          },
        complete: function(){
            create_tap_menu(TAP_LINKS);
          }
      });
    }
    
    var tap_menu_item = function(item){
      
      if( item.section){
        var tap_menu_item = $(MENU_SELECTOR +" li[class|=divider]").first().clone()[0]
      }else{
        var tap_menu_item = $(MENU_SELECTOR).find("li").filter(function(index){ return !$(this).hasClass("dropdown-submenu")   }).first().clone()[0];
        $(tap_menu_item).attr("title", item.title)
          
        //specific for code links
        if(item.snippet){ $(tap_menu_item).attr("snippet", item.snippet) }
        if(item.id){ $(tap_menu_item).attr("id", item.id)}else{$(tap_menu_item).attr("id", "")}
        if(item.classs){ $(tap_menu_item).addClass(item.classs)}
        if(item.link && item.link != "#"){
          $(tap_menu_item).find("a")
          .attr("href", item.link)
          .attr("target", "_blank")
          .html("<i class=\"fa fa-external-link menu-icon pull-right\"></i><span>"+item.name+"</span>")
        }
        else{
           $(tap_menu_item).find("a")
          .attr("href", '#').text(item.name);
        }
      }
      return tap_menu_item;
    }
    var tap_sub_menu_item = function(item, parent){
      var tap_sub_menu_item = $(".dropdown-submenu").first().clone()[0];
      
      $(tap_sub_menu_item).find("li").detach();
      if(item.id){ $(tap_menu_item).attr("id", item.id)} else {$(tap_menu_item).attr("id", "")}
      $(tap_sub_menu_item).find("a").text(item.name);
      
      
      if( item.menu ){
        for( sitem in item.menu){
          
          var menu_item = ( item.menu[sitem].menu ? tap_sub_menu_item(item.menu[sitem]) : tap_menu_item(item.menu[sitem]))
          
          $(tap_sub_menu_item).find("ul").first().append(menu_item)
        }
      }
      
      return tap_sub_menu_item;
    }
    
    var create_tap_menu = function(links){
      var tap_menu = $(".navbar-nav .dropdown").last().clone()[0];
      $(tap_menu).find(".dropdown-toggle").text("TAP Help");
      $(tap_menu).find("ul").first().attr("id", "tap_help" ).css("width", "200px");
      
      $(tap_menu).find("#tap_help li").detach()

      for( var link in links){
        
        
        var menu_item = ( links[link].menu ? tap_sub_menu_item(links[link]) : tap_menu_item(links[link]))
        
        
        $(tap_menu).find("ul").first().append(menu_item)
      }

      $(".navbar-nav").append(tap_menu)

      $("#tap_help li[snippet]").click(function(click){
        snippet = $(this).attr("snippet")
        cell = Jupyter.notebook.insert_cell_above();
        cell.set_text(snippet);
      })
    }
    
    atk_releases();
  }
    return {
        load_ipython_extension: load_ipython_extension
    };
});
