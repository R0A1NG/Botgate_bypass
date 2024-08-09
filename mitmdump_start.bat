@echo off
CHCP 65001
mitmdump -p 8081 -s mitmdump.py --ssl-insecure