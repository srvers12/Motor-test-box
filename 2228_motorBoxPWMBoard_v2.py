from machine import Pin, PWM, I2C
from ssd1306 import SSD1306_I2C
import framebuf
import utime

#Constants
MID_PWM_NS = 1500000
MIN_PWM_NS = 1000000
MAX_PWM_NS = 2000000
one_percent_pwm_ns_Step =5000

long_debounce_done = False
debounce_count = 5
long_debounce_count = 100

WIDTH = 128
HEIGHT = 64
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=200000)
# Display device address
print("I2C Address      : "+hex(i2c.scan()[0]).upper())

oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

oled.fill(0)
oled.show()

# *****THIS IS THE KEY TO THE DATA*****
#bdDataList =[[encoder_clk_current-0,
#                 encoder_clk_previous-1,
#                 encoder_DT-2,
#                 encoder_sw-3,
#                 encoder_sw_debounce_state-4,
#                 encoder_sw_count-5,
#                 encoder_sw_count_done_flg-6
#                 encoder_sw_long_count_done_flg-7
#                 percent increment-8,
#                 current_spd_setpt_%-9,
#                 output_spd_%-10
#                 Mode-0(on/off),1(follow setpt),,2(FWD-off-REV-off)-11,
#                 Mode_State(0-off,1-on/fwd,2-off,3-rev)-12
#                 ]]
#                 

bdDataList =[[0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0]]

#Define IO pins
board_led = Pin(25,Pin.OUT)

encoder0_clk = Pin(16,Pin.IN)
encoder0_DT = Pin(15,Pin.IN)
encoder0_sw = Pin(14,Pin.IN,Pin.PULL_UP)

encoder1_clk = Pin(19,Pin.IN)
encoder1_DT = Pin(18,Pin.IN)
encoder1_sw = Pin(17,Pin.IN,Pin.PULL_UP)

encoder2_clk = Pin(22,Pin.IN)
encoder2_DT = Pin(21,Pin.IN)
encoder2_sw = Pin(20,Pin.IN,Pin.PULL_UP)

encoder3_clk = Pin(28,Pin.IN)
encoder3_DT = Pin(27,Pin.IN)
encoder3_sw = Pin(26,Pin.IN,Pin.PULL_UP)

pwm0 = PWM(Pin(2))
pwm1 = PWM(Pin(3))
pwm2 = PWM(Pin(4))
#   set output freq and duty cycle
pwm0.freq(50)    
pwm0.duty_ns(MID_PWM_NS)
pwm1.freq(50)    
pwm1.duty_ns(MID_PWM_NS)
pwm2.freq(50)    
pwm2.duty_ns(MID_PWM_NS)

sw1 = Pin(5,Pin.IN)
sw2 = Pin(6,Pin.IN)

def Decode_switches():
    sw_change_flg = False
    for x in range(4):
 # reset debounce flags       
        if(bdDataList[x][4] == 1):
            bdDataList[x][6] = 0
            bdDataList[x][7] = 0        

        if( bdDataList[x][3] != bdDataList[x][4] ):
            bdDataList[x][5] += 1
            
            if(bdDataList[x][5] >= debounce_count):
# debounce complete set switch state done flg
                bdDataList[x][4] = bdDataList[x][3]
                bdDataList[x][5] = 0
                bdDataList[x][6] = 1
            
        
# update output in set mode               
            if(bdDataList[x][4] == 0 and bdDataList[x][6] == 1 ):
                sw_change_flg = True 
#       Mode 0
                if(bdDataList[x][11] == 0):
                    if(bdDataList[x][12] == 0):
                        bdDataList[x][10] = bdDataList[x][9]
                        bdDataList[x][12] = 1                           
                    else:
                        bdDataList[x][10] = 0 
                        bdDataList[x][12] = 0               
#       Mode 1
                if(bdDataList[x][11] == 1): 
                    bdDataList[x][9] = 0
                    bdDataList[x][10] = 0
                    bdDataList[x][12] = 0
