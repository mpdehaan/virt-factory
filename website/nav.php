<?php
  switch ($current_page) {

	case "about":
		echo "<ul id=\"nav\">
  		 <li id=\"active\"><a href=\"index.php\">About</a></li>
  		 <li><a href=\"news.php\">News</a></li>
   		<li><a href=\"download.php\">Download</a></li>
  		 <li><a href=\"faq.php\">FAQ</a></li>
  		 <li><a href=\"components.php\">Components</a></li>
  		 <li><a href=\"documentation.php\">Documentation</a></li>
  		 <li><a href=\"communicate\">Communicate</a></li>
 		</ul>";
		break;
  	case "news":
		echo "<ul id=\"nav\">
 		  <li><a href=\"index.php\">About</a></li>
  		 <li id=\"active\"><a href=\"news.php\">News</a></li>
  		 <li><a href=\"download.php\">Download</a></li>
  		 <li><a href=\"faq.php\">FAQ</a></li>
  		 <li><a href=\"components.php\">Components</a></li>
  		 <li><a href=\"documentation.php\">Documentation</a></li>
 		  <li><a href=\"communicate.php\">Communicate</a></li>
 		</ul>";
		break;
  	case "download":
		echo "<ul id=\"nav\">
   		<li><a href=\"index.php\">About</a></li>
  		 <li><a href=\"news.php\">News</a></li>
  		 <li id=\"active\"><a href=\"#\">Download</a></li>
  		 <li><a href=\"faq.php\">FAQ</a></li>
  		 <li><a href=\"components.php\">Components</a></li>
  		 <li><a href=\"documentation.php\">Documentation</a></li>
 		  <li><a href=\"communicate.php\">Communicate</a></li>
		 </ul>";
		break;
  	case "faq":
		echo "<ul id=\"nav\">
   		<li><a href=\"index.php\">About</a></li>
  		 <li><a href=\"news.php\">News</a></li>
  		 <li><a href=\"download.php\">Download</a></li>
  		 <li id=\"active\"><a href=\"faq.php\">FAQ</a></li>
  		 <li><a href=\"components.php\">Components</a></li>
  		 <li><a href=\"documentation.php\">Documentation</a></li>
  		 <li><a href=\"communicate.php\">Communicate</a></li>
 		</ul>";
		break;
  	case "communicate":
		echo "<ul id=\"nav\">
 		  <li><a href=\"index.php\">About</a></li>
		   <li><a href=\"news.php\">News</a></li>
  		 <li><a href=\"download.php\">Download</a></li>
  		 <li><a href=\"faq.php\">FAQ</a></li>
  		 <li><a href=\"components.php\">Components</a></li>
  		 <li><a href=\"documentation.php\">Documentation</a></li>
  		 <li id=\"active\"><a href=\"communicate.php\">Communicate</a></li>
 		</ul>";
		break;
	case "documentation":
                echo "<ul id=\"nav\">
                  <li><a href=\"index.php\">About</a></li>
                   <li><a href=\"news.php\">News</a></li>
                 <li><a href=\"download.php\">Download</a></li>
                 <li><a href=\"faq.php\">FAQ</a></li>
  		 <li><a href=\"components.php\">Components</a></li>
                 <li id=\"active\"><a href=\"documentation.php\">Documentation</a></li>                 
		<li><a href=\"communicate.php\">Communicate</a></li>
                </ul>";
		break;
	case "components":
		echo " <ul id=\"nav\">
  		 <li><a href=\"index.php\">About</a></li>
 		  <li><a href=\"news.php\">News</a></li>
  		 <li><a href=\"download.php\">Download</a></li>
  		 <li><a href=\"faq.php\">FAQ</a></li>
  		 <li id=\"active\"><a href=\"components.php\">Components</a></li>
  		 <li><a href=\"documentation.php\">Documentation</a></li>
 		  <li><a href=\"communicate.php\">Communicate</a></li>
 		</ul>";
		break;
	default:
		echo " <ul id=\"nav\">
  		 <li id=\"active\"><a href=\"index.php\">About</a></li>
 		  <li><a href=\"news.php\">News</a></li>
  		 <li><a href=\"download.php\">Download</a></li>
  		 <li><a href=\"faq.php\">FAQ</a></li>
  		 <li><a href=\"components.php\">Components</a></li>
  		 <li><a href=\"documentation.php\">Documentation</a></li>
 		  <li><a href=\"communicate.php\">Communicate</a></li>
 		</ul>";
		break;

}

?>

