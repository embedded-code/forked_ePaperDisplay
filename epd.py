import os
import socket
from time import sleep

VERBOSE = False
LAN = "192.168.0.22" # EPD's home IP
AP = "192.168.1.1"   # EPD's own AP IP
PORT = 3333
MAC = "/dev/cu.usbserial"
LINUX = "/dev/ttyUSB0"
DEV = "" # insert your serial port here if known

if DEV == "":
    # try to auto-determine what serial port to use
    # this is not guaranteed to work!
    from platform import system
    if system()=='Linux':
        DEV = LINUX
    elif system()=='Darwin':
        DEV = MAC
    else:
        DEV = raw_input('Define serial port for EPD connection (e.g. /dev/ttyUSB1 or just hit enter for none): ')

soc                 = None
BAUD_RATE           = 115200
BAUD_RATE_DEFAULT   = 115200
BAUD_RATES          = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
MAX_STRING_LEN      = 1024 - 4

# frame segments
FRAME_BEGIN         = "A5"
FRAME_END           = "CC33C33C"

# colours
BLACK               = "00"
DARK_GRAY           = "01"
GRAY                = "02"
WHITE               = "03"

# commands
CMD_HANDSHAKE       = "00"  # handshake
CMD_SET_BAUD        = "01"  # set baud
CMD_READ_BAUD       = "02"  # read baud
CMD_MEMORYMODE      = "07"  # set memory mode
CMD_STOPMODE        = "08"  # enter stop mode 
CMD_UPDATE          = "0A"  # update
CMD_SCREEN_ROTATION = "0D"  # set screen rotation
CMD_LOAD_FONT       = "0E"  # copy font files from SD card to NandFlash.
                            # Font files include GBK32/48/64.FON
                            # 48MB allocated in NandFlash for fonts
                            # LED will flicker 3 times when starts and ends.
CMD_LOAD_PIC        = "0F"  # Import the image files from SD card to the NandFlash.
                            # LED will flicker 3 times when starts and ends.
                            # 80MB allocated in NandFlash for images
CMD_SET_COLOR       = "10"  # set colour
CMD_SET_EN_FONT     = "1E"  # set English font
CMD_SET_CH_FONT     = "1F"  # set Chinese font

CMD_DRAW_PIXEL      = "20"  # set pixel
CMD_DRAW_LINE       = "22"  # draw line
CMD_FILL_RECT       = "24"  # fill rectangle
CMD_DRAW_RECT       = "25"  # draw rectangle
CMD_DRAW_CIRCLE     = "26"  # draw circle
CMD_FILL_CIRCLE     = "27"  # fill circle
CMD_DRAW_TRIANGLE   = "28"  # draw triangle
CMD_FILL_TRIANGLE   = "29"  # fill triangle
CMD_CLEAR           = "2E"  # clear screen use back colour
CMD_DRAW_STRING     = "30"  # draw string
CMD_DRAW_BITMAP     = "70"  # draw bitmap


# FONT SIZE (32/48/64 dots)
GBK32               = "01"
GBK48               = "02"
GBK64               = "03"
    
ASCII32             = "01"
ASCII48             = "02"
ASCII64             = "03"


# Memory Mode
MEM_NAND            = "00"
MEM_SD              = "01"


# set screen rotation
EPD_NORMAL          = "00"     #screen normal
EPD_INVERSION       = "01"     #screen inversion      


# command define
_cmd_handshake   = FRAME_BEGIN+"0009"+CMD_HANDSHAKE+FRAME_END
_cmd_read_baud   = FRAME_BEGIN+"0009"+CMD_READ_BAUD+FRAME_END
_cmd_stopmode    = FRAME_BEGIN+"0009"+CMD_STOPMODE+FRAME_END
_cmd_update      = FRAME_BEGIN+"0009"+CMD_UPDATE+FRAME_END
_cmd_clear       = FRAME_BEGIN+"0009"+CMD_CLEAR+FRAME_END
_cmd_import_font = FRAME_BEGIN+"0009"+CMD_LOAD_FONT+FRAME_END
_cmd_import_pic  = FRAME_BEGIN+"0009"+CMD_LOAD_PIC+FRAME_END
_cmd_use_nand    = FRAME_BEGIN+"000A"+CMD_MEMORYMODE+MEM_NAND+FRAME_END
_cmd_use_sd      = FRAME_BEGIN+"000A"+CMD_MEMORYMODE+MEM_SD+FRAME_END


