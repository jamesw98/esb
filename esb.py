import argparse
import time
import gc
import Queue
import threading
import RPi.GPIO as io

debug = False
esb = None 
leftGround = 16
rightGround = 18
leftButton = 15
rightButton = 13
leftLight = 12
rightLight = 11
beeper = 7
lightTimeSec = 2
beepTimeSec = 1.5
hitDelay = .02

def button_pressed(channel):
    #io.setup(channel,io.OUT) # no longer accept input on that button
    print('Putton pressed',channel)
    esb.pressed(channel)

class Esb(object):
    def __init__(self):
        self.buttons = [leftButton,rightButton,leftGround,rightGround]
        self.lights = [leftLight,rightLight]
        self.beeper = [beeper]
        self.bounceTime = 200
        self._buttonQ = Queue.Queue()
        self._event = threading.Event()
                    
        io.setwarnings(False)
        io.setmode(io.BOARD)
        
        for (i,l) in enumerate(self.lights):
            io.setup(l,io.OUT)
        
        for (i,beep) in enumerate(self.beeper):
            io.setup(beep,io.OUT)
        
        self.buttonInit(True)
        
    
    def write_debug(self,*msg):
        m = ""
        for i in msg:
            m += str(i)+' '

        print('DEBUG: '+m)
        
        return self
            
    def buttonInit(self,firstTime=False):
        for (i,b) in enumerate(self.buttons):   
            print('Initing',b,'to input')
            io.setup(b,io.IN, pull_up_down=io.PUD_DOWN) # sets each button for input

            
    def pressed(self,channel):
        if not io.input(channel):
            self.write_debug("Button press on channel ",channel)
            self._buttonQ.put(channel)
            self._event.set()
        else:
            self.write_debug( "FALSE button",button," on channel ",channel )
    
    def waitForButton(self,timeout_sec,buttonNumber):
        """
        Wait for a button to be pressed.  Will return
        the button number that was pressed
        """
        start = time.time()
        while True:
            button = io.input(buttonNumber)
            if button == 1:
                return 1
            elif timeout_sec > 0 and (time.time() - start) > timeout_sec:
                return 0
                
    def waitForAnyButton(self):
        """
        Wait for any button to be pressed.  Will return
        all the buttons
        """
        while True:
            left = io.input(leftButton)
            right = io.input(rightButton)
            leftBell = io.input(leftGround)
            rightBell = io.input(rightGround)
            if left or right or leftBell or rightBell:
                print(left, right, leftBell, rightBell)
                return left, right, leftBell, rightBell
    
    def beep(self, durationSec = 1, count = 1, delaySec = .1):
        for i in range(count):
            io.output(beeper,io.LOW)
            time.sleep(beepTimeSec)
            io.output(beeper,io.HIGH)
            if beepTimeSec < durationSec:
                time.sleep(durationSec-beepTimeSec)
                
            if count > 1:
                time.sleep(delaySec)
  
    
    def lightOn(self,channel):
        io.output(channel,io.LOW)
        print('Light on',channel)
    
    def lightOff(self,channel):
        io.output(channel,io.HIGH)
        
    def run(self):
        print('Ready?')
        self.lightOn(leftLight)
        self.lightOn(rightLight)
        self.beep()
        
        self.lightOff(leftLight)
        self.lightOff(rightLight)
        print('Fence!')
        while True:
            gc.disable()
            time.sleep(hitDelay)
            
            doubleTouch = 0
            
            (left, right, leftBell, rightBell) = self.waitForAnyButton() # wait for button
                        
            if left and right:
                doubleTouch = 1
            
            elif left: 
                x = rightButton
                if rightBell:
                    print('Left hit right bell')
                    continue
                elif leftBell:
                    print('Left bell and left touch ?!')
                    continue
                    
            elif right:
                x = leftButton
                if leftBell:
                    print('Right hit left bell')
                    continue
                elif rightBell:
                    print('Right bell and right touch ?!')
                    continue
                
            else:
                print('Only bell ?!')
                continue
        
            if doubleTouch == 0:
                doubleTouch = self.waitForButton(1/25.0,x) # waits for 1/25 seconds
                print('Waited for double, second try is',doubleTouch,'x is',x)
            
            if left and right and leftBell and rightBell:
                print('All hit ?!')
                continue
            
            elif doubleTouch != 0: # lights up both lights
                self.lightOn(leftLight)
                self.lightOn(rightLight)
                print('Double touch')
                self.beep(lightTimeSec)
                
            elif left: # lights up a single light
                self.lightOn(leftLight)
                print('Touch Left')
                self.beep(lightTimeSec)
            elif right: 
                self.lightOn(rightLight)
                print('Touch Right')
                self.beep(lightTimeSec)
            else:
                print('Bell Guard Magic ?!')
            
            self.lightOff(rightLight)
            self.lightOff(leftLight)
            print('Lights off')
            
            gc.enable()
            gc.collect()
            
if __name__ == '__main__':
    debug
    parser = argparse.ArgumentParser(description='Epee Scoring Box by Jimmy Wallace')
    parser.add_argument('-t','--test',action='store_true',help='run the simulator instead of on Pi hardware')
    parser.add_argument('-d','--debug',action='store_true',help='show debug message on console')

    args = parser.parse_args()
    
    if args.debug:
        debug = True
        
    esb = Esb()
    esb.run()