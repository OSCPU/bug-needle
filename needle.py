import subprocess
import random
import os
from pathlib import Path

# bug patterns are defined here
# NOTE:
#  1. `src` and `dst` will be concatenated to form a substitution command for `sed`
#  2. the first character of `src` will be considered as the seperator for the substitution command
#  3. pay attention to the escaped sequence in python string
#  4. Example: ['/\(i *\)++', '\\1--'] will form the following command
#                     s/\(i *\)++/\1--/

buglist = [  # TODO: add more bug patterns
  #   src         dst
  ['/\(i *\)++', '\\1--'],
]

#===========================================
# common functions

def shell(cmd):   # execute the shell command and return the output as a string
    output = subprocess.Popen("bash -c \"" + cmd + "\"", stdout = subprocess.PIPE, shell = True).communicate()
    return output[0].decode('UTF-8')

def shellv(cmd):  # return array of lines
    res = shell(cmd).split('\n')
    if res[-1] == '':
        res = res[:-1]
    return res


#===========================================
# check ysyx project

if os.getenv('YSYX_HOME') == None:
    print("Error: YSYX_HOME is not set!")
    exit(-1)

YSYX_HOME = Path(os.getenv('YSYX_HOME'))
print("YSYX_HOME=" + str(YSYX_HOME))

def check_path(path):
    if not path.exists():
        print("Error: " + str(path) + " does not exist!")
        exit(-1)

NEMU_HOME = YSYX_HOME / 'nemu'
AM_HOME = YSYX_HOME / 'abstract-machine'
OS_HOME = YSYX_HOME / 'nanos-lite'
NAVY_HOME = YSYX_HOME / 'navy-apps'
NPC_HOME = YSYX_HOME / 'npc'

for p in [NEMU_HOME, AM_HOME, OS_HOME, NAVY_HOME, NPC_HOME]:
    check_path(p)

#===========================================
# compute filelist

NEMU_filelist  = shellv("find " + str(NEMU_HOME / "src" ) + " -name '*.[ch]' | grep -v riscv32")
AM_filelist    = shellv("find " + str(AM_HOME / "am/src/riscv/nemu" ) + " -name '*.[chS]'")
AM_filelist   += shellv("ls " + str(AM_HOME / "am/src/platform/nemu/{include/nemu.h,ioe/{gpu,input,ioe,timer}.c}"))
AM_filelist   += shellv("ls " + str(AM_HOME / "klib/src/{stdio,string}.c"))
OS_filelist    = shellv("find " + str(OS_HOME / "src" ) + " -name '*.c'" )
NAVY_filelist  = shellv("ls " + str(NAVY_HOME / "libs/libos/src/{syscall.c,crt0/{crt0.c,start/riscv64.S}}"))
NAVY_filelist += shellv("ls " + str(NAVY_HOME / "libs/libndl/NDL.c"))
NAVY_filelist += shellv("ls " + str(NAVY_HOME / "libs/libminiSDL/src/{event,timer,video}.c"))

filelist = NEMU_filelist + AM_filelist + OS_filelist + NAVY_filelist
for f in filelist:
    check_path(Path(f))

#===========================================
# random select a file and a bug

def rand_element(array):
    i = random.randint(0, len(array) - 1)
    return array[i]

filename = None
bug = None

while True:
    filename = rand_element(filelist)
    bug = rand_element(buglist)
    # check if we can find the bug pattern in the file
    regex = bug[0][1:]
    grep_cmd = "grep -n '" + regex + "' " + filename
    grep_results = shellv(grep_cmd)

    if grep_results != []:
        break
    # if we can not find the bug pattern in the file, select again

#===========================================
# select a random matched line and prepare the `sed` command to insert the bug

grep_random = rand_element(grep_results)
line = grep_random.split(':')[0]

def sed_str(bug):
    seperator = bug[0][0]
    return bug[0] + bug[0][0] + bug[1] + bug[0][0]

sed_cmd = "sed -e '" + line + "s" + sed_str(bug) + "' " + filename

#===========================================
# display the `sed` command and different after insertion for debug

if os.getenv('DEBUG') != None:
    print(sed_cmd)
    print(shell(sed_cmd + ' | diff ' + filename + ' -'))

#===========================================
# apply the `sed` command to insert the bug
sed_cmd = "sed -i" + sed_cmd[3:]
shellv(sed_cmd)

print("Insert 1 bug somewhere sucessfully!")