# vector 7 segment LCD digits (calculator-like digits)
# 
# 34 points that make up all the stokes
# origin is top-left corner
# see ePaperDisplay/docs/LCD_digit_font_design.svg for reference

LCD_DIGIT_WIDTH = 120
LCD_DIGIT_HEIGHT = 220
LCD_SPACING = 20 # space between 2 adjacent digits

LPBG0 = [0,0] # two points defining the background area of each digit
LPBG1 = [LCD_DIGIT_WIDTH,LCD_DIGIT_HEIGHT]

LP01 = (20,0)
LP02 = (100,0)
LP03 = (10,10)
LP04 = (110,10)
LP05 = (0,20)
LP06 = (120,20)
LP07 = (30,30)
LP08 = (90,30)
LP09 = (45,60)
LP10 = (75,60) # unused
LP11 = (45,90) # unused
LP12 = (75,90)
LP13 = (0,95)
LP14 = (30,95)
LP15 = (90,95)
LP16 = (120,95)
LP17 = (15,110)
LP18 = (105,110)
LP19 = (0,125)
LP20 = (30,125)
LP21 = (90,125)
LP22 = (120,125)
LP23 = (45,130)
LP24 = (75,130) # unused
LP25 = (45,160) # unused
LP26 = (75,160)
LP27 = (30,190)
LP28 = (90,190)
LP29 = (0,200)
LP30 = (120,200)
LP31 = (10,210)
LP32 = (110,210)
LP33 = (20,220)
LP34 = (100,220)

#  ---               H1
# | . |           V1 C1 V2
#><---><         T1T2H2T3T4
# | . |           V3 C2 V4
#  ---               H3
# 
# each horizontal/vertical stroke is drawn with 4 filled triangles
# each dot of colon is a filled rectangle
# each triangle filler beside H2 is a filled triangle
# H2 overlaps with T2 and T3

H1 = [(LP01,LP07,LP03),(LP01,LP07,LP02),(LP02,LP08,LP04),(LP02,LP08,LP07)]
H2 = [(LP14,LP20,LP17),(LP14,LP20,LP15),(LP15,LP21,LP20),(LP15,LP21,LP18)]
H3 = [(LP27,LP33,LP31),(LP27,LP33,LP28),(LP28,LP34,LP33),(LP28,LP34,LP32)]
V1 = [(LP05,LP07,LP03),(LP05,LP07,LP13),(LP13,LP14,LP07),(LP13,LP14,LP17)]
V2 = [(LP08,LP06,LP04),(LP08,LP06,LP15),(LP15,LP16,LP06),(LP15,LP16,LP18)]
V3 = [(LP19,LP20,LP17),(LP19,LP20,LP29),(LP29,LP27,LP20),(LP29,LP27,LP31)]
V4 = [(LP21,LP22,LP18),(LP21,LP22,LP28),(LP28,LP30,LP22),(LP28,LP30,LP32)]
C1 = [(LP09,LP12)]
C2 = [(LP23,LP26)]
T1 = [(LP13,LP19,LP17)]
T2 = [(LP14,LP20,LP17)]
T3 = [(LP15,LP21,LP18)]
T4 = [(LP16,LP22,LP18)]

