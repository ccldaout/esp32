# esp32 - My Play Ground

## Custom firmware

My custom firmware `esp32-YYYYMMDD-v1.9.x-public.in` is located at top directory. It has several diffrences as follow:

### terminal duplication

#### `vterm`

A framework for REPL terminal (console?) duplication.
  
#### `socket.airterm`

This is a REPL terminal duplication based on vterm. It is combined socket object and communicate remote host by LWIP socket interface directly under background.
  
#### `uos.dupterm`

`os.dupterm` is re-writtern for esp32, it's not comptible original implementation in extmod/uos_dupterm.c.  That has two optional arugumets, 2nd parameter is same as original one and it's ignored too, 3rd parameter  is a stack size of stream reading thread which is needed for a REPL reader to read a character from stream object with no support non-blocking read. If 3rd parameter is omitted, passed stream object is assumed non-blocking type.

### WebREPL

`_webrepl` module is availabe by above `os.dupterm`. `webrepl.py` is also customized for ESP32.

###  TCP_NODELAY (**Experimental**)

A TCP_NODELAY socket option is added to socket module to improve interactive perfromance of above these functions. 

  **CAUTION**: This option will cause unexpceted closed connection. I don't get a reason of it at this time.

### genstream.genstream

`genstream` class provide stream protocol to user defined class which have a read method and a write method. This function is needed for a python script on a VFS to be imported.

### extmod/vfs.c

Original `mp_vfs_import_stat` search file for only internal and FAT file system. This function is extended to search it for all VFS.

### ports/esp32/machine_uart.c

Original `machine_uart_make_new` which is called `machine.UART()` install a uart driver with a event queue handle. But no function read the handle. As a result, `event queue full` is caused. This function don't pass the handle in the install the driver. **This is a ad-hoc step.**

## VSRfs - Very Slot (Stupid?) Remote File System

VSRfs provide a file system interface over the network. You can `import` a python script on your PC without uploading. VSRfs depend on a custom class `genstream`, so it' required that customized firmware or a patch of micropython sources, both are provided on this site.

- server side - tools/vsrfsd.py

  VSRfs server program is `tools/vsrfsd.py` depended on my another `tpp` package. The `tpp` is also public on a github. You can setup by following commands:

  ```sh
  prompt_% mkdir ~/test
  prompt_% cd ~/test
  promot_% git clone https://github.com/ccldaout/tpp.git
  prompt_% cp FOOBAR/tools/vsrfsd.py .
  prompt_% ./vsrfsd.py
  Usage: [host]:port root_dir
  ```

  `vsrfsd` require two parameters. 1st parameter is address of UDP server in the form of `host`:`port`.
  2nd parameter is root directory to be exported.


- client side - upy/test/vsrfs.py
  
  VSRfs client is VFS object of MicroPython. You can setup VSRfs in the following way:
    
  ```python
  >>> from vsrfs import VSRfs
  >>> vsrfs = VSRfs(('HOST_NAME', PORT_NUM))
  >>> import os
  >>> os.moount(vsrfs, '/VSR')
 ```
 
  MEMO: vsrfs.py require upy/lib/mipc.py


## Directories

- `mp/...`

   My customized sources and result of `git diff mater`. 

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
