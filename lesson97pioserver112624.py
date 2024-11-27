
##############################################################
#                                                            #
# SG90 servo PIO State machine lesson97pioservo112624.py     #
# state machine frequency = 1_000_000 hz = 1 µs/instruction  #   
# servo period = 50hz = 20_000 µs                            #
# servo control pin = Pin(0)                                 #
# X register: servo_pulse_width counter                      #
# Y register: servo period counter                           #
#                                                            #
# ->|                               |<-  period = 20_000 µs  #
#                                                            #
#___|****|__________________________|***|________            #
#                                                            #
# ->|    |<- pulse width = 700->2_500 µs = 0->180 degrees    #
#                                                            #
##############################################################

from machine import Pin
from rp2 import asm_pio, PIO, StateMachine
from time import sleep

@asm_pio(sideset_init = PIO.OUT_LOW)
def servo_pio():
    pull(noblock) .side(0)         # counter for servo pulse width, use X if no new data to pull()
    mov(x,osr)                     # servo pulse width counter in X
    mov(y, isr)                    # servo period counter preloaded in isr -> Y
    label('loop')                  # count down from period counter
    jmp(x_not_y, 'continue')       # check if servo pulse width counter needs starting
    nop() .side(1)                 # start servo pulse
    label('continue')
    jmp(y_dec, 'loop')             # decrement period counter until servo period complete
    
class ServoSM:
    ''' servo state machine specs for lesson 97:
        servo_pulse_width_min (µs) = 700
        servo_pulse_width_max (µs) = 2_500
        servo_signal_pin (servo control gpio pin) = Pin(0)
        servo_period (µs) = 20_000 
    '''
    def __init__(self, sm_id, sm_freq, servo_pulse_width_min_µs, servo_pulse_width_max_µs, servo_signal_pin, servo_period_counter):
        self.servo_pulse_width_min_µs = servo_pulse_width_min_µs
        self.servo_pulse_width_max_µs = servo_pulse_width_max_µs
        self._sm = StateMachine(sm_id, servo_pio, sm_freq, sideset_base = servo_signal_pin)
        self._sm.put(servo_period_counter)    # preload servo period counter into isr
        self._sm.exec("pull()")
        self._sm.exec("mov(isr,osr)")
        self._sm.active(1)
        
    def servo_angle(self, angle):
        '''
            y = m * degrees + b
            P1 = (x1,y1) = (0 deg, servo_pulse_width_min_µs);  P2 = (x2, y2) = (180 deg, servo_pulse_width_max_µs)
        '''
        m = (self.servo_pulse_width_max_µs - self.servo_pulse_width_min_µs) / 180  # m = (2_300-600)/180 = 9.444
        y = m * angle + self.servo_pulse_width_min_µs  # µs needed for degree
        self._sm.put( int( y//2) ) # servo_pio requires 2 instructions (2 µs) to decrement counter by one, so adjust counter by half

servo_signal_pin = Pin(0, Pin.OUT)
servo_period_counter = int(20_000//2 - 3)  # servo_pio requires 2 instructions (2µs) to decrement counter, and 3 instructions to setup
sm0 = ServoSM(0, 1_000_000, 700, 2_500, servo_signal_pin, servo_period_counter)
sm0.servo_angle(90)  # set servo to 90°

# bonus, cycle servo from 0°->180°->0° using state machine class ServoSM
sleep(3)
for i in range(0, 180+1, 10):
    sm0.servo_angle(i)
    sleep(0.3)
for i in reversed(range(0, 180+1, 10)):
    sm0.servo_angle(i)
    sleep(0.3)
    
sm0.servo_angle(90)  # set servo back to 90°
                  