LCD_0 = H1+H3+V1+V2+V3+V4+T1+T2+T3+T4
LCD_1 = V2+V4+T3+T4
LCD_2 = H1+H2+H3+V2+V3
LCD_3 = H1+H2+H3+V2+V4+T4
LCD_4 = H2+V1+V2+V4+T4
LCD_5 = H1+H2+H3+V1+V4
LCD_6 = H1+H2+H3+V1+V3+V4+T1
LCD_7 = H1+V1+V2+V4+T3+T4
LCD_8 = H1+H2+H3+V1+V2+V3+V4+T1+T4
LCD_9 = H1+H2+H3+V1+V2+V4+T4
LCD_COLON = C1+C2
LCD_BG = LPBG0+LPBG1

# for quick retrieval using target digit as index
LCD_DIGITS = [LCD_0,LCD_1,LCD_2,LCD_3,LCD_4,LCD_5,LCD_6,LCD_7,LCD_8,LCD_9]

# some default LCD digit sizes/scales
LCD_SM = 0.33 # approx. 17 digits over entire width
LCD_MD = 0.63 # approx. 9 digits over entire width
LCD_LG = 1.15 # approx. 5 digits over entire width 

# NOTE:
#   the EPD does not handle too many triangles at a time
#   if it does not display the digits sent, there are too many
#   send over a few segments until I fix it

def lcd_digit(x,y,d,scale=LCD_MD):
    # draw digit over existing image with transparency like other hollow shapes
    if d == ':':
        for rect in LCD_COLON:
            (x0,y0),(x1,y1) = rect
            epd_fill_rect(int(scale*x0+x),int(scale*y0+y),
                          int(scale*x1+x),int(scale*y1+y))
    elif d in [str(s) for s in range(0,10)]:
        for tri in LCD_DIGITS[int(d)]:
            (x0,y0),(x1,y1),(x2,y2) = tri
            epd_fill_triangle(int(scale*x0+x),int(scale*y0+y),
                              int(scale*x1+x),int(scale*y1+y),
                              int(scale*x2+x),int(scale*y2+y))
    else:
        print "'%s' is not a digit or colon. Leaving it blank." % d

def epd_lcd_digits(x,y,digits,scale=LCD_MD):
    if digits=='':
        return
    # for now, the input is expected to be a sequence of digits
    # or a time with colon as the separator, e.g. 12:48

    # fill all background area including spacing with white rectangle
    epd_set_color(WHITE,WHITE)
    epd_fill_rect(x,y,
                  int(x+(len(digits)-1)*(LCD_DIGIT_WIDTH+LCD_SPACING)*scale+LCD_DIGIT_WIDTH*scale),
                  int(y+LCD_DIGIT_HEIGHT*scale))
    epd_set_color(BLACK,WHITE)

    count = 0
    for d in digits:
        lcd_digit(int(x+count*scale*(LCD_DIGIT_WIDTH+LCD_SPACING)), y, d, scale)
        count+=1
        if count % 5 == 0:
            # force an update every 5 digits to avoid a no-display
            # due to too many triangles filling up EPD's buffer
            epd_update()
            sleep(2)
    if count % 5 != 0:
        # so we don't refresh twice if we just did it by the last digit in the loop
        epd_update()


# lightweight (in terms of drawing) and scalable block digits
# in contrast to the nice LCD digits which require drawing many
# triangles for each digit, these simple digits only require
# up to 3 rectangles (6x coordinates) per digit
# 
# see ePaperDisplay/docs/block_digit_font_design.svg for reference
# a 3x5 rectangle in FG colour is drawn and up to 2 areas are
# 'subtracted' with BG colour to make a digit, e.g.
#
# ### ### ### ### ### # # ### ###  #  ###
# # # # #   # #   #   # #   #   #  #  # #  #
# ### ###   # ### ### ### ### ###  #  # #
#   # # #   # # #   #   #   # #    #  # #  #
# ### ###   # ### ###   # ### ###  #  ###

BLOCK_DIGIT_WIDTH = 30
BLOCK_DIGIT_HEIGHT = 50
BLOCK_DIGIT_SPACING = 5 # space between 2 block digits

