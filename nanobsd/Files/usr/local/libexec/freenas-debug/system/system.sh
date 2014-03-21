#!/bin/sh
#+
# Copyright 2011 iXsystems, Inc.
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS 	 
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#####################################################################


system_opt() { echo t; }
system_help() { echo "Dump System Information"; }
system_directory() { echo "System"; }
system_func()
{
	section_header "uptime"
	uptime
	section_footer

	section_header "date"
	date
	section_footer

	section_header "ntpq -c rv"
	ntpq -c rv
	section_footer

	section_header "ps -axw"
	ps -axw
	section_footer

	section_header "mount"
	mount
	section_footer

	section_header "df -h"
	df -h
	section_footer

	section_header "swapinfo -h"
	swapinfo -h
	section_footer

	section_header "kldstat"
	kldstat
	section_footer

	section_header "dmesg -a"
	dmesg -a
	section_footer

	section_header "procstat -akk"
	procstat -akk
	section_footer

	section_header "vmstat -i"
	vmstat -i
	section_footer
}
