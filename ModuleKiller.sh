#!/bin/bash
kill -9 $(ps aux | grep do_work | grep -v grep| awk '{print $2}')