BP01 = (0,0)
BP02 = (10,0)
BP03 = (20,0)
BP04 = (0,10)
BP05 = (10,10)
BP06 = (20,20)
BP07 = (30,20)
BP08 = (0,30)
BP09 = (10,30)
BP10 = (20,40)
BP11 = (30,40)
BP12 = (10,50)
BP13 = (20,50)
BP14 = (30,50)

BLK_0 = [(BP05,BP10)]
BLK_1 = [(BP01,BP12),(BP03,BP14)]
BLK_2 = [(BP04,BP06),(BP09,BP11)]
BLK_3 = [(BP04,BP06),(BP08,BP10)]
BLK_4 = [(BP02,BP06),(BP08,BP13)]
BLK_5 = [(BP05,BP07),(BP08,BP10)]
BLK_6 = [(BP02,BP07),(BP09,BP10)]
BLK_7 = [(BP04,BP13)]
BLK_8 = [(BP05,BP06),(BP09,BP10)]
BLK_9 = [(BP05,BP06),(BP08,BP10)]
BLK_COLON = BLK_8 # invert FG/BG colour
BLK_BG = (BP01,BP14)

# for quick retrieval using target digit as index
BLK_DIGITS = [BLK_0,BLK_1,BLK_2,BLK_3,BLK_4,BLK_5,BLK_6,BLK_7,BLK_8,BLK_9]

# some default LCD digit sizes/scales
BLOCK_SM = 1.0 # approx. 23 digits over entire width
BLOCK_MD = 2.5 # approx. 9 digits over entire width
BLOCK_LG = 4.65 # approx. 5 digits over entire width

def block_digit(x,y,d,scale=BLOCK_SM):
    (x0,y0),(x1,y1) = BLK_BG

    if d == ':':
        epd_set_color(WHITE,WHITE)
        epd_fill_rect(int(scale*x0+x),int(scale*y0+y),
                      int(scale*x1+x),int(scale*y1+y))
        epd_set_color(BLACK,WHITE)
        d = '8'
    elif d in [str(s) for s in range(0,10)]:
        epd_set_color(BLACK,WHITE)
        epd_fill_rect(int(scale*x0+x),int(scale*y0+y),
                      int(scale*x1+x),int(scale*y1+y))
        epd_set_color(WHITE,WHITE)
    else:
        print "'%s' is not a digit or colon. Leaving it blank." % d
        return

    for rect in BLK_DIGITS[int(d)]:
        (x0,y0),(x1,y1) = rect
        epd_fill_rect(int(scale*x0+x),int(scale*y0+y),
                      int(scale*x1+x),int(scale*y1+y))
    epd_set_color(BLACK,WHITE)


def epd_block_digits(x,y,digits,scale=BLOCK_SM):
    if digits=='':
        return
    # fill all background area including spacing with white rectangle
    epd_set_color(WHITE,WHITE)
    epd_fill_rect(x,y,
                  int(x+(len(digits)-1)*(BLOCK_DIGIT_SPACING+BLOCK_DIGIT_WIDTH)*scale+BLOCK_DIGIT_WIDTH*scale),
                  int(y+BLOCK_DIGIT_HEIGHT*scale))
    count = 0
    for d in digits:
        block_digit(int(x+count*scale*(BLOCK_DIGIT_SPACING+BLOCK_DIGIT_WIDTH)), y, d, scale)
        count+=1
    epd_update()


# ASCII string to Hex string. e.g. "World" => "576F726C64"
def A2H(string):
    hex_str = ""
    for c in string:
        hex_str = hex_str+hex(ord(c))[-2:]
    return hex_str+"00" # append "00" to string as required


# hex string to bytes with parity byte at the end
def H2B(hexStr):
    bytes = []
    parity = 0x00
    hexStr = hexStr.replace(" ",'')
    for i in range(0, len(hexStr), 2):
        byte = int(hexStr[i:i+2],16)
        bytes.append(chr(byte))
        parity = parity ^ byte
    bytes.append(chr(parity))
    return ''.join(bytes)