#       Mode 2
                if(bdDataList[x][11] == 2):
                    if(bdDataList[x][12] == 0):
                        bdDataList[x][10] = bdDataList[x][9]
                        bdDataList[x][12] = 1
                    elif(bdDataList[x][12] == 1):
                        bdDataList[x][10] = 0 
                        bdDataList[x][12] = 2                        
                    elif(bdDataList[x][12] == 2):
                        bdDataList[x][10] = -bdDataList[x][9] 
                        bdDataList[x][12] = 3                        
                    elif((bdDataList[x][12] == 3)):
                        bdDataList[x][10] = 0
                        bdDataList[x][12] = 0
                        
# check for long delay count            
        if((bdDataList[x][4] == 0) and (bdDataList[x][7] == 0)  ):
            bdDataList[x][5] += 1

            if( bdDataList[x][5] >= long_debounce_count):
                sw_change_flg = True
                bdDataList[x][7] = 1
                bdDataList[x][9] = 0
                bdDataList[x][10] = 0
                bdDataList[x][11] += 1
                if(bdDataList[x][11] > 2):
                    bdDataList[x][11] = 0
                    bdDataList[x][12] = 0
                    
        if(bdDataList[0][4] == 0 and bdDataList[3][4] == 0):
            sw_change_flg = True
            for i in range(3):
                bdDataList[i][9] = 0
                bdDataList[i][10] = 0
                bdDataList[i][11] = 0 
                bdDataList[i][12] = 0       
    return sw_change_flg
        
def Decode_encoders():
    change_flg = False
    for x in range(3):
        if(bdDataList[x][0] != bdDataList[x][1]):
            change_flg = True              
#           data(DT) value != current clock(clk) value            
            if(bdDataList[x][2] != bdDataList[x][0]):            
                bdDataList[x][9] += bdDataList[x][8]
            else:
#               Encoder is rotating counter clockwise                
                bdDataList[x][9] -= bdDataList[x][8]
#           bound % to -100 to 100     
            if(bdDataList[x][9] >= 100):
                bdDataList[x][9] = 100
            elif(bdDataList[x][9] <= -100):
                bdDataList[x][9] = -100
#           bound % to 0 to 100                
            if((bdDataList[x][11] == 2) and bdDataList[x][9] < 0 ):
                bdDataList[x][9] = 0
        #   previous clk value = current clk value    
        bdDataList[x][1] = bdDataList[x][0]       

    return change_flg

def Display_motor_data():
    oled.fill(0)      
    oled.text("E1 M1Spd % " + str(bdDataList[0][9]), 0,0)
    oled.text("E2 M2Spd % " + str(bdDataList[1][9]) , 0,20)
    oled.text("E3 M3Spd % " + str(bdDataList[2][9]) , 0,40)
# motor 1
# mode 0
    if(bdDataList[0][11] == 0):   
        if((bdDataList[0][12]) == 1):           
            oled.text("Mode0 - ON ", 0,10)
        else:           
            oled.text("Mode0 - OFF ", 0,10)
#Mode 1            
    if(bdDataList[0][11] == 1):   
        if((bdDataList[0][12]) == 1 or (bdDataList[0][12] == 0)):
            bdDataList[0][10] = bdDataList[0][9]
            oled.text("Mode1-Follow ", 0,10)
#mode 2           
    if(bdDataList[0][11] == 2):   
        if(bdDataList[0][12] == 0):           
            oled.text("Mode2 - OFF ", 0,10)
        elif(bdDataList[0][12] == 1 ):             
            oled.text("Mode2 - FWD ", 0,10)
        elif(bdDataList[0][12] == 2 ):            
            oled.text("Mode2 - OFF ", 0,10)
        elif(bdDataList[0][12] == 3 ):             
            oled.text("Mode2 - REV ", 0,10)
# motor 2
# Mode 0
    if(bdDataList[1][11] == 0):   
        if((bdDataList[1][12]) == 1):            
            oled.text("Mode0 - ON ", 0,30)
        else:            
            oled.text("Mode0 - OFF ", 0,30)
