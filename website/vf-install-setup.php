<?php
  $current_page = 'documentation';
?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
<meta name="description" content="" />
<meta name="keywords" content="" />
<title>Virt-Factory</title>

  <link rel="stylesheet" href="css/style.css" type="text/css" media="all" />
</head>

<body>
<div id="wrap">
<?php 
  include("top.html"); 
?>

<div id="main">
 <div id="sidebar">
<?php 
  include("nav.php"); 
?>
 </div>

<div id="content">
<?php 
  include("docs/vf-install-setup.html"); 
?>

</div>
</div>
<div id="footer">
<?php 
  include("footer.html"); 
?>
</div>
</div>
</body>
</html>