def send(cmd):
    if soc == None:
        print ">> EPD not connected. Try epd_connect()"
    elif type(soc) == socket._socketobject:
        soc.send(H2B(cmd))
    else:
        soc.write(H2B(cmd))
        if VERBOSE:
            print ">",soc.readline()


def epd_connect(rate=BAUD_RATE):
    global soc, BAUD_RATE
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.settimeout(1)
    for ip in [LAN, AP]:
        try:
            soc.connect((LAN, PORT))
            print "> EPD connected at %s:%s" % (ip, PORT)
            break
        except:
            print ">> EPD not found at %s:%s" % (ip, PORT)
    else:
        if os.path.exists(DEV):
            import serial
            try:
                soc = serial.Serial(
                    port=DEV,
                    baudrate=rate,
                    timeout=1
                )
                print "> EPD connected via serial port"
                if BAUD_RATE != rate:
                    BAUD_RATE = rate
                    print "> Client-side BAUD_RATE is now %d" % rate
                return
            except:
                print ">> Unable to connect to USB serial port", DEV
        else:
            print ">> Serial port unavailable",DEV


def epd_verbose(v):
    global VERBOSE
    if v:
        VERBOSE = True
    else:
        VERBOSE = False


def epd_handshake():
    print "> EPD handshake"
    send(_cmd_handshake)


def epd_disconnect():
    global soc
    soc.close()
    print "> EPD connection closed."


def epd_update():
    send(_cmd_update)


def epd_clear():
    send(_cmd_clear)
    epd_update()


def reset_baud_rate():
    BAUD_RATE = BAUD_RATE_DEFAULT


def epd_set_baud(baud_rate): # 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200
    global BAUD_RATE
    if type(soc) == socket._socketobject:
        print "> Do not change baud rate when using WiFi relay, or the WiFi module and the EPD will have different baud rates and stop understanding each other."
        return
    if baud_rate in BAUD_RATES:
        hex_rate=('0000000'+hex(baud_rate)[2:])[-8:]
        _cmd = FRAME_BEGIN+"000D"+CMD_SET_BAUD+hex_rate+FRAME_END
        send(_cmd)
        print "> Releasing current serial connection..."
        epd_disconnect()
        print "> Waiting for the EPD to re-initiate with new baud rate..."
        sleep(5)
        print "> Reconnecting with baud rate %d ..." % baud_rate
        epd_connect(rate=baud_rate)
    else:
        print "> Invalid baud rate. Pick from",BAUD_RATES


def epd_read_baud():
    print "> EPD baud rate:"
    send(_cmd_read_baud)


def epd_set_memory_nand():
    send(_cmd_use_nand)

def epd_set_memory_sd():
    send(_cmd_use_sd)


def epd_halt():
    print "> EPD halt"
    send(_cmd_stopmode)


def epd_screen_normal():
    _cmd = FRAME_BEGIN+"000A"+CMD_SCREEN_ROTATION+EPD_NORMAL+FRAME_END
    send(_cmd)
    epd_update()

def epd_screen_invert():
    _cmd = FRAME_BEGIN+"000A"+CMD_SCREEN_ROTATION+EPD_INVERSION+FRAME_END
    send(_cmd)
    epd_update()


def epd_import_font():
    send(_cmd_import_font)


def epd_import_pic():
    send(_cmd_import_pic)


def epd_set_color(fg, bg):
    if fg in [BLACK, DARK_GRAY, GRAY, WHITE] and bg in [BLACK, DARK_GRAY, GRAY, WHITE]:
        _cmd = FRAME_BEGIN+"000B"+CMD_SET_COLOR+fg+bg+FRAME_END
        send(_cmd)


def epd_set_en_font(en_size):
    _cmd = FRAME_BEGIN+"000A"+CMD_SET_EN_FONT+en_size+FRAME_END
    send(_cmd)


