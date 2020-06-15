# TODO

- Replace all sockets with PIPEs between processes. I've come to the conclusion that the system will be never distributed across machines. Hence, sockets are a waste of time.
- Way too many magic strings in the code. Create a strings.py file, and import them when needed.
- Perform input validation everywhere.
- Take full advantage of the shared memory.
- Complete all the tasks marked by a `TODO` in the code.
