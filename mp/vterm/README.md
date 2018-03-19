# Alternative dupterm implementaion (WebREPL available)

## os.dupterm
`os.dupterm` is re-writtern for esp32, it's not comptible original implementation in extmod/uos_dupterm.c.  That has two optional arugumets, 2nd parameter is same as original one and it's ignored too, 3rd parameter  is a stack size of stream reading thread which is needed for a REPL reader to read a character from stream object with no support non-blocking read. If 3rd parameter is omitted, passed stream object is assumed non-blocking type.

## socket.airterm
`socket.airterm` is a specialized dupterm. It accept only socket object and it call lwip-API directoly. As a result, read/write peformance is better than `os.dupterm`.

## socket.setsockopt support TCP_NODELAY
A TCP_NODELAY socket option is added to socket module to improve interactive perfromance of above these functions. 

## webrepl
webrepl module is availabe by `os.dupterm` and customized webrepl.py.