def epd_set_ch_font(ch_size):
    _cmd = FRAME_BEGIN+"000A"+CMD_SET_CH_FONT+ch_size+FRAME_END
    send(_cmd)


def epd_pixel(x0, y0):
    hex_x0 = ("000"+hex(x0)[2:])[-4:]
    hex_y0 = ("000"+hex(y0)[2:])[-4:]
    _cmd = FRAME_BEGIN+"000D"+CMD_DRAW_PIXEL+hex_x0+hex_y0+FRAME_END
    send(_cmd)


def epd_line(x0, y0, x1, y1):
    hex_x0 = ("000"+hex(x0)[2:])[-4:]
    hex_y0 = ("000"+hex(y0)[2:])[-4:]
    hex_x1 = ("000"+hex(x1)[2:])[-4:]
    hex_y1 = ("000"+hex(y1)[2:])[-4:]
    _cmd = FRAME_BEGIN+"0011"+CMD_DRAW_LINE+hex_x0+hex_y0+hex_x1+hex_y1+FRAME_END
    send(_cmd)


def epd_rect(x0, y0, x1, y1):
    hex_x0 = ("000"+hex(x0)[2:])[-4:]
    hex_y0 = ("000"+hex(y0)[2:])[-4:]
    hex_x1 = ("000"+hex(x1)[2:])[-4:]
    hex_y1 = ("000"+hex(y1)[2:])[-4:]
    _cmd = FRAME_BEGIN+"0011"+CMD_DRAW_RECT+hex_x0+hex_y0+hex_x1+hex_y1+FRAME_END
    send(_cmd)


def epd_fill_rect(x0, y0, x1, y1):
    hex_x0 = ("000"+hex(x0)[2:])[-4:]
    hex_y0 = ("000"+hex(y0)[2:])[-4:]
    hex_x1 = ("000"+hex(x1)[2:])[-4:]
    hex_y1 = ("000"+hex(y1)[2:])[-4:]
    _cmd = FRAME_BEGIN+"0011"+CMD_FILL_RECT+hex_x0+hex_y0+hex_x1+hex_y1+FRAME_END
    send(_cmd)


def epd_circle(x0, y0, r):
    hex_x0 = ("000"+hex(x0)[2:])[-4:]
    hex_y0 = ("000"+hex(y0)[2:])[-4:]
    hex_r = ("000"+hex(r)[2:])[-4:]
    _cmd = FRAME_BEGIN+"000F"+CMD_DRAW_CIRCLE+hex_x0+hex_y0+hex_r+FRAME_END
    send(_cmd)


def epd_fill_circle(x0, y0, r):
    hex_x0 = ("000"+hex(x0)[2:])[-4:]
    hex_y0 = ("000"+hex(y0)[2:])[-4:]
    hex_r = ("000"+hex(r)[2:])[-4:]   
    _cmd = FRAME_BEGIN+"000F"+CMD_FILL_CIRCLE+hex_x0+hex_y0+hex_r+FRAME_END
    send(_cmd)


def epd_triangle(x0, y0, x1, y1, x2, y2):
    hex_x0 = ("000"+hex(x0)[2:])[-4:]
    hex_y0 = ("000"+hex(y0)[2:])[-4:]
    hex_x1 = ("000"+hex(x1)[2:])[-4:]
    hex_y1 = ("000"+hex(y1)[2:])[-4:]
    hex_x2 = ("000"+hex(x2)[2:])[-4:]
    hex_y2 = ("000"+hex(y2)[2:])[-4:]
    _cmd = FRAME_BEGIN+"0015"+CMD_DRAW_TRIANGLE+hex_x0+hex_y0+hex_x1+hex_y1+hex_x2+hex_y2+FRAME_END
    send(_cmd)