# Mode 1            
    if(bdDataList[1][11] == 1):   
        if((bdDataList[1][12]) == 1 or (bdDataList[1][12] == 0)):
            bdDataList[1][10] = bdDataList[1][9]
            oled.text("Mode1-Follow ", 0,30)
#Mode 2            
    if(bdDataList[1][11] == 2):   
        if(bdDataList[1][12] == 0):            
            oled.text("Mode2 - OFF ", 0,30)
        elif(bdDataList[1][12] == 1 ):            
            oled.text("Mode2 - FWD ", 0,30)
        elif(bdDataList[1][12] == 2 ):            
            oled.text("Mode2 - OFF ", 0,30)
        elif(bdDataList[1][12] == 3 ):            
            oled.text("Mode2 - REV ", 0,30)
# motor 3
# Mode 0
    if(bdDataList[2][11] == 0):   
        if((bdDataList[2][12]) == 1):            
            oled.text("Mode0 - ON ", 0,50)
        else:            
            oled.text("Mode0 - OFF ", 0,50)
# Mode 1
    if(bdDataList[2][11] == 1):   
        if((bdDataList[2][12]) == 1 or (bdDataList[2][12] == 0)):
            bdDataList[2][10] = bdDataList[2][9] 
            oled.text("Mode1-Follow ", 0,50)
# Mode 2                       
    if(bdDataList[2][11] == 2):   
        if(bdDataList[2][12] == 0):           
            oled.text("Mode2 - OFF ", 0,50)
        elif(bdDataList[2][12] == 1 ):           
            oled.text("Mode2 - FWD ", 0,50)
        elif(bdDataList[2][12] == 2 ):            
            oled.text("Mode2 - OFF ", 0,50)
        elif(bdDataList[2][12] == 3 ):            
            oled.text("Mode2 - REV ", 0,50)      
    oled.show()
    return
# Setup

#init variables

M2_pwm_percent_output = MID_PWM_NS

# init previous clk value 
bdDataList[0][0] = encoder0_clk.value()
bdDataList[1][0] = encoder1_clk.value()
bdDataList[2][0] = encoder2_clk.value()
bdDataList[3][0] = encoder3_clk.value()
   
for x in range(4):
#   init data table
    bdDataList[x][1] = bdDataList[x][0]
    bdDataList[x][2] = 0
    bdDataList[x][3] = 1
    bdDataList[x][4] = 1 
    bdDataList[x][5] = 0
    bdDataList[x][7] = 0
    bdDataList[x][8] = 5
    bdDataList[x][9] = 0
    #bdDataList[x][10] = 0
    bdDataList[x][11] = 0
    bdDataList[x][12] = 0
    
Display_motor_data()

# main
while True:
#    timer_start = utime.ticks_ms()
# read encoder inputs
    bdDataList[0][0] = encoder0_clk.value() 
    bdDataList[0][2] = encoder0_DT.value()
    bdDataList[0][3] = encoder0_sw.value()
    
    bdDataList[1][0] = encoder1_clk.value() 
    bdDataList[1][2] = encoder1_DT.value()
    bdDataList[1][3] = encoder1_sw.value()
    
    bdDataList[2][0] = encoder2_clk.value()
    bdDataList[2][2] = encoder2_DT.value()
    bdDataList[2][3] = encoder2_sw.value()
    
    
    bdDataList[3][0] = encoder3_clk.value() 
    bdDataList[3][2] = encoder3_DT.value()
    bdDataList[3][3] = encoder3_sw.value()
    
# update encoder / switch / display    
    if(Decode_encoders() or Decode_switches()):
        Display_motor_data()
    pwm0.duty_ns((bdDataList[1][10]*one_percent_pwm_ns_Step) + MID_PWM_NS)
    
    print( bdDataList[1][9],bdDataList[1][10], bdDataList[1][11], bdDataList[1][12] )
    pwm1.duty_ns((bdDataList[1][10]*one_percent_pwm_ns_Step) + MID_PWM_NS) 
    pwm2.duty_ns((bdDataList[2][10]*one_percent_pwm_ns_Step) + MID_PWM_NS)
    
#    print((utime.ticks_ms() - timer_start))
    utime.sleep_ms(10)
