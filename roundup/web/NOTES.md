
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

Roundup URL map check for backward compatibility:

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
       [x] /_file       - 500 TypeError: join()
       [x] /_file/      - 404
       [x] /_file/name  - 200 from STATIC_FILES or
                              TEMPLATES
    /@@file/(.*)
      StaticFileHandler
       [x] /@@file      - 500 TypeError: join()
       [x] /@@file/     - 404
       [x] /@@file/name - 200 from STATIC_FILES or
                              TEMPLATES 