def epd_fill_triangle(x0, y0, x1, y1, x2, y2):
    hex_x0 = ("000"+hex(x0)[2:])[-4:]
    hex_y0 = ("000"+hex(y0)[2:])[-4:]
    hex_x1 = ("000"+hex(x1)[2:])[-4:]
    hex_y1 = ("000"+hex(y1)[2:])[-4:]
    hex_x2 = ("000"+hex(x2)[2:])[-4:]
    hex_y2 = ("000"+hex(y2)[2:])[-4:]
    _cmd = FRAME_BEGIN+"0015"+CMD_FILL_TRIANGLE+hex_x0+hex_y0+hex_x1+hex_y1+hex_x2+hex_y2+FRAME_END
    send(_cmd)


def epd_ascii(x0, y0, txt):
    if len(txt) <= MAX_STRING_LEN:
        hex_x0 = ("000"+hex(x0)[2:])[-4:]
        hex_y0 = ("000"+hex(y0)[2:])[-4:]
        hex_txt = A2H(txt)
        hex_size = ("000"+hex(13+len(hex_txt)/2)[2:])[-4:]
        _cmd = FRAME_BEGIN+hex_size+CMD_DRAW_STRING+hex_x0+hex_y0+hex_txt+FRAME_END
        send(_cmd)
    else:
        print "> Too many characters. Max length =",MAX_STRING_LEN


def epd_chinese(x0, y0, gb2312_hex): # "hello world" in Chinese: C4E3 BAC3 CAC0 BDE7
    gb2312_hex = gb2312_hex.replace(" ","")+"00"
    if len(gb2312_hex)/2 <= MAX_STRING_LEN:
        hex_x0 = ("000"+hex(x0)[2:])[-4:]
        hex_y0 = ("000"+hex(y0)[2:])[-4:]
        hex_size = ("000"+hex(13+len(gb2312_hex)/2)[2:])[-4:]
        _cmd = FRAME_BEGIN+hex_size+CMD_DRAW_STRING+hex_x0+hex_y0+gb2312_hex+FRAME_END
        send(_cmd)
    else:
        print "> Too many characters. Max length =",MAX_STRING_LEN


def epd_bitmap(x0, y0, name): # file names must be all capitals and <10 letters including '.'
    hex_x0 = ("000"+hex(x0)[2:])[-4:]
    hex_y0 = ("000"+hex(y0)[2:])[-4:]
    hex_name = A2H(name)
    hex_size = ("000"+hex(13+len(hex_name)/2)[2:])[-4:]
    _cmd = FRAME_BEGIN+hex_size+CMD_DRAW_BITMAP+hex_x0+hex_y0+hex_name+FRAME_END
    send(_cmd)


def get_width(txt,size=32): # size in [32,48,64]
                            # characters in size 32 are manually measured so their
                            # widths are accurate. font size 48 and 64 are assumed
                            # widths based on simple calculation for rough estimates.
    if not size in [32, 48, 64]:
        print "> Error: size must be in [32,48,64]"
        return
    width = 0
    for c in txt:
        if c in "'":
            width += 5
        elif c in "ijl|":
            width += 6
        elif c in "f":
            width += 7
        elif c in " It![].,;:/\\":
            width += 8
        elif c in "r-`(){}":
            width += 9
        elif c in '"':
            width += 10
        elif c in "*":
            width += 11
        elif c in "x^":
            width += 12
        elif c in "Jvz":
            width += 13
        elif c in "cksy":
            width += 14
        elif c in "Labdeghnopqu$#?_1234567890":
            width += 15
        elif c in "T+<>=~":
            width += 16
        elif c in "FPVXZ":
            width += 17
        elif c in "ABEKSY&":
            width += 18
        elif c in "HNUw":
            width += 19
        elif c in "CDR":
            width += 20
        elif c in "GOQ":
            width += 21
        elif c in "m":
            width += 22
        elif c in "M":
            width += 23
        elif c in "%":
            width += 24
        elif c in "@":
            width += 27
        elif c in "W":
            width += 28
        else: # non-ascii or Chinese character
            width += 32
    return int(width * (size/32.0))


