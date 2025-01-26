# Software Architecture

This document provides an overview of the KeyShot submitter extension and adaptor that are in this repository.
The intent is to help you have a basic understanding of what the applications are doing to give you context to understand what you are looking at when diving through the code. This is not a comprehensive deep dive of the implementation.

## KeyShot Submitter extension

The KeyShot submitter is a single file `Submit to AWS Deadline Cloud.py`. This is stored in the repository at `/src/deadline/keyshot_submitter` and is a KeyShot script that should be copied to the KeyShot scripts folder, which is usually:
- Windows (choose one):
    - User scripts folder e.g. `%USERPROFILE%/Documents/KeyShot/Scripts`
    - System-wide scripts folder e.g. `%PROGRAMFILES%/KeyShot/Scripts`
- Mac: `/Library/Application Support/KeyShot12/` or `/Library/Application Support/KeyShot/` depending on your version of Keyshot.
    - You can navigate to the folder by going to Finder, clicking the menu for Go -> Go to Folder, and typing in the folder path.

`Submit to AWS Deadline Cloud.py` provides all of the business logic for the submitter. We chose the single file approach for this submitter due to non-standard behaviour in KeyShot's system path handling. Note that KeyShot is missing some standard Python libraries, so not all imports may work. We work around these by using alternative libraries.

### `deadline.keyshot_submitter`

Fundamentally, what this submitter is doing is creating a [Job Bundle](https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/build-job-bundle.html)
and calling the [`deadline` Python package](https://pypi.org/project/deadline/) command line interface to generate the UI that is displayed to the user. The important parts to know about in a job bundle are:

1. The job template file. The submitter code dynamically generates the template based on properties of the specific scene file that is loaded. For example, it may contain a step for each layer of the scene to render.
2. Asset references. These are the files that the job, when submitted, will require to be able to run. The submitter contains code that introspects the loaded scene to automatically discover these. The submitter extension's UI allows the end-user to modify this list of files.

The job submission itself is handled by functionality within the `deadline` package that is hooked up when the UI is created.

## KeyShot Adaptor Application

See the [README](../README.md#Adaptor) for background on what purpose the adaptor application serves.

The implementation of the adaptor for KeyShot has two parts:

1. The adaptor application itself whose code is located in `src/deadline/keyshot_adaptor/KeyShotAdaptor`. This is the implementation of the command-line application (named `keyshot-openjd`) that is run by jobs created by the KeyShot submitter.
2. A "KeyShotClient" application located in `src/deadline/keyshot_adaptor/KeyShotClient`. This is an application that is run within KeyShot by the adaptor application when it launches KeyShot. The KeyShot Client remains running as long as the KeyShot process is running. It facilitates communication between the adaptor process and the running KeyShot process; communication to tell KeyShot to, say, load a scene file, or render frame 20 of the loaded scene.

The adaptor application is built using the [Open Job Description Adaptor Runtime](https://github.com/OpenJobDescription/openjd-adaptor-runtime-for-python) package. This package supplies the application entrypoint that defines and parses the command-line subcommands and options, as well as the business logic that drives the state machine of the adaptor itself. Please see the README for the runtime package for information on the lifecycle states of an adaptor, and the command line options that are available.

Digging through the code for the adaptor, you will find that the `on_start()` method is where the KeyShot application is started.
The application is started with arguments that tell KeyShot to run the "KeyShot Client" application. This application is, essentially, a secure web server that is running over named pipes rather than network sockets. The adaptor sends the client commands (look for calls to `enqueue_action()` in the adaptor) to instruct KeyShot to do things, and then waits for the results of those actions to take effect.

You can see the definitions of the available commands, and the actions that they take by inspecting `src/deadline/KeyShotClient/keyshot_client.py`. You'll notice that the commands that it directly defines are minimal, and that the set of commands that are available is updated when the adaptor sends it a command to set the renderer being used.

The final thing to be aware of is that the adaptor defines a number of stdout/stderr handlers. These are registered when launching the KeyShot process via the `LoggingSubprocess` class. Each handler defines a regex that is compared against the output stream of KeyShot itself, and code that is run when that regex is matched in KeyShot's output. This allows the adaptor to, say, translate the rendering progress status from KeyShot into a form that can be understood and reported to Deadline Cloud.
