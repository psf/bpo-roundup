
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

    [ ] urlmap component

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