def wrap_ascii(x,y,txt,limit=800,size=32): # does not work well with size 48 or 64
    DELIMITER = " "
    DELIMITER_WIDTH = get_width(DELIMITER,size)
    WHITE_WIDTH = get_width(" ",size)
    lines = txt.strip().split("\n")
    y_offset = 0
    for l in lines:
        words = l.strip().split(DELIMITER)
        line = ""
        line_width = 0
        for word in words:
            word_width = get_width(word,size)
            if line_width+DELIMITER_WIDTH+word_width <= limit:
                line += DELIMITER + word
                line_width += DELIMITER_WIDTH + word_width
            else:
                # clear line up to the whole line width
                epd_set_color(WHITE,WHITE)
                epd_fill_rect(x,y+y_offset,x+limit,y+y_offset+size)
                epd_set_color(BLACK,WHITE)
                epd_ascii(x,y+y_offset,line.strip(DELIMITER))
                y_offset += size
                line = word
                line_width = word_width
        if line != "":
            # clear line up to the whole line width
            epd_set_color(WHITE,WHITE)
            epd_fill_rect(x,y+y_offset,x+limit,y+y_offset+size)
            epd_set_color(BLACK,WHITE)
            epd_ascii(x,y+y_offset,line.strip(DELIMITER))
            y_offset += size


def help(): # list all available functions
    print """\
epd_connect()                           # opens a connection to EPD (TCP/IP or USB serial)
epd_handshake()                         # check if EPD is ready via serial connection
epd_disconnect()                        # close serial connection to EPD
epd_verbose(True|False)                 # enable/disable(default) verbose serial communication (SLOW!)
epd_halt()                              # put EPD to sleep. to wake up pin by physical pin only

epd_read_baud()                         # read EPD serial connection baud rate
epd_set_baud(int)                       # set EPD serial baud rate & restart & reconnect

epd_set_memory_nand()                   # use internal memory (default)
epd_set_memory_sd()                     # use SD card

epd_import_font()                       # copy font files form SD card to internal memory
epd_import_pic()                        # copy images from SD card to internal memory

epd_set_color(foreground,background)    # set colours from BLACK|DARK_GRAY|GRAY|WHITE

epd_set_ch_font(GBK32|GBK48|GBK64)      # set Chinese font size
epd_set_en_font(ASCII32|ASCII48|ASCII64)# set ASCII font size

epd_screen_normal()                     # flip EPD screen back to normal
epd_screen_invert()                     # flip EPD screen 180 degrees
epd_clear()                             # clear display
epd_update()                            # update screen with buffered commands

epd_lcd_digits(x,y,"digits string",scale=LCD_SM|LCD_MD|LCD_LG|<num>)
                                        # display digits including colon in LCD-digit font
                                        # scale can be any reasonable number
epd_block_digits(x,y,"digits string",scale=BLOCK_SM|BLOCK_MD|BLOCK_LG|<num>)
                                        # display 3x5 block digits including colon
                                        # scale can be any reasonable number
epd_ascii(x,y,"ascii string")           # display ascii string
epd_chinese(x,y,"hex code of Chinese")  # display Chinese string

wrap_ascii(x,y,txt,limit=800,size=32)   # auto-wraps a paragraph of ascii texts and displays
                                        # from origin x,y with optional width limit and font size

epd_pixel(x,y)                          # draw a pixel
epd_line(x0,y0,x1,y1)                   # draw a line
epd_rect(x0,y0,x1,y1)                   # draw a rectangle
epd_fill_rect(x0,y0,x1,y1)              # draw a filled rectangle
epd_circle(x,y,radius)                  # draw a circle
epd_fill_circle(x,y,radius)             # draw a filled circle
epd_triangle(x0,y0,x1,y1,x2,y2)         # draw a triangle
epd_fill_triangle(x0,y0,x1,y1,x2,y2)    # draw a filled triangle

epd_bitmap(x,y,"image file name")       # display image
"""