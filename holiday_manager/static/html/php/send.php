<?php
	if($_POST){
		$to = 'user@domain.com'; /*Put Your Email Adress Here*/
		$from_name = $_POST['name'];
		$from_email = $_POST['email'];
		$message = $_POST['message'];
		$subject = "Contact form message: $from_name <$from_email>";
		$header = "From: $from_name <$from_email>";
		mail($to, $subject, $message, $header);
	}
?>