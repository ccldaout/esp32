# esp32 - My Play Ground

This repository have mainly results of trial of MicroPython on esp32.
- `mp/...`

   My customized sources and result of `git diff mater`. 

   - `vterm / airterm / dupterm`

     Termianl duplicators. `vterm` is a framework of duplication. `airterm` is one of duplicatior, it communicate raw data by LWIP level interface. `dupterm` is my original implementation on the `vterm` framework.

   - `genstream`

     `genstream` privide stream protocol to user defined class which have a read and a write method.

- `mp/vterm (Obsolete)`

   A patch of MicroPython realize dupterm, airterm (my specialized dupterm) and WebREPL on esp32.
   They are already included above tree.
   
- `tools`

   There are several tools on PC side. 
   
   - `espmini.sh`
   
     Minimum administraion functions on a minimum boot mode.
     File transfer (get/put) and mkdir are supported.
     
   - `espadm.py`
   
     Several administration functions on a full boot mode. 
     File transfer (get/put), mkdir, rmdir, ls, remove, rename, display on/off, enable services, and reset.
     
   - `pnet.c`
     
     Minimum airterm (REPL on the air) client.
     
- `upy/*`
   
   User defined micropython scripts.
     
   - `upy/boot/*`
     
     Scripts on a boot sequence. `full` mode enable wifi and support several administration services which are depend on other scripts.
     On the other hand, `mini` mode enable wifi and support self contained minimum administrations. 
       
   - `upy/lib/*`
     
     There are several kind of library, threading (my origianl port), socket service framework, display, wifi, motor drivers, and so on.
       
   - `upy/service/*`
     
     There are several services implemented on above libraries. On the `full` mode boot, admin service is enable. 

   - `upy/test/vsrfs.py`

     Very Slow Remote File System over my original protocol.
