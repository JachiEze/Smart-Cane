import time
import Adafruit_ADS1x15
import pygame

ADC = Adafruit_ADS1x15.ADS1115()

ADC_CHANNEL = 3
GAIN = 1
MIN_ADC_VALUE = 0
MAX_ADC_VALUE = 32767

# Initialize pygame mixer
pygame.mixer.init()

# Load the MP3 file
water_file = "waterdetected.mp3"
pygame.mixer.music.load(water_file)

try:
    while True:
        adc_value = ADC.read_adc(ADC_CHANNEL, gain=GAIN)
        
        water_level = (adc_value - MIN_ADC_VALUE) / (MAX_ADC_VALUE - MIN_ADC_VALUE) * 100
        
        print("ADC Value: {} | Water Level: {:.2f}%".format(adc_value, water_level))
        
        # If water level is 25% or greater, play the MP3 file
        if water_level >= 25:
            pygame.mixer.music.play()
        
        time.sleep(2)
        
except KeyboardInterrupt:
    # Stop playback and cleanup pygame mixer
    pygame.mixer.music.stop()
    pygame.mixer.quit()
