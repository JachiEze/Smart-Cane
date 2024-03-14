import time
import Adafruit_ADS1x15

ADC = Adafruit_ADS1x15.ADS1115()

ADC_CHANNEL = 3

GAIN = 1

MIN_ADC_VALUE = 0
MAX_ADC_VALUE = 32767

try:
    while True:
        adc_value = ADC.read_adc(ADC_CHANNEL, gain=GAIN)
        
        water_level = (adc_value - MIN_ADC_VALUE) / (MAX_ADC_VALUE - MIN_ADC_VALUE) * 100
        
        print("ADC Value: {} | Water Level: {:.2f}%)".format(adc_value, water_level)) 
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\nScript Terminated.") 


