<head>
    <title>Mongorunway</title>
    <style>
        /* Set a gradient background */
        .gradient-heading {
            -webkit-background-clip: text;
            font-family: 'Roboto', sans-serif;
            text-align: center; /* Centered horizontally */
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400&display=swap" rel="stylesheet">
</head>


<head>
    <title>Centered Shield.io Icons</title>
<style>
    /* Center the icons horizontally */
    .centered-icons {
        display: flex;
        justify-content: center;
    }

    /* Add margin to the icons */
    .centered-icons .icon {
        margin: 10px;
    }
</style>
</head>
<body>
    <h1 class="gradient-heading" align="center">Mongorunway<br>Migration can be easy</h1>
    <div class="centered-icons">
        <div class="icon">
            <img src="https://img.shields.io/github/actions/workflow/status/Animatea/mongorunway/main.yml?style=flat" alt="CI">
        </div>
        <div class="icon">
            <img src="https://img.shields.io/pypi/pyversions/mongorunway" alt="Py versions">
        </div>
        <div class="icon">
            <img src="https://img.shields.io/badge/mongodb-4.2 | 4.4 | 5.0 | 6.0-brightgreen" alt="Mongo versions">
        </div>
    </div>
</body>

<style>
    /* Create a blurry image effect */
    .blurry-image {
        display: flex;
        justify-content: center;
        align-items: center;
        position: relative;
    }

    /* Apply the blur effect to the background image */
    .blurry-image::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("assets/project-structure-stakeholder-circle-map.png") center center no-repeat;
        background-size: cover;
        filter: blur(10px);
        opacity: 0.8;
        z-index: -1;
    }
</style>

<div class="blurry-image">
    <img src="assets/project-structure-stakeholder-circle-map.png" alt="Image">
</div>

<div align="center">
    <strong>Mongorunway</strong> is a tool for MongoDB migrations that allows you to version the states of your 
    databases. By default, Mongorunway uses <code>builtins.None</code> as the initial state indicator that 
    has no migrations applied. The versioning starts from one onwards.
</div>
