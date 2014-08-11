
Engineering notes for Roundup components for web.


### Logical structure of web components

An attempt to see what components are present in
web request processing.

    +-----------+
    |           |
    | Router    |
    └─----------+                     (pure logic)
    ----------------------------------------------
    +-----------+    
    |           |    
    | Login     |    
    └-----------+   (logic + templates + messages)
    ----------------------------------------------
    +-----------+
    ¦           ¦
    ¦ User DB   ¦
    └-----------+                       (messages)


Every component consists of messages (data), logic
(code) and representation (templates). Message
definition (data) also takes into account actions
that make component work. Templates are mostly
needed for human readability. 


### Router

Status for Roundup URL map check:

    [ ] check urlpath values for
      [ ] example.com
      [ ] example.com/
      [ ] example.com/tracker
      [ ] example.com/tracker/
      [ ] example.com/tracker/item
      [ ] example.com/tracker?anything
      [ ] example.com/tracker/?anything
      [ ] example.com/tracker/item?anything

    [x] get full list of url handlers
        (1.5.0, entrypoing: cgi.client.main)
      [x] /xmlrpc     - hardcoded xmlrpc endpoint
      [x] /           - main home page
          /index
          /home
      [x] /_file      - static resources
          /@@file
      [x] /<class>    - dynamic handler based on db

    [ ] check url handling for db scheme paths

      [ ] example.com/tracker/class
      [ ] example.com/tracker/class/
      [ ] example.com/tracker/class1
      [ ] example.com/tracker/class1/

    [ ] check url handling for static files

    /_file/(.*) 
      StaticFileHandler
       [ ] /_file
       [ ] /_file/
       [ ] /_file/name
    /@@file/(.*)
      StaticFileHandler
       [ ] /@@file
       [ ] /@@file/
       [ ] /@@file/name

