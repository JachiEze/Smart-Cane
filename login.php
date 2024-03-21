<?php
// Check if the form is submitted
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Check username and password
    $username = $_POST['username'];
    $password = $_POST['password'];

    // Here, you should replace 'your_username' and 'your_password' with your actual username and password
    if ($username === 'jachi' && $password === 'eze') {
        // Redirect to map.html upon successful login
        header("Location: map.html");
        exit();
    } else {
        // Redirect back to login.html upon failed login
        header("Location: login.html");
        exit();
    }
}
?>
